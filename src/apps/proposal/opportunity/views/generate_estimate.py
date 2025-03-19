import urllib.parse
from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from django.db.models import Q, QuerySet
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse

from apps.constants import LOGGER
from apps.mixin import (
    CustomDataTableMixin,
    CustomViewMixin,
    ProposalViewMixin,
    TemplateViewMixin,
)

from ..models import AssignedProduct, TaskMapping
from ..tasks import format_number


class TaskProductDataView(CustomDataTableMixin):

    def get_queryset(self):
        document_number = self.kwargs.get("document_number")
        qs = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(
            # Q(assign_to__isnull=False, task__description__icontains="labor") | 
            Q(linked_task__isnull=False, task__description__icontains="labor") |
            Q(task__description__icontains="Freight")
        )
        # Q(linked_task__isnull=False, task__description__icontains="labor") |
        return qs.exclude(code__icontains="FRT")

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(task__internal_id__icontains=self.search)
                | Q(task__name__icontains=self.search)
                | Q(task__description__icontains=self.search)
                | Q(task_description__icontains=self.search)
            )
        return qs

    def _get_code(self, obj):
        """Get code details."""
        task_name = obj.code if obj.task is None else obj.task.name

        # Construct the URL dynamically using reverse
        url = reverse("proposal_app:opportunity:update-estimation-products-ajax", args=[obj.id])

        # Now format the HTML with proper values
        code = f"""
        <a hx-get="{url}"
            data-url="{url}"
            class="htmx-trigger-btn-task-prod"
            hx-target="#task-content"
            hx-trigger="click"
            data-toggle="modal"
            data-target="#showProduct"
            data-backdrop="false">
            <ins>{task_name}</ins>
        </a>
        """
        return code

    def _get_description(self, obj):
        """Generate the HTML for the description with a clickable link."""
        et = obj  # Or whatever object has the `et` property

        if et.task is None:
            task_description = f"{et.code} : {et.description}"
        else:
            task_description = f"{et.task.name} : {et.task.description}"

        # Construct the URL dynamically using reverse
        url = reverse("proposal_app:opportunity:update-estimation-products-ajax", args=[et.id])

        # Now format the HTML with the proper values
        description = f"""
            <a hx-get="{url}"
            data-url="{url}"
            class="htmx-trigger-btn-task-prod"
            hx-target="#task-content"
            hx-trigger="click"
            data-toggle="modal"
            data-target="#showProduct"
            data-backdrop="false">
                <ins>{task_description}</ins>
            </a>
        """
        return description

    def _labor_gp_percent(self, obj):
        """Generate the HTML for the labor gp percent."""
        et = obj

        labor_gp_percent = f"""
            <input type="text" class="form-control btn-outline-warning labor_gp_percent" value="{et.labor_gp_percent}">
        """
        return labor_gp_percent

    def _labor_gp_percent_data(self, obj):
        return obj.labor_gp_percent if obj.labor_gp_percent else 0

    def _mat_gp_percent(self, obj):
        """Generate the HTML for the mat gp percent."""
        et = obj
        mat_gp_percent = f"""
            <input type="text" class="form-control btn-outline-warning mat_gp_percent" value="{ et.mat_gp_percent }">"""
        return mat_gp_percent

    def _mat_gp_percent_data(self, obj):
        return obj.mat_gp_percent if obj.mat_gp_percent else 0
    
    def frt_total(self, obj):
        if not obj or not hasattr(obj, "opportunity") or not obj.opportunity:
            return 0

        task_mappings = TaskMapping.objects.filter(opportunity__document_number=obj.opportunity.document_number)
        
        if task_mappings.exists():
            filtered_task_mappings = task_mappings.filter(task__description__icontains="Freight")
            task_mapping_ids = task_mappings.values_list("id", flat=True)
        else:
            return 0

        try:
            assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids).order_by("sequence")
        except Exception as e:
            LOGGER.error(f"Exception : {e}")
            assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        total_price = 0  
        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)
            total_price += sum(
                (   
                    product.vendor_quoted_cost * product.quantity
                    if product.vendor_quoted_cost
                    else product.standard_cost * product.quantity
                )
                for product in task_assigned_products
            )
        
        return total_price


    def prepare_results(self, qs):
        """
        This method formats the queryset into the structure that DataTables expects.
        Each row of data is a list of values corresponding to the columns in the table.
        """
        data = []
        items_list = []

        item = False
        for item in qs:
            items_list.append(item)
            
            data.append(
                {
                    "code": self._get_code(item),
                    "description": self._get_description(item),
                    "labor_cost": format_number(item.labor_cost),
                    "labor_gp_percent": self._labor_gp_percent(item),
                    "labor_gp": format_number(item.labor_gp),
                    "labor_sell": format_number(item.labor_sell),
                    "mat_cost": format_number(item.mat_cost),
                    "mat_gp_percent": self._mat_gp_percent(item),
                    "mat_gp": format_number(item.mat_gp),
                    "mat_plus_mu": format_number(item.mat_plus_mu),
                    "sales_tax": format_number(item.sales_tax),
                    "mat_sell": format_number(item.mat_sell),
                    "mat_tax_labor": format_number(item.mat_tax_labor),
                    "comb_gp": item.comb_gp,
                    "labor_gp_percent_data": self._labor_gp_percent_data(item),  # type : ignore
                    "mat_gp_percent_data": self._mat_gp_percent_data(item),  # type : ignore
                }
            )
        
        last_item = items_list[-1] if items_list else None
        data.append({
            "code": "FRT",
            "description": "FRT: Freight",
            "labor_cost": "",
            "labor_gp_percent": "",
            "labor_gp": "",
            "labor_sell": "",
            "mat_cost": "",
            "mat_gp_percent": "",
            "mat_gp": "",
            "mat_plus_mu": "",
            "sales_tax": "",
            "mat_sell": "",
            "mat_tax_labor": "",
            "comb_gp": "",
            "labor_gp_percent_data": self._labor_gp_percent_data(item) if item else 0,  # type : ignore
            "mat_gp_percent_data": self._mat_gp_percent_data(item) if item else 0,  # type : ignore
            "frt_total": self.frt_total(last_item),
            # "is_freight": "Freight" in (item.task.description if item.task else ""),            
        })
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class GenerateEstimateTable(ProposalViewMixin):
    """
    View class for rendering the estimate generation.
    """

    render_template_name = "proposal/opportunity/stage/generate_estimation/generate_estimate_table.html"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Populate context with necessary data for rendering the estimate table.

        :param kwargs: Additional context variables.
        :return: Updated context dictionary.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs["document_number"]

        # Fetch task mappings excluding and including labor descriptions
        context["estimation_table"] = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(
            task__description__icontains="labor"
        )

        context["estimation_table_labor"] = TaskMapping.objects.filter(
            opportunity__document_number=document_number
        ).filter(task__description__icontains="labor", assign_to__isnull=True)

        # Calculate totals and add to context
        context["total"] = GenerateEstimate._get_total(document_number)
        context["document_number"] = document_number
        return context


class UpdateEstimationProduct(TemplateViewMixin):
    """
    View for updating product information in the estimation table.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/estimation_product_update.html"

    def get_tasks_products_data(self, task_id: int) -> QuerySet:
        """
        Retrieve assigned products for a specific task.

        :param task_id: The ID of the task to retrieve products for.
        :return: QuerySet of assigned products.
        """
        return AssignedProduct.objects.filter(task_mapping__id=task_id)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Populate context with task mapping and associated products.

        :param kwargs: Additional context variables.
        :return: Updated context dictionary.
        """
        context = super().get_context_data(**kwargs)
        task_id = self.kwargs["task_id"]

        # Use get_object_or_404 for better error handling
        task_mapping_obj = get_object_or_404(TaskMapping, id=task_id)

        context["task_mapping"] = task_mapping_obj
        context["prods"] = self.get_tasks_products_data(task_id)
        return context


class UpdateEstimationLabor(TemplateViewMixin):
    """
    View for updating labor information in the estimation table.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/estimation_labor_update.html"

    def get_tasks_labor_data(self, task_id: int) -> QuerySet:
        """
        Retrieve assigned labor products for a specific task.

        :param task_id: The ID of the task to retrieve labor data for.
        :return: QuerySet of assigned labor products.
        """
        return AssignedProduct.objects.filter(task_mapping__id=task_id)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Populate context with associated labor data for a specific task.

        :param kwargs: Additional context variables.
        :return: Updated context dictionary.
        """
        context = super().get_context_data(**kwargs)
        task_id = self.kwargs["task_id"]

        # Use get_object_or_404 for better error handling
        task_mapping_obj = get_object_or_404(TaskMapping, id=task_id)

        context["task_mapping"] = task_mapping_obj
        context["labors"] = self.get_tasks_labor_data(task_id)
        return context


class UpdateEstimationTable(CustomViewMixin):
    """
    View for updating various fields in the estimation table.
    """

    def __post(self, data: dict) -> dict:
        """
        Update task mapping based on provided data.

        :param data: Parsed request data containing update information.
        """
        document_number = data.get("document_number", [None])[0]
        print(f"document_number {type(document_number)}: {document_number}")
        update_fields = {
            "labor_gp_percent": data.get("labor_gp_percent", [None])[0],
            "mat_gp_percent": data.get("mat_gp_percent", [None])[0],
            "s_and_h": data.get("s_and_h", [None])[0],
        }

        task_mapping_objs = TaskMapping.objects.filter(opportunity__document_number=document_number)
        update_data = {key: value for key, value in update_fields.items() if value is not None}

        if update_data:
            task_mapping_objs.update(**update_data)
            _text = ", ".join(update_data.keys()).replace("_", " ").replace("percent", "%").title()
            self._message = f"{_text} Updated Successfully"
            self._code = 200
        else:
            self._message = "No valid fields provided to update"
            self._code = 400

        return self.generate_response()

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to update estimation table data.

        :param request: The HTTP request object.
        """
        try:
            # Parse the incoming request body
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            return self.__post(data)

        except Exception as e:
            LOGGER.error(f"Error occurred in [UpdateEstimationTable]: {str(e)}")
            self._code = 400
            return self.generate_response()


class GenerateEstimate:

    @staticmethod
    def _get_task_products(document_number: str) -> QuerySet:
        """
        Retrieve task mappings for products associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A queryset of task mappings excluding those with 'labor' in the description.
        """
        qs = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(
            task__description__icontains="labor"
        )

        return qs

    @staticmethod
    def _get_task_labor(document_number: str) -> QuerySet:
        """
        Retrieve task mappings for labor associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A queryset of task mappings that include 'labor' in the description.
        """
        qs = TaskMapping.objects.filter(opportunity__document_number=document_number).filter(
            task__description__icontains="labor", assign_to__isnull=True
        )
        return qs

    @staticmethod
    def _get_total(document_number: str) -> dict:
        """
        Calculate the total costs associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A dictionary with total labor and material costs, and total cost.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(Q(code__icontains="FRT") | Q(task__description__icontains="freight"))
        
        totals = {
            "total_labor_cost": Decimal("0.00"),
            "total_labor_gp_percent": Decimal("0.00"),
            "total_labor_gp": Decimal("0.00"),
            "total_labor_sell": Decimal("0.00"),
            "total_mat_cost": Decimal("0.00"),
            "total_mat_gp_percent": Decimal("0.00"),
            "total_mat_gp": Decimal("0.00"),
            "total_mat_mu": Decimal("0.00"),
            "total_sales_tax": Decimal("0.00"),
            "total_s_and_h": Decimal("0.00"),
            "total_mat_sell": Decimal("0.00"),
            "total_mat_tax_labor": Decimal("0.00"),
            "total_comb_gp": Decimal("0.00"),
        }
        total_cost = Decimal("0.00")
        for task in task_mapping_qs:
            totals["total_labor_cost"] += round(Decimal(task.labor_cost or "0.0"), 2)
            try:
                labor_gp_percent = Decimal(task.labor_gp_percent or "0.0")
            except (ValueError, InvalidOperation):
                labor_gp_percent = Decimal("0.0")
            totals["total_labor_gp_percent"] = round(labor_gp_percent, 2)
            totals["total_labor_gp"] += round(Decimal(task.labor_gp or "0.0"), 2)
            totals["total_labor_sell"] += round(Decimal(task.labor_sell or "0.0"), 2)
            totals["total_mat_cost"] += round(Decimal(task.mat_cost or "0.0"), 2)
            totals["total_mat_gp_percent"] = round(Decimal(task.mat_gp_percent if task.mat_gp_percent else "0.0"), 2)
            totals["total_mat_gp"] += round(Decimal(task.mat_gp or "0.0"), 2)
            totals["total_mat_mu"] += round(Decimal(task.mat_plus_mu or "0.0"), 2)
            totals["total_sales_tax"] += round(Decimal(task.sales_tax or "0.0"), 2)
            totals["total_s_and_h"] = round(Decimal(task.s_and_h or "0.0"), 2)
            totals["total_mat_sell"] += round(Decimal(task.mat_sell or "0.0"), 2)
            totals["total_mat_tax_labor"] += round(Decimal(task.mat_tax_labor or "0.0"), 2)
            totals["total_comb_gp"] += round(Decimal(task.comb_gp or "0.0"), 2)
            total_cost += Decimal(task.labor_cost or "0.0") + Decimal(task.mat_cost or "0.0")
            
        totals["total_cost"] = totals["total_labor_cost"] + totals["total_mat_cost"]
        totals["total_sale"] = totals["total_labor_sell"] + totals["total_mat_sell"]
        totals["total_gp"] = totals["total_mat_gp"] + totals["total_labor_gp"]
        totals["total_gp_per"] = totals["total_sale"] - total_cost  

        if totals["total_sale"] != 0:
            totals["total_gp_percent"] = (totals["total_gp"] / totals["total_sale"]) * 100

        else:
            totals["total_gp_percent"] = Decimal("0.00")

        for key, value in totals.items():
            totals[key] = f"{value:,.2f}"

        return totals


# KPI
class TotalCostBreakdown(TemplateViewMixin):
    """
    View to display the total cost breakdown for a given opportunity.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/total_cost_breakdown.html"

    def get_total(self, document_number: str) -> dict:
        """
        Calculate the total costs associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A dictionary with total labor and material costs, and total cost.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(Q(code__icontains="FRT") | Q(task__description__icontains="freight"))
        totals = {
            "total_labor_cost": Decimal("0.00"),
            "total_mat_cost": Decimal("0.00"),
        }

        for task in task_mapping_qs:
            totals["total_labor_cost"] += Decimal(task.labor_cost or "0.0")
            totals["total_mat_cost"] += Decimal(task.mat_cost or "0.0")

        totals["total_cost"] = totals["total_labor_cost"] + totals["total_mat_cost"]

        return totals

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Get the context data for rendering the template.

        :param kwargs: Additional keyword arguments.
        :return: Updated context dictionary with total costs.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        context["total"] = self.get_total(document_number)
        return context


class TotalSaleBreakdown(TemplateViewMixin):
    """
    View to display the total sales breakdown for a given opportunity.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/total_sale_breakdown.html"

    def get_total(self, document_number: str) -> dict:
        """
        Calculate the total sales associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A dictionary with total labor sales, material sales, and overall total sales.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(Q(code__icontains="FRT") | Q(task__description__icontains="freight"))
        totals = {
            "total_labor_sale": Decimal("0.00"),
            "total_mat_sale": Decimal("0.00"),
        }

        for task in task_mapping_qs:
            totals["total_labor_sale"] += Decimal(task.labor_sell or "0.0")
            totals["total_mat_sale"] += Decimal(task.mat_sell or "0.0")

        totals["total_sale"] = totals["total_labor_sale"] + totals["total_mat_sale"]
        return totals

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Get the context data for rendering the template.

        :param kwargs: Additional keyword arguments.
        :return: Updated context dictionary with total sales.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        context["total"] = self.get_total(document_number)
        return context


class TotalGPBreakdown(TemplateViewMixin):
    """
    View to display the total Gross Profit (GP) breakdown for a given opportunity.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/total_gp_breakdown.html"

    def get_total(self, document_number: str) -> dict:
        """
        Calculate the total GP associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A dictionary with total labor GP, material GP, and overall total GP.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(Q(code__icontains="FRT") | Q(task__description__icontains="freight"))
        print('task_mapping_qs: ||||TotalGPBreakdown|||||||||| ', task_mapping_qs)

        totals = {
            "total_sale": Decimal("0.00"),
            "total_cost": Decimal("0.00"),
            "total_mat_gp": Decimal("0.00"),
            "total_labor_gp": Decimal("0.00"),
        }

        for task in task_mapping_qs:
            totals["total_mat_gp"] += Decimal(task.mat_gp or "0.0")
            totals["total_labor_gp"] += Decimal(task.labor_gp or "0.0")

        totals["total_gp"] = totals["total_mat_gp"] + totals["total_labor_gp"]

        return totals

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Get the context data for rendering the template.

        :param kwargs: Additional keyword arguments.
        :return: Updated context dictionary with total GP.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        context["total"] = self.get_total(document_number)
        return context


class TotalGPPerBreakdown(TemplateViewMixin):
    """
    View to display the total Gross Profit Percentage (GP%) breakdown for a given opportunity.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/total_gp_per_breakdown.html"

    def get_total(self, document_number: str) -> dict:
        """
        Calculate the total GP% associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A dictionary with total labor GP%, material GP%, combined GP%, and overall GP%.
        :raises ZeroDivisionError: if the value not divided by the number.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(Q(code__icontains="FRT") | Q(task__description__icontains="freight"))
        print('task_mapping_qs:-------------------- ', task_mapping_qs)

        total_cost = 0
        totals = {
            "total_gp": Decimal("0.00"),
            "total_sell": Decimal("0.00"),
            "total_mat_gp": Decimal("0.00"),
            "total_labor_gp": Decimal("0.00"),
        }

        for task in task_mapping_qs:
            totals["total_sell"] += Decimal(task.labor_sell or "0.0") + Decimal(task.mat_sell or "0.0")
            total_cost += Decimal(task.labor_cost or "0.0") + Decimal(task.mat_cost or "0.0")
            totals["total_mat_gp"] += Decimal(task.mat_gp or "0.0")
            totals["total_labor_gp"] += Decimal(task.labor_gp or "0.0")

        totals["total_gp"] = totals["total_mat_gp"] + totals["total_labor_gp"]
        totals["total_gp_per"] = totals["total_sell"] - total_cost
        
        try:
            if totals["total_sell"] == Decimal("0.00"):
                totals["total_gp_percent"] = Decimal("0.00")
            else:
                totals["total_gp_percent"] = (totals["total_gp"] / totals["total_sell"]) * 100

        except (ZeroDivisionError, InvalidOperation):
            totals["total_gp_percent"] = Decimal("0.00")

        return totals

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Get the context data for rendering the template.

        :param kwargs: Additional keyword arguments.
        :return: Updated context dictionary with total GP%.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        context["total"] = self.get_total(document_number)
        return context