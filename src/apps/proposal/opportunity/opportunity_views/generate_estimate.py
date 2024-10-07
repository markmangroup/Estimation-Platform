import urllib.parse
from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from apps.constants import ERROR_RESPONSE
from apps.rental.mixin import LoginRequiredMixin, ProposalViewMixin, ViewMixin

from ..models import AssignedProduct, TaskMapping


class GenerateEstimateTable(ProposalViewMixin):
    """
    View class for rendering the estimate generation.
    """

    render_template_name = "proposal/opportunity/stage/generate_estimation/generate_estimate_table.html"

    def get_total(self, document_number):
        """
        Calculate totals for various cost categories based on task mappings.

        :param document_number: The document number to filter opportunities.
        :return: Dictionary containing total costs and profits.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)

        # Initialize totals with Decimal objects for precision
        totals = {
            key: Decimal("0.00")
            for key in [
                "total_labor_cost",
                "total_labor_gp_percent",
                "total_labor_gp",
                "total_labor_sell",
                "total_mat_cost",
                "total_mat_gp_percent",
                "total_mat_gp",
                "total_mat_mu",
                "total_sales_tax",
                "total_s_and_h",
                "total_mat_sell",
                "total_mat_tax_labor",
                "total_comb_gp",
            ]
        }

        # Aggregate totals using Django's annotate for performance
        for task in task_mapping_qs:
            totals["total_labor_cost"] += Decimal(task.labor_cost or "0.0")
            totals["total_labor_gp_percent"] += Decimal(task.labor_gp_percent or "0.0")
            totals["total_labor_gp"] += Decimal(task.labor_gp or "0.0")
            totals["total_labor_sell"] += Decimal(task.labor_sell or "0.0")
            totals["total_mat_cost"] += Decimal(task.mat_cost or "0.0")
            totals["total_mat_gp_percent"] += Decimal(task.mat_gp_percent or "0.0")
            totals["total_mat_gp"] += Decimal(task.mat_gp or "0.0")
            totals["total_mat_mu"] += Decimal(task.mat_plus_mu or "0.0")
            totals["total_sales_tax"] += Decimal(task.sales_tax or "0.0")
            totals["total_s_and_h"] += Decimal(task.s_and_h or "0.0")
            totals["total_mat_sell"] += Decimal(task.mat_sell or "0.0")
            totals["total_mat_tax_labor"] += Decimal(task.mat_tax_labor or "0.0")
            totals["total_comb_gp"] += Decimal(task.comb_gp or "0.0")

        return totals

    def get_context_data(self, **kwargs):
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
        ).filter(task__description__icontains="labor")

        # Calculate totals and add to context
        context["total"] = self.get_total(document_number)
        return context


class UpdateEstimationProduct(LoginRequiredMixin, TemplateView):
    """
    View for updating product information in the estimation table.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/estimation_product_update.html"

    def get_tasks_products_data(self, task_id):
        """
        Retrieve assigned products for a specific task.

        :param task_id: The ID of the task to retrieve products for.
        :return: QuerySet of assigned products.
        """
        return AssignedProduct.objects.filter(task_mapping__id=task_id)

    def get_context_data(self, **kwargs):
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


class UpdateEstimationLabor(LoginRequiredMixin, TemplateView):
    """
    View for updating labor information in the estimation table.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/estimation_labor_update.html"

    def get_tasks_labor_data(self, task_id):
        """
        Retrieve assigned labor products for a specific task.

        :param task_id: The ID of the task to retrieve labor data for.
        :return: QuerySet of assigned labor products.
        """
        return AssignedProduct.objects.filter(task_mapping__id=task_id)

    def get_context_data(self, **kwargs):
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


class UpdateEstimationTable(ViewMixin):
    """
    View for updating various fields in the estimation table.
    """

    def _update_data(self, data):
        """
        Update task mapping based on provided data.

        :param data: Parsed request data containing update information.
        :return: Response dictionary with status and message.
        """
        task_mapping_id = data.get("task_mapping_id", [None])[0]
        task_mapping_obj = get_object_or_404(TaskMapping, id=task_mapping_id)

        if not data:
            return {"status": "error", "message": "No data provided"}

        updates = {
            "labor_gp_percent": "Labor GP % Updated successfully",
            "mat_gp_percent": "MAT GP % Updated successfully",
            "s_and_h": "S & H Updated successfully",
        }

        for key, success_message in updates.items():
            if key in data and data[key]:
                setattr(task_mapping_obj, key, float(data[key][0]))
                task_mapping_obj.save()
                return {"status": "success", "message": success_message}

        return {"status": "error", "message": "No valid fields provided for update"}

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to update estimation table data.

        :param request: The HTTP request object.
        :return: JsonResponse with the result of the update operation.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            response = self._update_data(data)
            return JsonResponse(response)
        except Exception as e:
            print("Error: [UpdateEstimationTable]", e)
            return JsonResponse(ERROR_RESPONSE, status=400)


class GenerateEstimate:

    @staticmethod
    def _get_task_products(document_number):
        qs = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(
            task__description__icontains="labor"
        )

        return qs

    @staticmethod
    def _get_task_labor(document_number):
        qs = TaskMapping.objects.filter(opportunity__document_number=document_number).filter(
            task__description__icontains="labor"
        )
        return qs

    @staticmethod
    def _get_total(document_number):
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)
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

        for task in task_mapping_qs:
            totals["total_labor_cost"] += round(Decimal(task.labor_cost or "0.0"), 2)
            totals["total_labor_gp_percent"] += round(Decimal(task.labor_gp_percent or "0.0"), 2)
            totals["total_labor_gp"] += round(Decimal(task.labor_gp or "0.0"), 2)
            totals["total_labor_sell"] += round(Decimal(task.labor_sell or "0.0"), 2)
            totals["total_mat_cost"] += round(Decimal(task.mat_cost or "0.0"), 2)
            totals["total_mat_gp_percent"] += round(Decimal(task.mat_gp_percent or "0.0"), 2)
            totals["total_mat_gp"] += round(Decimal(task.mat_gp or "0.0"), 2)
            totals["total_mat_mu"] += round(Decimal(task.mat_plus_mu or "0.0"), 2)
            totals["total_sales_tax"] += round(Decimal(task.sales_tax or "0.0"), 2)
            totals["total_s_and_h"] += round(Decimal(task.s_and_h or "0.0"), 2)
            totals["total_mat_sell"] += round(Decimal(task.mat_sell or "0.0"), 2)
            totals["total_mat_tax_labor"] += round(Decimal(task.mat_tax_labor or "0.0"), 2)
            totals["total_comb_gp"] += round(Decimal(task.comb_gp or "0.0"), 2)

        totals["total_cost"] = totals["total_labor_cost"] + totals["total_mat_cost"]
        totals["total_sale"] = totals["total_labor_sell"] + totals["total_mat_sell"]
        totals["total_gp"] = totals["total_labor_gp"] + totals["total_mat_gp"]
        totals["total_gp_percent"] = (
            totals["total_labor_gp_percent"] + totals["total_mat_gp_percent"] + totals["total_comb_gp"]
        )

        return totals


# KPI
class TotalCostBreakdown(LoginRequiredMixin, TemplateView):
    """
    View to display the total cost breakdown for a given opportunity.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/total_cost_breakdown.html"

    def get_total(self, document_number):
        """
        Calculate the total costs associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A dictionary with total labor and material costs, and total cost.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)
        totals = {
            "total_labor_cost": Decimal("0.00"),
            "total_mat_cost": Decimal("0.00"),
        }

        for task in task_mapping_qs:
            totals["total_labor_cost"] += Decimal(task.labor_cost or "0.0")
            totals["total_mat_cost"] += Decimal(task.mat_cost or "0.0")

        totals["total_cost"] = totals["total_labor_cost"] + totals["total_mat_cost"]

        return totals

    def get_context_data(self, **kwargs):
        """
        Get the context data for rendering the template.

        :param kwargs: Additional keyword arguments.
        :return: Updated context dictionary with total costs.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        context["total"] = self.get_total(document_number)
        return context


class TotalSaleBreakdown(LoginRequiredMixin, TemplateView):
    """
    View to display the total sales breakdown for a given opportunity.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/total_sale_breakdown.html"

    def get_total(self, document_number):
        """
        Calculate the total sales associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A dictionary with total labor sales, material sales, and overall total sales.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)
        totals = {
            "total_labor_sale": Decimal("0.00"),
            "total_mat_sale": Decimal("0.00"),
        }

        for task in task_mapping_qs:
            totals["total_labor_sale"] += Decimal(task.labor_sell or "0.0")
            totals["total_mat_sale"] += Decimal(task.mat_sell or "0.0")

        totals["total_sale"] = totals["total_labor_sale"] + totals["total_mat_sale"]
        return totals

    def get_context_data(self, **kwargs):
        """
        Get the context data for rendering the template.

        :param kwargs: Additional keyword arguments.
        :return: Updated context dictionary with total sales.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        context["total"] = self.get_total(document_number)
        return context


class TotalGPBreakdown(LoginRequiredMixin, TemplateView):
    """
    View to display the total Gross Profit (GP) breakdown for a given opportunity.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/total_gp_breakdown.html"

    def get_total(self, document_number):
        """
        Calculate the total GP associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A dictionary with total labor GP, material GP, and overall total GP.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)
        totals = {
            "total_labor_gp": Decimal("0.00"),
            "total_mat_gp": Decimal("0.00"),
        }

        for task in task_mapping_qs:
            totals["total_labor_gp"] += Decimal(task.labor_gp or "0.0")
            totals["total_mat_gp"] += Decimal(task.mat_gp or "0.0")

        totals["total_gp"] = totals["total_labor_gp"] + totals["total_mat_gp"]
        return totals

    def get_context_data(self, **kwargs):
        """
        Get the context data for rendering the template.

        :param kwargs: Additional keyword arguments.
        :return: Updated context dictionary with total GP.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        context["total"] = self.get_total(document_number)
        return context


class TotalGPPerBreakdown(TemplateView):
    """
    View to display the total Gross Profit Percentage (GP%) breakdown for a given opportunity.
    """

    template_name = "proposal/opportunity/stage/generate_estimation/total_gp_per_breakdown.html"

    def get_total(self, document_number):
        """
        Calculate the total GP% associated with the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A dictionary with total labor GP%, material GP%, combined GP%, and overall GP%.
        """
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)
        totals = {
            "total_labor_gp_percent": Decimal("0.00"),
            "total_mat_gp_percent": Decimal("0.00"),
            "total_comb_gp": Decimal("0.00"),
        }

        for task in task_mapping_qs:
            totals["total_labor_gp_percent"] += Decimal(task.labor_gp_percent or "0.0")
            totals["total_mat_gp_percent"] += Decimal(task.mat_gp_percent or "0.0")
            totals["total_comb_gp"] += Decimal(task.comb_gp or "0.0")

        totals["total_gp_percent"] = (
            totals["total_labor_gp_percent"] + totals["total_mat_gp_percent"] + totals["total_comb_gp"]
        )
        return totals

    def get_context_data(self, **kwargs):
        """
        Get the context data for rendering the template.

        :param kwargs: Additional keyword arguments.
        :return: Updated context dictionary with total GP%.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        context["total"] = self.get_total(document_number)
        return context
