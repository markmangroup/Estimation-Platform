import csv
import datetime
import json
import urllib.parse
from collections import defaultdict
from decimal import Decimal
from io import StringIO

import pandas as pd
from django.contrib import messages
from django.db.models import Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.generic import CreateView, FormView, TemplateView, View
from django_datatables_too.mixins import DataTableMixin

from apps.proposal.customer.models import Customer
from apps.proposal.labour_cost.models import LabourCost
from apps.proposal.product.models import Product
from apps.proposal.task.models import Task
from apps.proposal.vendor.models import Vendor
from apps.rental.mixin import ProposalDetailViewMixin, ProposalViewMixin

from .forms import AddTaskForm, ImportOpportunityCSVForm, UploadDocumentForm
from .models import (
    AssignedProduct,
    Document,
    GlueAndAdditionalMaterial,
    Invoice,
    MaterialList,
    Opportunity,
    PreliminaryMaterialList,
    ProposalCreation,
    SelectTaskCode,
    TaskMapping,
)
from .tasks import import_opportunity_from_xlsx


class SearchView(View):

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle GET requests to search for opportunities by document number.

        Retrieves the 'query' parameter from the request, filters `Opportunity`
        for records where `document_number` contains the query string, and returns
        the results in JSON format.

        :request (HttpRequest): The HTTP request object containing query parameters.

        Returns:
        - JsonResponse: JSON response with a list of matching `document_number` values.
        """
        query = request.GET.get("query", "")
        results = []
        # Check length of query
        if len(query) > 3 and query:
            # Set limit with results
            results = Opportunity.objects.filter(document_number__icontains=query).values("document_number")[:5]
        return JsonResponse({"results": list(results)})


class OpportunityList(ProposalViewMixin):
    """
    View to display a list of Opportunities.
    Renders the template for the Opportunity list page.
    """

    render_template_name = "proposal/opportunity/opportunity_list.html"


class OpportunityDocumentView(TemplateView):
    """
    Opportunity document view
    """

    template_name = "proposal/opportunity/opportunity_document.html"

    def _get_opportunity_document(self, document_number):
        qs = Document.objects.filter(opportunity__document_number=document_number)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs["document_number"]
        context["document_number"] = document_number
        context["opportunity_document"] = self._get_opportunity_document(document_number)
        return context


class OpportunityListAjaxView(DataTableMixin, View):
    """
    DataTable view for Opportunities.
    Provides JSON data for the DataTable widget with search and filtering capabilities.
    """

    model = Opportunity
    queryset = Opportunity.objects.all()

    def _get_document_number(self, obj):
        """
        Create a link to the Opportunity detail page with the document number.
        """
        edit_url = reverse(
            "proposal_app:opportunity:opportunity-detail",
            kwargs={"document_number": obj.document_number},
        )
        return f'<a href="{edit_url}">{obj.document_number}</a>'

    def _get_estimation_stage(self, obj):
        """
        Render the estimation stages for the Opportunity using a partial template.
        """
        t = get_template("proposal/partial/estimation_stages.html")
        return t.render({"o": obj})

    def _get_design_estimation_note(self, obj):
        """
        Render the design estimation note for the Opportunity using a partial template.
        """
        t = get_template("proposal/partial/design_estimation_note.html")
        return t.render({"o": obj})

    def _get_actions(self, obj):
        """
        Generate action buttons for the Opportunity with a link to the detail page.
        """
        t = get_template("proposal/partial/opportunity_detail_and_document_button.html")

        edit_url = reverse(
            "proposal_app:opportunity:opportunity-detail",
            kwargs={"document_number": obj.document_number},
        )
        return t.render(
            {
                "edit_url": edit_url,
                "o": obj,
                "request": self.request,
            }
        )

    def filter_queryset(self, qs):
        """
        Filter the queryset based on the search term.
        """
        # Apply global search if present
        if self.search:
            qs = qs.filter(
                Q(document_number__icontains=self.search)
                | Q(designer__icontains=self.search)
                | Q(estimator__icontains=self.search)
                | Q(pump_electrical_designer__icontains=self.search)
                | Q(design_estimation_note__icontains=self.search)
                | Q(estimation_stage__icontains=self.search)
                | Q(updated_at__icontains=self.search)
            )

        # Apply custom filters
        filters = self.request.GET.get("filters")
        if filters:
            filters = json.loads(filters)
            column = filters.get("column")
            values = filters.get("values")
            filter_type = filters.get("filter_type")
            filter_value = filters.get("filter_value")
            date_range = filters.get("date_range")

            column_filters = {
                0: "document_number",
                1: "designer",
                2: "estimator",
                3: "pump_electrical_designer",
                4: "design_estimation_note",
                5: "estimation_stage",
                6: "updated_at",
            }

            column_name = column_filters.get(column)
            # print("column_name: ", column_name)
            if column_name:
                if values:
                    # print("values: ", values)
                    qs = qs.filter(**{f"{column_name}__in": values})

                if column_name == "updated_at" and date_range:
                    try:
                        start_date, end_date = date_range.split(" - ")
                        start_date = parse_date(start_date)
                        end_date = parse_date(end_date)
                        if start_date and end_date:
                            qs = qs.filter(updated_at__date__range=(start_date, end_date))
                    except ValueError:
                        pass

                if filter_type and filter_value is not None and column_name != "updated_at":
                    filter_mapping = {
                        "equals": "exact",
                        "not_equals": "exact",
                        "begins_with": "startswith",
                        "not_begins_with": "startswith",
                        "ends_with": "endswith",
                        "not_ends_with": "endswith",
                        "contains": "icontains",
                        "not_contains": "icontains",
                    }

                    django_filter = filter_mapping.get(filter_type)
                    if django_filter:
                        lookup = f"{column_name}__{django_filter}"
                        if filter_type.startswith("not_"):
                            qs = qs.exclude(**{lookup: filter_value})
                        else:
                            qs = qs.filter(**{lookup: filter_value})

        # Apply ordering
        order_values = self.request.GET.get("order_values")
        if order_values:
            try:
                order_values = json.loads(order_values)
                if order_values and isinstance(order_values, list) and len(order_values) > 0:
                    column_index = order_values[0][0]
                    direction = order_values[0][1]

                    column_names = [
                        "document_number",
                        "designer",
                        "estimator",
                        "pump_electrical_designer",
                        "design_estimation_note",
                        "estimation_stage",
                        "updated_at",
                    ]
                    if 0 <= column_index < len(column_names):
                        column_name = column_names[column_index]
                        if direction == "asc":
                            qs = qs.order_by(column_name)
                        elif direction == "desc":
                            qs = qs.order_by(f"-{column_name}")
            except (json.JSONDecodeError, IndexError, KeyError):
                pass  # Handle error if order_values is invalid

        return qs

    def prepare_results(self, qs):
        """
        Prepare the results for DataTable by creating row data.
        """
        data = []
        for o in qs:
            data.append(
                {
                    "document_number": self._get_document_number(o),
                    "designer": o.designer if o.designer else " - ",
                    "estimator": o.estimator if o.estimator else " - ",
                    "pump_electrical_designer": o.pump_electrical_designer if o.pump_electrical_designer else " - ",
                    "design_estimation_note": self._get_design_estimation_note(o),
                    "estimation_stage": self._get_estimation_stage(o),
                    "updated_at": o.updated_at.strftime("%m-%d-%Y %I:%M %p"),
                    "actions": self._get_actions(o),
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests for the DataTable view.
        Return JSON response with the filtered and prepared data.
        """
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class OpportunityCreateFromCSVFormView(FormView):
    """
    View for importing Opportunities from a CSV or Excel file.
    Handles form submission for file upload and processes the file.
    """

    template_name = "proposal/opportunity/import_opportunity.html"
    form_class = ImportOpportunityCSVForm

    def form_valid(self, form):
        """
        Handle a valid form submission for file import.
        Process the file and provide feedback to the user.
        """
        csv_file = form.cleaned_data["csv_file"]
        file = csv_file
        _response = import_opportunity_from_xlsx(file)
        if _response.get("error"):
            form.add_error("csv_file", _response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)
        else:
            return JsonResponse(
                {
                    "redirect": reverse("proposal_app:opportunity:opportunity-list"),
                    "message": "Opportunity Import Successfully!!",
                    "status": "success",
                    "code": 200,
                }
            )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)


class OpportunityDetail(ProposalDetailViewMixin):
    """
    View to display detailed information about an Opportunity.
    """

    model = Opportunity
    render_template_name = "proposal/opportunity/opportunity_detail.html"
    context_object_name = "opportunity"

    def get_object(self, queryset=None):
        """
        Override to retrieve the Opportunity object using document_number.
        """
        document_number = self.kwargs.get("document_number")
        return get_object_or_404(Opportunity, document_number=document_number)

    def _get_tasks(self, document_number):
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.exclude(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                product.standard_cost if product.standard_cost else product.vendor_quoted_cost
                for product in task_assigned_products
            )

            total_percent = sum(product.gross_profit_percentage for product in task_assigned_products)

            tasks_with_products[task.id] = {
                "task": task,
                "assigned_products": task_assigned_products,
                "total_quantity": round(total_quantity, 2),
                "total_price": round(total_price, 2),
                "total_percent": round(total_percent, 2),
            }

        return tasks_with_products

    def _get_task_total(self, document_number):
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.exclude(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                product.standard_cost if product.standard_cost else product.vendor_quoted_cost
                for product in task_assigned_products
            )

            tasks_with_products[task.id] = {
                "total_quantity": total_quantity,
                "total_price": total_price,
            }

        # Calculate grand total price correctly
        grand_total_price = sum(v["total_price"] for v in tasks_with_products.values())

        grand_total_quantity = sum(v["total_quantity"] for v in tasks_with_products.values())

        total_data = {
            "grand_total_price": round(grand_total_price, 2),
            "grand_total_quantity": round(grand_total_quantity, 2),
        }
        return total_data

    def _get_labour_tasks(self, document_number):
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.filter(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)
        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)
        tasks_with_products = {}

        for task in filtered_task_mappings:
            tasks_with_products[task.id] = {
                "task": task,
                "assigned_products": assigned_products.filter(task_mapping_id=task.id),
            }
        return tasks_with_products

    def _get_task_products(self, document_number):
        qs = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(
            task__description__icontains="labor"
        )

        return qs

    def _get_task_labor(self, document_number):
        qs = TaskMapping.objects.filter(opportunity__document_number=document_number).filter(
            task__description__icontains="labor"
        )
        return qs

    def _get_total(self, document_number):
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

    def _get_proposal_creation(self, document_number):
        qs = ProposalCreation.objects.filter(opportunity__document_number=document_number).prefetch_related(
            Prefetch("task_mapping__assigned_products")
        )

        grouped_proposals = qs.values("group_name").annotate(count=Count("id"))
        result = {
            group["group_name"]: {
                "proposals": [],
                "assigned_products": defaultdict(list),
                "task_totals": defaultdict(float),
                "main_total": 0.0,
                "proposal_ids": [],
            }
            for group in grouped_proposals
        }

        for proposal in qs:
            group_name = proposal.group_name
            result[group_name]["proposals"].append(
                {
                    "proposal": proposal,
                }
            )

            # Add the ProposalCreation ID to the list
            result[group_name]["proposal_ids"].append(proposal.id)

            # Fetch all assigned products for the task
            assigned_products = proposal.task_mapping.assigned_products.all()  # Get all assigned products
            task_object = proposal.task_mapping

            # Initialize an empty list for filtered assigned products
            filtered_assigned_products = []

            for product in assigned_products:
                if product.is_select:  # Only include selected products
                    filtered_assigned_products.append(product)

                    # Calculate value based on available costs
                    quantity = product.quantity or 0
                    standard_cost = product.standard_cost or 0
                    local_cost = product.local_cost or 0

                    if quantity and standard_cost:
                        value = quantity * standard_cost
                    elif quantity and local_cost:
                        value = quantity * local_cost
                    else:
                        value = 0

                    result[group_name]["task_totals"][task_object] += value
                    result[group_name]["main_total"] += value

            # Store the filtered assigned products
            result[group_name]["assigned_products"][task_object] = filtered_assigned_products

        for group_data in result.values():
            group_data["assigned_products"] = dict(group_data["assigned_products"])
            group_data["task_totals"] = dict(group_data["task_totals"])

        return result

    def _get_proposal_totals(self, document_number):

        invoice = Invoice.objects.get(opportunity__document_number=document_number)

        proposal_creations = ProposalCreation.objects.filter(opportunity__document_number=document_number)

        # Get the related TaskMapping objects
        task_mappings = TaskMapping.objects.filter(id__in=proposal_creations.values_list("task_mapping_id", flat=True))

        # Include all task mappings
        filtered_task_mappings = task_mappings

        # Get task mapping IDs for the assigned products
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        # Retrieve assigned products linked to these task mappings
        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}
        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)

            total_price = sum(
                (product.standard_cost or product.vendor_quoted_cost or 0) * product.quantity
                for product in task_assigned_products
            )

            total_local_cost = sum(
                product.local_cost * product.quantity
                for product in task_assigned_products
                if product.local_cost is not None
            )

            tasks_with_products[task.id] = {
                "total_quantity": total_quantity,
                "total_price": total_price,
                "total_local_cost": total_local_cost,
            }

        # Calculate grand total price correctly
        total_price_sum = sum(v["total_price"] for v in tasks_with_products.values())
        total_local_cost_sum = sum(v["total_local_cost"] for v in tasks_with_products.values())
        grand_total_price = total_price_sum + total_local_cost_sum

        # final price with taxes
        final_total_price = grand_total_price + invoice.sales_tax + invoice.other_tax + (invoice.tax_rate / 100)

        total_data = {
            "grand_total_price": round(grand_total_price, 2),
            "final_total_price": round(final_total_price, 2),
        }

        return total_data

    def _get_new_material_master_data(self, document_number):

        task_mapping_obj = TaskMapping.objects.filter(opportunity__document_number=document_number).values_list(
            "id", flat=True
        )
        new_material_master_data_obj = AssignedProduct.objects.filter(
            task_mapping__id__in=task_mapping_obj, is_assign=False
        )
        return new_material_master_data_obj

    def _get_cost_variances_data(self, document_number):
        task_mapping_obj = TaskMapping.objects.filter(opportunity__document_number=document_number).values_list(
            "id", flat=True
        )
        cost_variances_data = AssignedProduct.objects.filter(
            task_mapping__id__in=task_mapping_obj,
            vendor_quoted_cost__isnull=False,
        )
        return cost_variances_data

    def _get_netsuite_extract_data(self, document_number):
        # First, get the task mapping objects related to the current opportunity
        task_mapping_objs = TaskMapping.objects.filter(opportunity__document_number=document_number)

        # Then, get the assigned products related to those task mappings
        assigned_products = AssignedProduct.objects.filter(task_mapping__in=task_mapping_objs)

        # If you want to convert it to a list or perform further operations
        assigned_products_list = list(assigned_products)
        # print("assigned_products_list", assigned_products_list)
        return assigned_products_list

    def get_context_data(self, **kwargs):
        """
        Returns a dictionary od the context object.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        opportunity = Opportunity.objects.get(document_number=document_number)
        invoice = Invoice.objects.get(opportunity=opportunity)

        context["invoice"] = invoice
        context["stage"] = opportunity.estimation_stage
        context["task_mapping_list"] = self._get_tasks(document_number)
        context["task_mapping_labor_list"] = self._get_labour_tasks(document_number)
        context["task_product_list"] = self._get_task_products(document_number)
        context["task_labor_list"] = self._get_task_labor(document_number)
        context["total"] = self._get_total(document_number)
        context["grouped_proposals"] = self._get_proposal_creation(document_number)
        context["new_material_master_data"] = self._get_new_material_master_data(document_number)
        context["cost_variances_data"] = self._get_cost_variances_data(document_number)
        context["netsuite_extract_data"] = self._get_netsuite_extract_data(document_number)
        context["grand_total"] = self._get_task_total(document_number)
        context["proposal_total"] = self._get_proposal_totals(document_number)

        return context


class UpdateOpportunityView(View):
    """
    Update Opportunity view
    """

    def update_date(self, data):
        try:
            opportunity_obj = Opportunity.objects.get(document_number=data["document_number"][0])
            if data["type"][0] == "job":
                opportunity_obj.job = data["value"][0]
                opportunity_obj.save()
                response_message = {
                    "status": "success",
                    "message": "Job updated successfully",
                }
            elif data["type"][0] == "job_name":
                opportunity_obj.job_name = data["value"][0]
                opportunity_obj.save()
                response_message = {
                    "status": "success",
                    "message": "Job name Updated successfully",
                }
            elif data["type"][0] == "project":
                opportunity_obj.project = data["value"][0]
                opportunity_obj.save()
                response_message = {
                    "status": "success",
                    "message": "Project name Updated successfully",
                }
            elif data["type"][0] == "ranch":
                opportunity_obj.ranch_name = data["value"][0]
                opportunity_obj.save()
                response_message = {
                    "status": "success",
                    "message": "Ranch name Updated successfully",
                }
            elif data["type"][0] == "term_and_condition":

                json_data = json.loads(data["value"][0])
                if opportunity_obj.term_and_condition != json_data:
                    opportunity_obj.term_and_condition = json_data
                    opportunity_obj.save()
                    response_message = {
                        "status": "success",
                        "message": "Terms Updated successfully",
                    }
                else:
                    response_message = {}
            return response_message
        except Exception as e:
            print("Error [UpdateOpportunity][update_date]", e)
            return {"status": "error", "message": "something went wrong please try again"}

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            # print(f"data ==>>: {data}")
            response = self.update_date(data)
            return JsonResponse(response)
        except Exception as e:
            print("Error [UpdateOpportunity]", e)
            return JsonResponse({"status": "error", "message": "something went wrong please try again"}, status=400)


class SelectedTaskListAjaxView(DataTableMixin, View):
    model = SelectTaskCode

    def get_queryset(self):
        """Returns a list of selected tasks"""
        document_number = self.kwargs.get("document_number")
        qs = SelectTaskCode.objects.filter(opportunity__document_number=document_number)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(task__internal_id__icontains=self.search)
                | Q(task__name__icontains=self.search)
                | Q(task__description__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "task__internal_id": o.task.internal_id,
                    "task__name": o.task.name,
                    "task__description": o.task.description,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class TaskManagementView(View):
    """
    Handle both rendering of the task selection form and task creation.
    """

    template_name = "proposal/opportunity/stage/select_task_code/select_task_code_model.html"

    def get(self, request, *args, **kwargs):
        """
        Render the task selection template with available tasks.
        """
        document_number = self.kwargs.get("document_number")
        context = self._get_context_data(document_number)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        """
        Handle task selection and creation.
        """
        tasks = request.POST.getlist("task")
        document_number = request.POST.get("document_number")

        if tasks and document_number:
            try:
                opportunity = Opportunity.objects.get(document_number=document_number)

                for task_name in tasks:
                    task_instance = Task.objects.get(name=task_name)
                    SelectTaskCode.objects.create(opportunity=opportunity, task=task_instance)

                messages.success(self.request, f"Tasks added successfully!")
                return JsonResponse(
                    {
                        "success_url": reverse("proposal_app:opportunity:opportunity-detail", args=(document_number,)),
                        "modal_to_close": "modelSelectTask",
                    },
                    status=201,
                )

            except Opportunity.DoesNotExist:
                return JsonResponse({"error": "Opportunity not found."}, status=404)
            except Task.DoesNotExist:
                return JsonResponse({"error": "One or more tasks not found."}, status=404)

        return JsonResponse({"error": "Tasks and document number are required."}, status=400)

    def _get_context_data(self, document_number):
        """
        Returns context data with available tasks.
        """
        context = {}
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            context["select_tasks"] = Task.objects.none()
            return context

        selected_task_ids = SelectTaskCode.objects.filter(opportunity=opportunity).values_list("task_id", flat=True)
        context["select_tasks"] = Task.objects.exclude(id__in=selected_task_ids)
        context["document_number"] = document_number
        return context

    def render_to_response(self, context, **response_kwargs):
        """
        Render the response using the template specified.
        """
        return render(self.request, self.template_name, context, **response_kwargs)


# ====================================          ===============================
# ==================================== Document ===============================
# ====================================          ===============================
class DocumentListAjaxView(DataTableMixin, View):

    model = Document

    def get_queryset(self):
        document_number = self.kwargs.get("document_number")
        stage = self.kwargs.get("stage")
        qs = Document.objects.filter(opportunity__document_number=document_number, stage=stage)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(document_icontains=self.search)
                | Q(comment_icontains=self.search)
                | Q(created_at_icontains=self.search)
            )
        return qs

    def _get_documents(self, obj):
        if obj.document:
            return f"<div class='text-center'><a href='{obj.file_path}' target='_blank' download><i class='icon-cloud-download'></i> {obj.document.name}</a></div>"
        else:
            return "<div class='text-center'>-</div>"

    def _get_comments(self, obj):
        if obj.comment:
            return f"<div class='text-center'>{obj.comment}</div>"
        else:
            return "<div class='text-center'>-</div>"

    def _get_created_at(self, obj):
        if obj.created_at:
            created_at = obj.created_at.strftime("%m-%d-%Y")
            return f"<div class='text-center'>{created_at}</div>"
        else:
            return "<div class='text-center'>-</div>"

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "document": self._get_documents(o),
                    "created_at": self._get_created_at(o),
                    "comment": self._get_comments(o),
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class UploadDocument(CreateView):
    """
    Upload a documents.
    """

    model = Document
    form_class = UploadDocumentForm
    template_name = "proposal/file_upload.html"

    def form_valid(self, form):
        document_number = self.request.POST.get("document_number")
        comment = self.request.POST.get("comment")
        stage = self.request.POST.get("stage")
        opportunity_object = Opportunity.objects.get(document_number=document_number)
        if document_number or comment:
            form.instance.opportunity = opportunity_object
            form.instance.stage = stage
            form.instance.comment = comment
            form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors:
            print("Form Error ==>> :", error)
        return super().form_invalid(form)

    def get_success_url(self):
        document_number = self.request.POST.get("document_number")
        return reverse("proposal_app:opportunity:opportunity-detail", args=(document_number,))


class UpdateStages(View):
    """
    Update Opportunity Stages.
    """

    def post(self, request):
        try:
            data = json.loads(request.body)
            document_number = data.get("document_number")
            updated_stage = data.get("stage")
            # print(f"updated_stage : {updated_stage}")

            if not document_number or not updated_stage:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            opportunity = get_object_or_404(Opportunity, document_number=document_number)
            current_stage = opportunity.get_current_stage_constant()
            # print("current_stage", current_stage)
            estimation_stage = getattr(Opportunity, updated_stage)
            # print("Estimation Stage", estimation_stage)
            if current_stage < updated_stage:
                opportunity.estimation_stage = estimation_stage
                opportunity.updated_at = datetime.datetime.now()
                opportunity.save()
                return JsonResponse({"message": "Opportunity stage updated successfully"}, status=200)
            else:
                return JsonResponse({"message": "Opportunity stage lower than current stage"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class OpportunityFilterView(View):
    column_mapping = {
        "Document Number": "document_number",
        "Designer": "designer",
        "Estimator": "estimator",
        "Pump Electrical Designer": "pump_electrical_designer",
        "Design Estimation Note": "design_estimation_note",
        "Estimation Stage": "estimation_stage",
        "Updated At": "updated_at",
    }

    def get(self, request, column):
        search_query = request.GET.get("search", "").strip()

        # Map column name to model field
        field = self.column_mapping.get(column, column)
        if field not in self.column_mapping.values():
            return JsonResponse({"error": "Invalid column name"}, status=400)

        # Base queryset for distinct values
        queryset = Opportunity.objects.all()

        # Add search functionality if at least 2 characters are entered
        if search_query and len(search_query) >= 2:
            queryset = queryset.filter(Q(**{f"{field}__icontains": search_query}))

        choices = queryset.values_list(field, flat=True).distinct()
        options = list(choices)
        return JsonResponse({"options": options})


# ====================================                 ===============================
# ==================================== UPload CAD File ===============================
# ====================================                 ===============================


class UploadCADFile(View):

    def generate_material_list(self, uploaded_file, document_number):
        """
        Generates material list from an uploaded file.

        :param uploaded_file: Uploaded file object (InMemoryUploadedFile).
        :param document_number: Document number for the associated opportunity.
        :return: Dictionary containing the material list data.
        """
        material_list_obj = MaterialList.objects.filter(opportunity__document_number=document_number)
        # print("Len :::::::::", len(material_list_obj))

        if len(material_list_obj) != 0:
            MaterialList.objects.filter(opportunity__document_number=document_number).delete()
            GlueAndAdditionalMaterial.objects.filter(opportunity__document_number=document_number).delete()
            PreliminaryMaterialList.objects.filter(opportunity__document_number=document_number).delete()

        data = {"Quantity": [], "Description": [], "Item Number": []}

        # Get the opportunity instance to save the material list data
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            print(f"Opportunity with document number {document_number} not found.")
            return data

        # Read the file content
        file_content = uploaded_file.read().decode("utf-8")
        file_like_object = StringIO(file_content)

        reader = csv.reader(file_like_object)
        for row in reader:
            if len(row) != 3:
                continue

            quantity, description, item_number = row

            # Append the values to the corresponding lists in the dictionary
            data["Quantity"].append(float(quantity))
            data["Description"].append(description)
            data["Item Number"].append(item_number)

            # Save data into the database
            MaterialList.objects.create(
                opportunity=opportunity, quantity=float(quantity), description=description, item_number=item_number
            )
        return data

    # --Helper function to generate rows with calculations for Material List.
    def apply_transformations(self, row):
        description = row["Description"]

        # Formula for form1
        form1 = description.replace('"', "")

        # Formula for form2
        if '"' in description:
            quote_index = description.find('"')
            form2 = description[:3] + description[quote_index - 2 : quote_index]
        else:
            form2 = description[:3]  # fallback if no quote found

        # Formula for form3
        if '"' in description:
            quote_index = description.find('"')
            form3 = description[quote_index - 5 : quote_index].replace("  ", " ")
        else:
            form3 = description  # fallback if no quote found

        # Formula for form4
        if " " in form3:
            space_index = form3.find(" ")
            form4 = description[:3] + " " + form3[space_index + 1 : space_index + 11].strip()
        else:
            form4 = description[:3]  # fallback if no space found in form3

        return pd.Series([form1, form2, form3, form4], index=["form1", "form2", "form3", "form4"])

    # --Helper function to generate rows with calculations for Material List.
    def calculate_additional_columns(self, row):
        description = row["Description"]
        form1 = row["form1"]
        form3 = row["form3"]

        # Extract 'Tee's'
        if "TEE" in description:
            if "X " in description:
                start_index = description.find("X ") + 2
                tee_value = description[start_index : start_index + 4].strip()
            else:
                tee_value = description.split(" ")[-1].strip()
        else:
            tee_value = "ERR"

        # Extract 'RED BUSH & COUPS'
        if "RED BUSH" in description:
            red_bush_value = description.split("X ")[-1].split("SPXS")[0].strip()
        elif "RED COUP" in description:
            red_bush_value = description.split("X ")[-1].strip()
        else:
            red_bush_value = "IFERR"

        # Extract 'CROSS'
        if "CROSS" in form1:
            if "X " in form1:
                start_index = form1.find("X ") + 2
                cross_value = form1[start_index : start_index + 4].strip()
            else:
                if " " in form3:
                    space_index = form3.find(" ")
                    cross_value = form3[space_index + 1 : space_index + 4].strip()
                else:
                    cross_value = "ERR"
        else:
            cross_value = "ERR"

        # Extract 'Hose'
        hose_value = description[:14].strip()

        return pd.Series(
            [tee_value, red_bush_value, cross_value, hose_value], index=["Tee's", "RED BUSH & COUPS", "CROSS", "Hose"]
        )

    # -Helper function to generate rows with calculations for Glue & Additional Material List.
    def calculate_mains_manifold(self, df, pipe_size, joints_per_pint):
        # Filters based on pipe size and type
        solvent_weld_pipe = df[
            df["form1"].str.contains(f"PIPE.*{pipe_size} SW", case=False, na=False)
            | df["form1"].str.contains(f"PIPE.*{pipe_size} BE", case=False, na=False)
        ]

        # Cross joints calculation using the formula provided
        cross_joints_from_form4 = df[df["form4"].str.contains(f"CRO {pipe_size}", case=False, na=False)][
            "Quantity"
        ].sum()
        cross_joints_from_cross = df[df["CROSS"].str.contains(f"{pipe_size}", case=False, na=False)]["Quantity"].sum()
        cross_joints_sum = (cross_joints_from_form4 + cross_joints_from_cross) * 2

        # Tee joints calculation
        tee_joints_formula = (
            df[df["form4"].str.contains(f"TEE {pipe_size}", case=False, na=False)]["Quantity"].sum() * 2
        ) + df[df["Tee's"].str.contains(f"{pipe_size}", case=False, na=False)]["Quantity"].sum()

        # Elbow, Coupler, RB, RC Joints calculation
        elbow_coupler_rb_rc_joints = (
            df[df["form4"].str.contains(f"ELB {pipe_size}", case=False, na=False)]["Quantity"].sum() * 2
            + df[df["form4"].str.contains(f"COU {pipe_size}", case=False, na=False)]["Quantity"].sum() * 2
            + df[df["form4"].str.contains(f"RED {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["form4"].str.contains(f"FLA {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["form4"].str.contains(f"CAP {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["form4"].str.contains(f"FA {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["form4"].str.contains(f"MA {pipe_size}", case=False, na=False)]["Quantity"].sum()
            + df[df["RED BUSH & COUPS"].str.contains(f"{pipe_size}", case=False, na=False)]["Quantity"].sum()
        )

        # Sum quantities
        solvent_weld_pipe_sum = solvent_weld_pipe["Quantity"].sum()
        cross_joints_sum = cross_joints_sum
        tee_joints_sum = tee_joints_formula
        elbow_coupler_rb_rc_joints_sum = elbow_coupler_rb_rc_joints
        total_joints = (solvent_weld_pipe_sum / 20) + cross_joints_sum + tee_joints_sum + elbow_coupler_rb_rc_joints_sum
        pints = total_joints / joints_per_pint
        thrust_block_conc_bags = 0

        return {
            "Pipe Size": pipe_size,
            "Solvent Weld Pipe": solvent_weld_pipe_sum,
            "Cross Joints": cross_joints_sum,
            "Tee Joints": tee_joints_sum,
            "Elbow, Coupler, RB, RC Joints": elbow_coupler_rb_rc_joints_sum,
            "TOTAL JOINTS": total_joints,
            "JOINTS PER PINT": joints_per_pint,
            "PINTS": round(pints, 1),
            "Thrust Block # Conc. Bags": thrust_block_conc_bags,
        }

    # --Helper function to generate rows with calculations for Glue & Additional Material List.
    def calculate_flex_riser_quantities(self, df, values):
        results = []

        # Calculate the quantity for '1/2' Flex Risers (C37) and '1/2' Saddles (D37)
        flex_riser_half_data = df[df["form1"].str.contains("FLEX RISER", case=False, na=False)]
        flex_riser_half_sum = flex_riser_half_data.groupby("form1")["Quantity"].sum().reset_index()
        flex_riser_half_sum = flex_riser_half_sum[
            flex_riser_half_sum["form1"].str.contains("1/2", case=False, na=False)
        ]
        C37 = flex_riser_half_sum["Quantity"].sum()

        saddle_half_data = df[df["form1"].str.contains("SADDLE", case=False, na=False)]
        saddle_half_sum = saddle_half_data.groupby("form1")["Quantity"].sum().reset_index()
        saddle_half_sum = saddle_half_sum[saddle_half_sum["form1"].str.contains("1/2", case=False, na=False)]
        D37 = saddle_half_sum["Quantity"].sum()

        for value in values:
            # Filter for Flex Risers
            flex_riser_data = df[df["form1"].str.contains("FLEX RISER", case=False, na=False)]

            # Aggregate quantities for Flex Risers
            flex_riser_sum = flex_riser_data.groupby("form1")["Quantity"].sum().reset_index()
            flex_riser_sum = flex_riser_sum[flex_riser_sum["form1"].str.contains(f"{value}", case=False, na=False)]
            flex_riser_total = flex_riser_sum["Quantity"].sum()

            # Special handling for value == '1'
            if value == "1":
                if flex_riser_total == 0:
                    flex_riser_total = 0
                else:
                    flex_riser_total = flex_riser_total - C37

            # Filter for Saddles
            saddle_data = df[df["form1"].str.contains("SADDLE", case=False, na=False)]

            # Aggregate quantities for Saddles
            saddle_sum = saddle_data.groupby("form1")["Quantity"].sum().reset_index()
            saddle_sum = saddle_sum[saddle_sum["form1"].str.contains(f"{value}", case=False, na=False)]
            saddle_total = saddle_sum["Quantity"].sum()

            # Special handling for value == '1'
            if value == "1":
                if saddle_total == 0:
                    saddle_total = 0
                else:
                    saddle_total = saddle_total - D37

            # Calculate Total Joints
            total_joints = flex_riser_total + saddle_total

            # Define Joints per Pint
            if value == "1":
                joints_per_pint = 25
            elif value == "1/2":
                joints_per_pint = 50
            elif value == "3/4":
                joints_per_pint = 50
            else:
                joints_per_pint = 0

            # Calculate Pints
            pints = total_joints / joints_per_pint

            # Append result for current value
            results.append(
                {
                    "Size": value,
                    "Flex Risers": flex_riser_total,
                    "Saddles": saddle_total,
                    "Total Joints": total_joints,
                    "JOINTS PER PINT": joints_per_pint,
                    "Pints": round(pints, 1),
                }
            )

        # Create DataFrame for Flex Risers and Saddles
        flex_riser_summary = pd.DataFrame(results)

        return flex_riser_summary

    def generate_glue_and_additional_material_list(self, document_number):
        """
        Generate Glue and Additional Material List.

        :param document_number: Document number for the associated opportunity.
        """
        glue_and_additional_data = {
            "Quantity": [1, 2, 1, 2, 2, 7, 7, 14, 4, 2, 25, 2, 11, 25, 11, 11, 22, 36, 12, 3, 1],
            "Form1": [
                ",1",
                ",2",
                ",1",
                ",2",
                ",2",
                ",7",
                ",7",
                ",14",
                ",4",
                ",2",
                ",25",
                ",2",
                ",11",
                ",25",
                ",11",
                ",11",
                ",22",
                ",36",
                ",12",
                ",3",
                ",1",
            ],
            "Form2": [
                ",1",
                ",2",
                ",1",
                ",2",
                ",2",
                ",7",
                ",7",
                ",14",
                ",4",
                ",2",
                ",25",
                ",2",
                ",11",
                ",25",
                ",11",
                ",11",
                ",22",
                ",36",
                ",12",
                ",3",
                ",1",
            ],
            "Description": [
                "Cement -711 Heavy Gray, Gallon",
                "Cement -719 Extra Heavy Gray, Quart",
                "Cement - Primer Purple P70 Gal",
                "CEMENT - RED HOT CLEAR, PINT",
                "CEMENT - RED HOT CLEAR, PINT (HOSE FITTINGS)",
                'Cement - Empty Can, Quart 1.75" Neck',
                'Cement - Empty Can, Pint 1.75" Neck',
                "Cement - Dauber for Quart Can",
                "Cement - Dauber for Pint Can",
                "Cement - Dauber for Pint Can (HOSE FITTINGS)",
                'COUPLER BLACK 1/2"',
                'COUPLER S40 2"',
                "PERMA-LOC X SWIVEL-W TEE 062",
                "PERMA-LOC COUPLING 062",
                'Ball Valve, Riser 3/4" FHTxMHT',
                'MALE HOSE ADAP X 1/2"S(3/4"SP)',
                "FIGURE 8 062",
                'FLEX RISER 1/2" X 48"',
                'SADDLE 1/2" X 2"',
                'CUT PIPE PVC S40 2" x 48"',
                'SURVEY FLAGS GLO ORA 21" WIRE ',
            ],
            "Item": [
                "4200-001600",
                "4200-002500",
                "4200-007500",
                "4200-005000",
                "4200-005000",
                "4200-013000",
                "4200-013500",
                "4200-014500",
                "4200-015000",
                "4200-015000",
                "2800-116500",
                "429020",
                "2800-006000",
                "2800-001000",
                "2800-117500",
                "2800-114000",
                "2800-118500",
                "6200-008000",
                "2800-105000",
                "5400-031120",
                "3600-004500",
            ],
            "Category": [
                "#N/A",
                "GLU010",
                "GLU020",
                "GLU010",
                "FHO",
                "GLU040",
                "GLU040",
                "GLU040",
                "GLU040",
                "FHO",
                "FHO910",
                "FMP429",
                "FHO010",
                "FHO005",
                "FHO915",
                "FHO905",
                "FHO920",
                "TUB030",
                "FHO900",
                "PIP010",
                "FSO020",
            ],
        }

        # Get the opportunity instance to save the Glue and Additional material list data
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            print(f"Opportunity with document number {document_number} not found.")
            return glue_and_additional_data

        for i in range(len(glue_and_additional_data["Item"])):
            GlueAndAdditionalMaterial.objects.create(
                opportunity=opportunity,
                quantity=glue_and_additional_data["Quantity"][i],
                description=glue_and_additional_data["Description"][i],
                item_number=glue_and_additional_data["Item"][i],
                category=glue_and_additional_data["Category"][i],
            )

        return glue_and_additional_data

    # --Helper function to generate rows with calculations for Glue & Additional Material List.
    def add_to_merged_data(self, data, key_field, merged_data):
        for quantity, description, item_number in zip(data["Quantity"], data["Description"], data[key_field]):
            if item_number in merged_data:
                # Append quantity if item number already exists
                merged_data[item_number]["Quantity"].append(quantity)
            else:
                # Create a new entry
                merged_data[item_number]["Description"] = description
                merged_data[item_number]["Item Number"] = item_number
                merged_data[item_number]["Quantity"] = [quantity]

    def generate_preliminary_material_list(self, material_list, glue_and_additional_data, document_number):
        """
        Generate and save preliminary material list into database.

        :param material_list : Material List data.
        :param glue_and_additional_data : Glue & Additional Material List data.
        :param document_number: Document number for the associated opportunity.
        """
        # Get the opportunity instance to save the Glue and Additional material list data
        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            print(f"Opportunity with document number {document_number} not found.")
            return glue_and_additional_data

        # Initialize data structures
        irricad_data = material_list
        glue_data = glue_and_additional_data

        # Create dictionaries for mapping item numbers to quantities
        irricad_quantities = {
            item: quantity for item, quantity in zip(irricad_data["Item Number"], irricad_data["Quantity"])
        }
        glue_quantities = {item: quantity for item, quantity in zip(glue_data["Item"], glue_data["Quantity"])}

        # Create a dictionary to hold the combined results
        combined_data = defaultdict(lambda: {"Irricad Imported Quantities": 0, "Glue & Additional Mat'l Quantities": 0})
        # Populate combined data with quantities from Irricad
        for item_number, quantity in irricad_quantities.items():
            combined_data[item_number]["Irricad Imported Quantities"] += quantity

        # Populate combined data with quantities from Glue & Additional Mat'l
        for item_number, quantity in glue_quantities.items():
            combined_data[item_number]["Glue & Additional Mat'l Quantities"] += quantity

        # Calculate Combined Quantities from both Imports
        for item_number in combined_data:
            combined_data[item_number]["Combined Quantities from both Imports"] = (
                combined_data[item_number]["Irricad Imported Quantities"]
                + combined_data[item_number]["Glue & Additional Mat'l Quantities"]
            )

        # Map descriptions from both data sources
        description_dict = {}
        # Populate descriptions from glue_data
        for item, description in zip(glue_data["Item"], glue_data["Description"]):
            description_dict[item] = description
        # Add descriptions from irricad_data if not already present
        for item, description in zip(
            irricad_data["Item Number"], irricad_data["Description"] * len(irricad_data["Item Number"])
        ):
            if item not in description_dict:
                description_dict[item] = description

        # Populate the final combined dictionary
        final_data = {
            "Irricad Imported Quantities": [],
            "Glue & Additional Mat'l Quantities": [],
            "Combined Quantities from both Imports": [],
            "Description": [],
            "Item Number": [],
        }

        for item_number, values in combined_data.items():
            final_data["Item Number"].append(item_number)
            final_data["Description"].append(description_dict.get(item_number, "Description not available"))
            final_data["Irricad Imported Quantities"].append(values["Irricad Imported Quantities"])
            final_data["Glue & Additional Mat'l Quantities"].append(values["Glue & Additional Mat'l Quantities"])
            final_data["Combined Quantities from both Imports"].append(values["Combined Quantities from both Imports"])

        # TODO: Need to Create category and bag_bundle_quantity dynamically.
        for item_number, values in combined_data.items():
            PreliminaryMaterialList.objects.create(
                opportunity=opportunity,
                irricad_imported_quantities=values["Irricad Imported Quantities"],
                glue_and_additional_mat_quantities=values["Glue & Additional Mat'l Quantities"],
                combined_quantities_from_both_import=values["Combined Quantities from both Imports"],
                description=description_dict.get(item_number, "Description not available"),
                item_number=item_number,
                category="",
                bag_bundle_quantity="",
            )

        return final_data

    def post(self, request, *args, **kwargs):
        """
        Handel POST request for uploaded CAD File.
        """
        if "file" not in request.FILES:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        uploaded_file = request.FILES["file"]
        document_number = request.POST.get("document_number")

        if uploaded_file.name.lower().endswith(".tmp"):
            # Generate and save Material List
            # NOTE: Converted Macro code into python ("Split List")
            material_list = self.generate_material_list(uploaded_file, document_number)
            material_list_df = pd.DataFrame(material_list)
            # print("Material List Df",material_list_df)

            # Helper function to calculate ['form1', 'form2', 'form3', 'form4'] for material list
            material_list_df[["form1", "form2", "form3", "form4"]] = material_list_df.apply(
                self.apply_transformations, axis=1
            )

            # Helper function to calculate ['Tee\'s', 'RED BUSH & COUPS', 'CROSS', 'Hose'] for material list
            material_list_df[["Tee's", "RED BUSH & COUPS", "CROSS", "Hose"]] = material_list_df.apply(
                self.calculate_additional_columns, axis=1
            )

            # Define pipe sizes and joints per pint
            pipe_sizes = [24, 21, 20, 18.7, 15, 12, 10, 8, 6, 5, 4, 3, 2.5, 2]
            joints_per_pint_values = {
                24: 0.0625,
                21: 0.125,
                20: 0.125,
                18.7: 0.25,
                15: 0.375,
                12: 0.5,
                10: 1,
                8: 2,
                6: 5,
                5: 10,
                4: 15,
                3: 20,
                2.5: 25,
                2: 30,
            }

            # Calculate values for each pipe size
            mains_manifold_results = []
            for pipe_size in pipe_sizes:
                joints_per_pint = joints_per_pint_values.get(pipe_size, "")
                mains_manifold_data = self.calculate_mains_manifold(material_list_df, pipe_size, joints_per_pint)
                mains_manifold_results.append(mains_manifold_data)

            # Create a DataFrame for mains and manifold pipes
            # mains_manifold_df = pd.DataFrame(mains_manifold_results)

            # Calculate Flex Riser Quantities
            values = ["1/2", "3/4", "1"]
            # flex_riser_df = self.calculate_flex_riser_quantities(material_list_df, values)
            self.calculate_flex_riser_quantities(material_list_df, values)

            # Generate and save Glue & Additional Material List
            # NOTE: Converted Macro code into python ("Run Miscellaneous Material")
            # _glue_and_additional_data_df
            glue_and_additional_data = self.generate_glue_and_additional_material_list(document_number)
            # glue_and_additional_data_df = pd.DataFrame(glue_and_additional_data)

            # Generate and save Preliminary Material List
            # NOTE: Converted Macro code into python ("Import Material from Previous Tabs", "FINALIZE MATERIAL")

            # --[Import Material from Previous Tabs]
            # Dictionary to store merged data
            merged_data = defaultdict(lambda: {"Quantity": [], "Description": None, "Item Number": None})

            # Add both datasets to merged_data
            self.add_to_merged_data(material_list, "Item Number", merged_data)
            self.add_to_merged_data(glue_and_additional_data, "Item", merged_data)

            # Convert quantities to comma-separated strings and finalize the merged data
            final_merged_data = {
                "Quantity": [],
                "Item Number": [],
                "Description": [],
            }

            for item_number, values in merged_data.items():
                final_merged_data["Item Number"].append(values["Item Number"])
                final_merged_data["Description"].append(values["Description"])
                final_merged_data["Quantity"].append(",".join(map(str, values["Quantity"])))

            # import_from_previous_data = pd.DataFrame(final_merged_data)
            # import_from_previous_data_df = import_from_previous_data.sort_values(by='Item Number').reset_index(drop=True)

            # --[FINALIZE MATERIAL]
            # Generate and save preliminary material list data
            # preliminary_material_list = self.generate_preliminary_material_list(material_list, glue_and_additional_data, document_number)
            # preliminary_material_list_df = pd.DataFrame(preliminary_material_list)
            self.generate_preliminary_material_list(material_list, glue_and_additional_data, document_number)

            return JsonResponse(
                {
                    "message": "Generated Material list, Glue & Additional Material List and Preliminary Material List successfully"
                },
                status=200,
            )

        return JsonResponse({"error": "Invalid file format. Only .Tmp files are supported."}, status=400)


class MaterialListAjaxView(DataTableMixin, View):

    model = MaterialList

    def get_queryset(self):
        document_number = self.kwargs.get("document_number")
        qs = MaterialList.objects.filter(opportunity__document_number=document_number)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(quantity__icontains=self.search)
                | Q(description__icontains=self.search)
                | Q(item_number__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "quantity": o.quantity,
                    "description": o.description,
                    "item_number": o.item_number,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class GlueAndAdditionalMaterialAjaxView(DataTableMixin, View):

    model = GlueAndAdditionalMaterial

    def get_queryset(self):
        document_number = self.kwargs.get("document_number")
        qs = GlueAndAdditionalMaterial.objects.filter(opportunity__document_number=document_number)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(quantity__icontains=self.search)
                | Q(description__icontains=self.search)
                | Q(item_number__icontains=self.search)
                | Q(category__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "quantity": o.quantity,
                    "description": o.description,
                    "item_number": o.item_number,
                    "category": o.category,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class PreliminaryMaterialListAjaxView(DataTableMixin, View):

    model = PreliminaryMaterialList

    def get_queryset(self):
        document_number = self.kwargs.get("document_number")
        qs = PreliminaryMaterialList.objects.filter(opportunity__document_number=document_number)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(irricad_imported_quantities__icontains=self.search)
                | Q(glue_and_additional_mat_quantities__icontains=self.search)
                | Q(combined_quantities_from_both_import__icontains=self.search)
                | Q(description__icontains=self.search)
                | Q(item_number__icontains=self.search)
                | Q(category__icontains=self.search)
                | Q(bag_bundle_quantity__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "irricad_imported_quantities": o.irricad_imported_quantities,
                    "glue_and_additional_mat_quantities": o.glue_and_additional_mat_quantities,
                    "combined_quantities_from_both_import": o.combined_quantities_from_both_import,
                    "description": o.description,
                    "item_number": o.item_number,
                    "category": o.category,
                    "bag_bundle_quantity": o.bag_bundle_quantity,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


# ====================================              ===============================
# ==================================== Task Mapping ===============================
# ====================================              ===============================
class AssignProdLabor(TemplateView):
    """
    Import data from CSV or Excel files.
    """

    template_name = "proposal/opportunity/assign_prod_labor.html"

    def _get_products_data(self, task_mapping_id, document_number):
        all_products = PreliminaryMaterialList.objects.filter(opportunity__document_number=document_number)
        # print("All Products =>>", all_products)

        assigned_item_codes = AssignedProduct.objects.filter(task_mapping__id=task_mapping_id).values_list(
            "item_code", flat=True
        )
        # print("Assigned product ==>", assigned_item_codes)

        try:
            assigned_product_ids = [int(code) for code in assigned_item_codes]
        except ValueError:
            assigned_product_ids = []
        # print("Assigned product ID's ==>", assigned_product_ids)

        available_products = all_products.exclude(item_number__in=assigned_product_ids)
        return available_products

    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get("items", "[]"))
        # print("data ==>", data)
        document_number = self.kwargs["document_number"]
        task_id = self.kwargs.get("task_id")

        if not task_id:
            return JsonResponse({"status": "error", "message": "Task ID is missing"}, status=400)

        try:
            task_mapping_obj = TaskMapping.objects.get(id=task_id)
        except TaskMapping.DoesNotExist:
            return JsonResponse({"status": "error", "message": "TaskMapping not found"}, status=404)

        created_products = []
        errors = []

        for i in data:
            try:
                prod_obj = PreliminaryMaterialList.objects.get(
                    opportunity__document_number=document_number, item_number=i["internal_id"]
                )

                assigned_product = AssignedProduct(
                    task_mapping=task_mapping_obj,
                    quantity=prod_obj.combined_quantities_from_both_import,
                    item_code=prod_obj.item_number,
                    description=prod_obj.description,
                    standard_cost=2,
                    is_assign=True,
                )

                assigned_product.save()
                created_products.append(assigned_product.id)

            except Product.DoesNotExist:
                errors.append({"internal_id": i["internal_id"], "error": "Product not found"})

            except Exception as e:
                print("Error", e)

        if errors:
            return JsonResponse({"status": "error", "errors": errors}, status=404)

        if task_mapping_obj.code:
            messages.success(self.request, f'Product assigned for "{task_mapping_obj.code}" successfully!')
        else:
            messages.success(self.request, f'Product assigned for "{task_mapping_obj.task.name}" successfully!')

        return JsonResponse({"status": "success", "created_products": created_products})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs["document_number"]
        task_mapping_id = self.kwargs["task_id"]
        context["products"] = self._get_products_data(task_mapping_id, document_number)
        context["document_number"] = document_number
        context["task_id"] = task_mapping_id
        return context


class UpdateAssignProdView(View):
    """
    Update data based on input
    """

    def update_fields(self, data):
        """
        Update fields on database based on input
        """
        input_type = data.get("type", [""])[0]
        id = data.get("id", [""])[0]
        value = data.get("value", [""])[0]
        # print("value", value)

        if input_type == "task" or input_type == "task":
            task_mapping = TaskMapping.objects.get(id=id)
        else:
            assigned_prod = AssignedProduct.objects.get(id=id)

        if input_type == "quantity":

            assigned_prod.quantity = value
            assigned_prod.save()

            response_data = {"status": "success", "message": f"Quantity updated successfully"}
        elif input_type == "vendor-quoted-cost":

            assigned_prod.vendor_quoted_cost = value
            assigned_prod.save()

            response_data = {"status": "success", "message": f"Vendor quoted updated successfully"}
        elif input_type == "comment":

            assigned_prod.comment = value
            assigned_prod.save()

            response_data = {"status": "success", "message": f"Comment updated successfully"}

        elif input_type == "vendor":

            vendor_value = Vendor.objects.get(id=value)
            assigned_prod.vendor = vendor_value.name
            assigned_prod.save()

            response_data = {"status": "success", "message": f"Vendor updated successfully"}

        elif input_type == "task":

            task = Task.objects.get(id=value)
            task_mapping.task = task
            task_mapping.save()

            response_data = {"status": "success", "message": f"Task updated successfully"}

        elif input_type == "labor-task":

            task = Task.objects.get(id=value)
            task_mapping.task = task
            task_mapping.save()

            response_data = {"status": "success", "message": f"Labor Task updated successfully"}

        else:
            response_data = {"status": "error", "message": "Invalid type"}

        return response_data

    def bulk_update(self, data):
        try:
            rows = {}
            for key, value in data.items():
                if key.startswith("rows["):  # Only process keys that start with 'rows['
                    row_index = key.split("[")[1].split("]")[0]
                    field_name = key.split("[")[2].split("]")[0]

                    if row_index not in rows:
                        rows[row_index] = {}

                    rows[row_index][field_name] = value[0].strip()  # Clean whitespace

            for index, row in rows.items():
                # print(f"Row {index}:")
                for field, value in row.items():
                    if field == "assign_prod_id":
                        assigned_prod_obj = AssignedProduct.objects.get(id=value)
                    elif field == "quantity":
                        assigned_prod_obj.quantity = value
                        assigned_prod_obj.save()
                    elif field == "quotedCost":
                        assigned_prod_obj.vendor_quoted_cost = value
                        assigned_prod_obj.save()
                    # elif field == "local_cost":
                    #     assigned_prod_obj.local_cost = value
                    #     assigned_prod_obj.save()
                    # elif field == "out_of_town_cost":
                    #     assigned_prod_obj.out_of_town_cost = value
                    #     assigned_prod_obj.save()

            messages.success(self.request, "Updated Successfully")
            return {"status": "success", "type": "bulk_update", "message": "Product Updated Successfully"}

        except Exception as e:

            print("Error: [UpdateAssignProdView][bulk_update]", e)
            return {"status": "error", "message": "Something went wrong please try again"}

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            if data.get("type")[0] == "bulk_update":
                _response = self.bulk_update(data)
            else:
                _response = self.update_fields(data)
            return JsonResponse(_response)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)


class AddProdRowView(View):
    """
    Add row product data
    """

    def format_data(self, input_data):
        result = {}

        for key, value in input_data.items():
            parts = key.split("][")
            field_name = parts[1].split("]")[0]

            index = parts[0].split("[")[-1]
            task_id = input_data.get(f"rows[{index}][task_id]", [None])[0]

            if task_id not in result:
                result[task_id] = []

            task_data = {field_name: value[0]}

            existing_entry = next((entry for entry in result[task_id] if entry.get("index") == index), None)

            if existing_entry:
                existing_entry.update(task_data)
            else:
                task_data["index"] = index
                task_data["task_id"] = task_id
                result[task_id].append(task_data)

        overall_data_saved = False

        for task_id, products in result.items():
            task_mapping = TaskMapping.objects.get(id=task_id)
            data_saved = False

            for product in products:
                item_code = product.get("item_code")
                task_name = product.get("task_name")
                std_cost = product.get("standardCost")
                local_cost = product.get("local_cost")
                labor_task = product.get("task_name")
                labor_description = product.get("labor_description")
                item_description = product.get("description")

                if not item_code and not task_name:
                    print("No item code or task name found, skipping...")
                    continue

                if item_code:

                    if not std_cost:
                        return {"status": "warning", "message": "Please add standard cost"}

                    try:
                        vendor = Vendor.objects.get(id=product.get("vendor"))
                    except Exception:
                        vendor = None

                    try:
                        product_obj = Product.objects.get(id=item_code)
                        product_item_code = product_obj.internal_id
                    except Exception:
                        product_item_code = item_code

                    try:
                        product_obj = Product.objects.get(id=item_description)
                        description = product_obj.description
                    except Exception:
                        description = item_description

                    # Save data
                    AssignedProduct.objects.create(
                        task_mapping=task_mapping,
                        quantity=float(product.get("quantity", 0)),
                        item_code=product_item_code,
                        description=description,
                        standard_cost=float(product.get("standardCost", 0)),
                        vendor_quoted_cost=float(product.get("quotedCost", 0)),
                        vendor=vendor,
                        comment=product.get("comment", ""),
                    )
                    data_saved = True

                elif task_name:

                    if not local_cost:
                        return {"status": "warning", "message": "Please add local cost"}

                    try:
                        labor_obj = LabourCost.objects.get(id=task_name)
                        task_name_value = labor_obj.labour_task
                    except Exception:
                        task_name_value = labor_task

                    try:
                        labor_obj = LabourCost.objects.get(id=labor_description)
                        task_description = labor_obj.description
                    except Exception:
                        task_description = labor_description

                    # Save data
                    AssignedProduct.objects.create(
                        task_mapping=task_mapping,
                        quantity=float(product.get("quantity", 0)),
                        description=task_description,
                        labor_task=task_name_value if task_name_value else "",
                        local_cost=product.get("local_cost", 0),
                        out_of_town_cost=product.get("out_of_town_cost", 0),
                        comment=product.get("comment", ""),
                    )
                    data_saved = True

            if data_saved:
                overall_data_saved = True

        if overall_data_saved:
            return {"status": "success", "message": "Product added successfully"}
        else:
            return {"status": "empty", "message": ""}

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            if data == {}:
                return JsonResponse({"status": "empty", "message": "Please enter data"})
            response = self.format_data(data)
            if response["status"] == "success":
                messages.success(self.request, response["message"])
            elif response["status"] == "warning":
                messages.warning(self.request, response["message"])
            elif response["status"] == "error":
                messages.error(self.request, response["message"])
            return JsonResponse(response)
        except json.JSONDecodeError:
            messages.error(self.request, "Something went wrong please try again")
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)


class DeleteAssignProdLabor(View):
    """
    View for delete the assigned product objects.
    """

    def post(self, request):
        assigned_prod_id = request.POST.get("id")
        AssignedProduct.objects.filter(id=assigned_prod_id).delete()
        return JsonResponse({"message": "Deleted Successfully.", "code": 200, "status": "success"})


class AddTaskView(CreateView):
    """
    Add manual task on task mapping.
    """

    template_name = "proposal/opportunity/add_tasks.html"
    form_class = AddTaskForm

    def form_valid(self, form):
        # Get opportunity instance
        document_number = self.kwargs["document_number"]
        opportunity = Opportunity.objects.get(document_number=document_number)

        # Get form data
        code = form.cleaned_data["code"]
        description = form.cleaned_data["description"]

        if code and description:
            TaskMapping.objects.create(opportunity=opportunity, code=code, description=description)
            messages.success(self.request, f'Task "{code} - {description}" added successfully!')
        return JsonResponse({"status": "success", "code": "200"})

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["document_number"] = self.kwargs["document_number"]
        return context


# ==================================                     ===============================
# ================================== Generate Estimation ===============================
# ==================================                     ===============================
class GenerateEstimateTable(ProposalViewMixin):
    """
    View class for rendering the estimate generation.
    """

    render_template_name = "proposal/generate_estimate_table.html"

    def get_total(self, document_number):
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

        return totals

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs["document_number"]

        task_mapping_object = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(
            task__description__icontains="labor"
        )

        task_mapping_labor_object = TaskMapping.objects.filter(opportunity__document_number=document_number).filter(
            task__description__icontains="labor"
        )

        context["estimation_table"] = task_mapping_object
        context["estimation_table_labor"] = task_mapping_labor_object
        context["total"] = self.get_total(document_number)
        return context


class UpdateEstimationProduct(TemplateView):
    """
    Update the product information of estimation table.
    """

    template_name = "proposal/opportunity/estimation_product_update.html"

    def get_tasks_products_data(self, task_id):
        qs = AssignedProduct.objects.filter(task_mapping__id=task_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = self.kwargs["task_id"]
        task_mapping_obj = TaskMapping.objects.get(id=task_id)
        context["task_mapping"] = task_mapping_obj
        context["prods"] = self.get_tasks_products_data(task_id)
        return context


class UpdateEstimationLabor(TemplateView):
    """
    Update the labor information of estimation table.
    """

    template_name = "proposal/opportunity/estimation_labor_update.html"

    def get_tasks_labor_data(self, task_id):
        qs = AssignedProduct.objects.filter(task_mapping__id=task_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_id = self.kwargs["task_id"]
        context["labors"] = self.get_tasks_labor_data(task_id)
        return context


class UpdateEstimationTable(View):

    def update_data(self, data):
        task_mapping_obj = TaskMapping.objects.get(id=data["task_mapping_id"][0])

        if data:
            if "labor_gp_percent" in data and data["labor_gp_percent"]:
                task_mapping_obj.labor_gp_percent = float(data["labor_gp_percent"][0])
                task_mapping_obj.save()
                return {"status": "success", "message": "Labor GP % Updated successfully"}

            elif "mat_gp_percent" in data and data["mat_gp_percent"]:
                task_mapping_obj.mat_gp_percent = float(data["mat_gp_percent"][0])
                task_mapping_obj.save()
                return {"status": "success", "message": "MAT GP % Updated successfully"}

            elif "s_and_h" in data and data["s_and_h"]:
                task_mapping_obj.s_and_h = float(data["s_and_h"][0])
                task_mapping_obj.save()
                return {"status": "success", "message": "S & H Updated successfully"}

            else:
                response = {"status": "error", "message": "Something went wrong"}

            response = {"status": "error", "message": "Please fill data"}
        return response

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            print("UpdateEstimationTable [DATA] ==>>", data)
            response = self.update_data(data)
            return JsonResponse(response)
        except Exception as e:
            print("ERROR FROM [1770] ==> UpdateEstimationTable", e)
            return JsonResponse({"status": "error", "message": "Something went wrong please try again"}, status=400)


# ==================================                   ===============================
# ================================== Proposal Creation ===============================
# ==================================                   ===============================
class CreateProposalView(View):
    """
    Create proposal view.
    """

    template_name = "proposal/opportunity/stage/proposal_creation/create_proposal_form.html"

    def get(self, request, *args, **kwargs):
        document_number = self.kwargs["document_number"]

        # Fetch task mappings for the given document number
        task_mapping_obj = TaskMapping.objects.filter(opportunity__document_number=document_number)

        # Get the IDs of task mappings that are already in the ProposalCreation for the current opportunity
        existing_task_mapping_ids = ProposalCreation.objects.filter(
            opportunity__document_number=document_number
        ).values_list("task_mapping__id", flat=True)

        # Filter out task mappings that are already in ProposalCreation
        available_task_mapping_obj = task_mapping_obj.exclude(id__in=existing_task_mapping_ids)

        context = {"task_mapping_obj": available_task_mapping_obj, "document_number": document_number}

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        document_number = self.kwargs["document_number"]
        tasks = request.POST.getlist("task")
        grp_name = request.POST.getlist("grp_name")

        if tasks and grp_name:
            try:
                opportunity = Opportunity.objects.get(document_number=document_number)
                for task_id in tasks:
                    task_instance = TaskMapping.objects.get(id=task_id)
                    ProposalCreation.objects.create(
                        opportunity=opportunity, group_name=grp_name[0], task_mapping=task_instance
                    )

                messages.success(self.request, f"Proposal Create successfully!")
                return JsonResponse(
                    {
                        "success_url": reverse("proposal_app:opportunity:opportunity-detail", args=(document_number,)),
                        "modal_to_close": "modelSelectTask",
                    },
                    status=201,
                )

            except Opportunity.DoesNotExist:
                print("Error: Opportunity NOT Found")
                return JsonResponse({"error": "Something went wrong please try again!!"}, status=404)
            except TaskMapping.DoesNotExist:
                print("Error: Task Mapping ID NOT Found")
                return JsonResponse({"error": "Something went wrong please try again!!"}, status=404)

        return JsonResponse({"error": "Tasks and Grp name are required."}, status=400)


class DeleteTaskView(View):
    """
    Delete task mapping objects view.
    """

    def post(self, request):
        task_mapping_id = request.POST.get("id")
        TaskMapping.objects.filter(id=task_mapping_id).delete()
        messages.info(request, "Deleted Successfully")
        return JsonResponse({"message": "Deleted Successfully.", "code": 200, "status": "success"})


class UpdateGroupName(View):
    """
    Update proposal group name
    """

    def post(self, request, *args, **kwargs):
        ids = request.POST.getlist("ids")
        group_name = request.POST.get("group_name")
        document_number = request.POST.get("document")

        id_string = ids[0]
        id_list = [int(id.strip()) for id in id_string.split(",")]

        try:
            proposal_creation_obj = ProposalCreation.objects.filter(
                opportunity__document_number=document_number, id__in=id_list
            )
            proposal_creation_obj.update(group_name=group_name)
            return JsonResponse(
                {
                    "status": "success",
                    "message": "Group name updated successfully",
                },
                status=200,
            )
        except Exception as e:
            print("ERROR: [UpdateGroupName][2003]", e)
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Something went wrong here please try again.",
                },
                status=400,
            )


# ==================================                   ===============================
# ================================== Proposal Preview  ===============================
# ==================================                   ===============================
class AddItemsView(View):
    """
    Add dynamic generated items into assigned product
    """

    def add_items(self, data):
        try:
            saved = False
            for i in data:
                assigned_prod = AssignedProduct.objects.get(
                    id=int(i["itemCode"]),
                )
                assigned_prod.is_select = True
                assigned_prod.save()
                saved = True

            if saved:
                response = {"status": "success", "message": "Item added successfully"}
            else:
                response = {"status": "warning", "message": "No item to add"}
        except Exception as e:
            print("ERROR: [AddItemsView][2035]", e)
            response = {"status": "error", "message": "Something went wrong please try again"}

        return response

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode("utf-8")
            data = json.loads(body_unicode)
            response = self.add_items(data)
            return JsonResponse(response)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)


class AddDescriptionView(View):
    """
    Add dynamically generated description.
    """

    def add_description(self, data):
        try:
            saved = False

            for task_id in data:
                task_mapping_obj = TaskMapping.objects.get(id=task_id)

                # Prepare new descriptions based on incoming data
                new_descriptions = []

                for description_dict in data[task_id]:
                    # print(f'description_dict {type(description_dict)}: {description_dict}')
                    for key, value in description_dict.items():
                        if value:
                            # print("Adding new description:", {key: value})
                            new_descriptions.append({key: value})

                if new_descriptions:
                    # print("task_mapping_obj.extra_description == new_descriptions", task_mapping_obj.extra_description == new_descriptions)
                    # print("task_mapping", task_mapping_obj.extra_description)
                    # print("Updating descriptions...", new_descriptions)
                    if task_mapping_obj.extra_description != new_descriptions:
                        task_mapping_obj.extra_description = new_descriptions
                        task_mapping_obj.save()
                        saved = True
                else:
                    # print("IN elseeeeeeeeeeeeeeeee")
                    task_mapping_obj.extra_description = []
                    task_mapping_obj.save()
                    saved = True

            if saved:
                return {"status": "success", "message": "Description updated successfully"}
            else:
                return {"status": "empty", "message": ""}

        except Exception as e:
            print("Error [AddDescriptionView][add_description]", e)
            return {"status": "error", "message": "Something went wrong, please try again"}

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            response = self.add_description(data)
            return JsonResponse(response)
        except Exception as e:
            print("Error [AddDescriptionView]", e)
            return JsonResponse({"status": "error", "message": "Something went wrong please try again"})


class UpdateItemIncludeView(View):
    """
    Update item include view.
    """

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            id = data.get("id")
            task_mapping_obj = TaskMapping.objects.get(id=id)

            if task_mapping_obj.include:
                task_mapping_obj.include = False
                task_mapping_obj.save()
                return JsonResponse({"status": "success", "message": "Include item update successfully"})
            task_mapping_obj.include = True
            task_mapping_obj.save()
            return JsonResponse({"status": "success", "message": "Include item update successfully"})
        except Exception as e:
            print("ERROR: [UpdateItemIncludeView][2071]", e)
            return JsonResponse({"status": "error", "message": "Something went wrong please try again"})


class UpdateTaskMappingView(View):
    """
    Update task mapping fields view.
    """

    def post(self, request, *args, **kwargs):
        try:

            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)

            try:

                task_mapping_obj = TaskMapping.objects.get(id=data.get("id")[0])

                if data.get("type")[0] == "task_code":
                    task_mapping_obj.code = data.get("value")[0]
                    task_mapping_obj.save()
                    return JsonResponse({"status": "success", "message": "Task code updated successfully"}, status=200)
                elif data.get("type")[0] == "task_description":
                    task_mapping_obj.description = data.get("value")[0]
                    task_mapping_obj.save()
                    return JsonResponse(
                        {"status": "success", "message": "Task description updated successfully"}, status=200
                    )
                elif data.get("type")[0] == "approve":
                    task_mapping_obj.approve = data.get("value")[0]
                    task_mapping_obj.save()
                    return JsonResponse(
                        {"status": "success", "message": "Approve & Initial	updated successfully"}, status=200
                    )

            except Exception as e:
                print("Error: [UpdateTaskMappingView][1]", e)
                return JsonResponse({"status": "error", "message": "Something went wrong please try again"}, status=400)

        except Exception as e:
            print("Error: [UpdateTaskMappingView][2]", e)
            return JsonResponse({"status": "error", "message": "Something went wrong please try again"}, status=400)


class UpdateProposalItemsView(View):
    """
    Update proposal items of task.
    """

    def update_data(self, data):
        try:

            assigned_pro_obj = AssignedProduct.objects.get(id=data.get("id")[0])

            if data.get("input_type")[0] == "prod_item_code":
                assigned_pro_obj.item_code = data.get("value")[0]
                assigned_pro_obj.save()
                response_message = {"status": "success", "message": "Item Code Updated successfully"}
            elif data.get("input_type")[0] == "prod_labor_task":
                assigned_pro_obj.labor_task = data.get("value")[0]
                assigned_pro_obj.save()
                response_message = {"status": "success", "message": "Item Updated successfully"}
            elif data.get("input_type")[0] == "prod_local_cost":
                value = data.get("value")[0]
                assigned_pro_obj.local_cost = float(value.replace("$", "").strip())
                assigned_pro_obj.save()
                response_message = {"status": "success", "message": "Price Updated successfully"}
            elif data.get("input_type")[0] == "prod_description":
                assigned_pro_obj.description = data.get("value")[0]
                assigned_pro_obj.save()
                response_message = {"status": "success", "message": "Description Updated successfully"}
            elif data.get("input_type")[0] == "prod_quantity":
                assigned_pro_obj.quantity = data.get("value")[0]
                assigned_pro_obj.save()
                response_message = {"status": "success", "message": "Quantity Updated successfully"}
            elif data.get("input_type")[0] == "prod_cost":
                value = data.get("value")[0]
                assigned_pro_obj.standard_cost = float(value.replace("$", "").strip())
                assigned_pro_obj.save()
                response_message = {"status": "success", "message": "Price Updated successfully"}

            return response_message

        except Exception as e:
            print("Error [UpdateProposalItemsView][update_data]", e)
            return {"status": "error", "message": "Something went wrong please try again"}

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            response = self.update_data(data)
            return JsonResponse(response)
        except Exception as e:
            print("Error: [UpdateProposalItemsView][2]", e)
            return JsonResponse({"status": "error", "message": "Something went wrong please try again"}, status=400)


class UpdateInvoiceView(View):
    """
    Update Invoice view
    """

    def update_data(self, data):
        try:
            invoice_obj = Invoice.objects.get(id=data["id"][0])
            if data["type"][0] == "invoice_number":
                invoice_obj.invoice_number = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Invoice Number Updated successfully"}
            elif data["type"][0] == "invoice_date":
                invoice_obj.invoice_data = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Invoice Date Updated successfully"}
            elif data["type"][0] == "deposit":
                invoice_obj.deposit_amount = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Deposit Updated successfully"}
            elif data["type"][0] == "address":
                invoice_obj.billing_address = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Address Updated successfully"}
            elif data["type"][0] == "other_tax":
                invoice_obj.other_tax = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Other Tax Updated successfully"}
            elif data["type"][0] == "tax_rate":
                invoice_obj.tax_rate = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Tax Rate Updated successfully"}
            elif data["type"][0] == "sales_tax":
                invoice_obj.sales_tax = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Sales Tax Updated successfully"}
            elif data["type"][0] == "to-address":
                invoice_obj.deposit_address = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Address Updated successfully"}
            elif data["type"][0] == "buyer":
                invoice_obj.buyer = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Buyer Updated successfully"}
            elif data["type"][0] == "buyer-date":
                invoice_obj.buyer_date = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Buyer Date Updated successfully"}
            elif data["type"][0] == "buyer-name":
                invoice_obj.buyer_name = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Buyer Name Updated successfully"}
            elif data["type"][0] == "buyer-position":
                invoice_obj.buyer_position = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Buyer Position Updated successfully"}
            elif data["type"][0] == "seller":
                invoice_obj.seller = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Seller Updated successfully"}
            elif data["type"][0] == "seller-date":
                invoice_obj.seller_date = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Seller Date Updated successfully"}
            elif data["type"][0] == "seller-name":
                invoice_obj.seller_name = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Seller Name Updated successfully"}
            elif data["type"][0] == "seller-position":
                invoice_obj.seller_position = data["value"][0]
                invoice_obj.save()
                response_message = {"status": "success", "message": "Seller Position Updated successfully"}
            return response_message
        except Exception as e:
            print("Error [UpdateInvoiceView][update_data]", e)
            return {"status": "error", "message": "Something went wrong please try again"}

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            response = self.update_data(data)
            return JsonResponse(response)
        except Exception as e:
            print("Error [UpdateInvoiceView]", e)
            return JsonResponse({"status": "error", "message": "Something went wrong please try again"}, status=400)


# ==================================                     ===============================
# ================================== Generate Estimation ===============================
# ==================================                     ===============================
# --Breakdown Estimation
class TotalCostBreakdown(TemplateView):
    """
    Total cost breakdown
    """

    template_name = "proposal/opportunity/total_cost_breakdown.html"

    def get_total(self, document_number):
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)
        totals = {
            "total_labor_cost": Decimal("0.00"),
            "total_mat_cost": Decimal("0.00"),
        }

        for task in task_mapping_qs:
            totals["total_labor_cost"] += round(Decimal(task.labor_cost or "0.0"), 2)
            totals["total_mat_cost"] += round(Decimal(task.mat_cost or "0.0"), 2)

        totals["total_cost"] = totals["total_labor_cost"] + totals["total_mat_cost"]

        return totals

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs["document_number"]
        context["total"] = self.get_total(document_number)
        return context


class TotalSaleBreakdown(TemplateView):
    """
    Total Sales breakdown
    """

    template_name = "proposal/opportunity/total_sale_breakdown.html"

    def get_total(self, document_number):
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)
        totals = {
            "total_labor_sale": Decimal("0.00"),
            "total_mat_sale": Decimal("0.00"),
        }

        for task in task_mapping_qs:

            totals["total_labor_sale"] += round(Decimal(task.labor_sell or "0.0"), 2)
            totals["total_mat_sale"] += round(Decimal(task.mat_sell or "0.0"), 2)

        totals["total_sale"] = totals["total_labor_sale"] + totals["total_mat_sale"]
        return totals

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs["document_number"]
        context["total"] = self.get_total(document_number)
        return context


class TotalGPBreakdown(TemplateView):
    """
    Total GP breakdown
    """

    template_name = "proposal/opportunity/total_gp_breakdown.html"

    def get_total(self, document_number):
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)
        totals = {
            "total_labor_gp": Decimal("0.00"),
            "total_mat_gp": Decimal("0.00"),
        }

        for task in task_mapping_qs:

            totals["total_labor_gp"] += round(Decimal(task.labor_gp or "0.0"), 2)
            totals["total_mat_gp"] += round(Decimal(task.mat_gp or "0.0"), 2)

        totals["total_gp"] = totals["total_labor_gp"] + totals["total_mat_gp"]
        return totals

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs["document_number"]
        context["total"] = self.get_total(document_number)
        return context


class TotalGPPerBreakdown(TemplateView):
    """
    Total GP % breakdown
    """

    template_name = "proposal/opportunity/total_gp_per_breakdown.html"

    def get_total(self, document_number):
        task_mapping_qs = TaskMapping.objects.filter(opportunity__document_number=document_number)
        totals = {
            "total_labor_gp_percent": Decimal("0.00"),
            "total_mat_gp_percent": Decimal("0.00"),
            "total_comb_gp": Decimal("0.00"),
        }

        for task in task_mapping_qs:

            totals["total_labor_gp_percent"] += round(Decimal(task.labor_gp_percent or "0.0"), 2)
            totals["total_mat_gp_percent"] += round(Decimal(task.mat_gp_percent or "0.0"), 2)
            totals["total_comb_gp"] += round(Decimal(task.comb_gp or "0.0"), 2)

        totals["total_gp_percent"] = (
            totals["total_labor_gp_percent"] + totals["total_mat_gp_percent"] + totals["total_comb_gp"]
        )
        return totals

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs["document_number"]
        context["total"] = self.get_total(document_number)
        return context


# ==================================              ===============================
# ================================== Search Views ===============================
# ==================================              ===============================
# --Search Views
class ItemCodeSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get("q", "")
        item_codes = Product.objects.filter(internal_id__icontains=search_term)[:15]
        item_code_list = [{"id": item_code.id, "text": item_code.internal_id} for item_code in item_codes]
        return JsonResponse({"results": item_code_list})

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode("utf-8")
        data = urllib.parse.parse_qs(body_unicode)
        id = data["value"][0]
        product_object = Product.objects.get(id=id)

        return JsonResponse(
            {
                "code": 200,
                "message": "success",
                "description": product_object.description,
                "std_cost": product_object.std_cost,
            }
        )


class ItemDescriptionSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get("q", "")
        item_descriptions = Product.objects.filter(description__icontains=search_term)[:15]
        item_description_list = [
            {"id": item_description.id, "text": item_description.description} for item_description in item_descriptions
        ]
        return JsonResponse({"results": item_description_list})


class VendorSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get("q", "")
        vendors = Vendor.objects.filter(name__icontains=search_term)[:15]  # Limit results to 15
        vendor_list = [{"id": vendor.id, "text": vendor.name} for vendor in vendors]
        return JsonResponse({"results": vendor_list})


class CustomerSearchView(View):
    """
    Customer Search View
    """

    def get(self, request, *args, **kwargs):
        search_term = request.GET.get("q", "")
        customers = Customer.objects.filter(name__icontains=search_term)[:15]
        customer_list = [{"id": customer.id, "text": customer.name} for customer in customers]
        return JsonResponse({"results": customer_list})

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)

            try:
                # Save customer into opportunity
                customer_obj = Customer.objects.get(id=data.get("value")[0])
                opportunity_obj = Opportunity.objects.get(document_number=data.get("document_number")[0])
                opportunity_obj.customer = customer_obj
                opportunity_obj.save()
                messages.success(request, "Customer Added successfully")
                return JsonResponse({"code": 200, "status": "success", "message": "Customer Added successfully"})
            except Exception as e:
                print("Error", e)
                messages.error(request, "Something went wrong while adding customer, please try again!!")
                return JsonResponse(
                    {
                        "code": 400,
                        "status": "error",
                        "message": "Something went wrong while adding customer, please try again!!",
                    }
                )

        except Exception as e:
            print("ERROR: [CustomerSearchView][2304]", e)
            return JsonResponse(
                {
                    "code": 400,
                    "status": "error",
                    "message": "Something went wrong while adding customer, please try again after some time!!",
                }
            )


class TaskSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get("q", "")
        document_number = request.GET.get("document_number", None)

        mapped_task_ids = TaskMapping.objects.filter(
            opportunity__document_number=document_number, task_id__isnull=False
        ).values_list("task_id", flat=True)

        tasks = (
            Task.objects.filter(name__icontains=search_term)
            .exclude(id__in=mapped_task_ids)
            .exclude(description__icontains="labor")[:15]
        )  # Limit results to 15

        task_list = [{"id": task.id, "text": task.name} for task in tasks]
        return JsonResponse({"results": task_list})


class LaborTaskSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get("q", "")
        tasks = Task.objects.filter(name__icontains=search_term).filter(description__icontains="labor")[
            :15
        ]  # Limit results to 15
        task_list = [{"id": task.id, "text": task.name} for task in tasks]
        return JsonResponse({"results": task_list})


class LaborDescriptionView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get("q", "")
        descriptions = LabourCost.objects.filter(description__icontains=search_term)[:15]
        description_list = [{"id": description.id, "text": description.description} for description in descriptions]
        return JsonResponse({"results": description_list})


class LaborTaskNameView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get("q", "")
        labors = LabourCost.objects.filter(labour_task__icontains=search_term)[:15]
        labor_list = [{"id": labor.id, "text": labor.labour_task} for labor in labors]
        return JsonResponse({"results": labor_list})

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode("utf-8")
        data = urllib.parse.parse_qs(body_unicode)
        id = data["value"][0]

        labor_obj = LabourCost.objects.get(id=id)

        return JsonResponse(
            {
                "code": 200,
                "message": "success",
                "description": labor_obj.description,
                "local_labor_rates": labor_obj.local_labour_rates,
                "out_of_town_labour_rates": labor_obj.out_of_town_labour_rates,
            }
        )


class TaskItemView(View):
    """
    Task Item code search view.
    """

    def get(self, request, *args, **kwargs):
        search_term = request.GET.get("q", "")
        task_id = kwargs["task_id"]
        # print("task_id", task_id)
        task_item = AssignedProduct.objects.filter(task_mapping__id=task_id, item_code__icontains=search_term).exclude(
            is_select=True
        )[:15]
        task_item_list = [{"id": t.id, "text": t.item_code} for t in task_item]
        return JsonResponse({"results": task_item_list})

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode("utf-8")
        data = urllib.parse.parse_qs(body_unicode)
        id = data["value"][0]
        assigned_prod = AssignedProduct.objects.get(id=id)
        return JsonResponse(
            {
                "code": 200,
                "message": "success",
                "description": assigned_prod.description,
                "quantity": assigned_prod.quantity,
                "price": (
                    assigned_prod.standard_cost if assigned_prod.standard_cost else assigned_prod.vendor_quoted_cost
                ),
            }
        )
