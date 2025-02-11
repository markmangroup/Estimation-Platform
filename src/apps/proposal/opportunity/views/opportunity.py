import datetime
import json
import urllib.parse
from typing import Any, Dict

from django.contrib import messages
from django.db.models import Q, QuerySet
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.utils.dateparse import parse_date

from apps.constants import ERROR_RESPONSE, LOGGER
from apps.mixin import (
    CustomDataTableMixin,
    FormViewMixin,
    ProposalDetailViewMixin,
    ProposalViewMixin,
    TemplateViewMixin,
    ViewMixin,
)

from ..forms import ImportOpportunityCSVForm
from ..models import Document, Invoice, Opportunity
from ..tasks import import_opportunity_from_xlsx
from .final_document import FinalDocument
from .generate_estimate import GenerateEstimate
from .proposal_creation import ProposalCreationData
from .task_mapping import TaskMappingData

# Opportunity View Start


class SearchView(ViewMixin):
    """
    View to search opportunities by document number.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Search for document numbers based on a query.

        :param request: The HTTP request object containing query parameters.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JsonResponse: JSON response with a list of matching `document_number` values.
        """

        query = request.GET.get("query", "").strip()
        results = []

        if len(query) > 3:
            results = Opportunity.objects.filter(document_number__icontains=query).values("document_number")[:5]

        return JsonResponse({"results": list(results)})


class OpportunityList(ProposalViewMixin):
    """
    View to display a list of Opportunities.
    """

    render_template_name = "proposal/opportunity/opportunity_list.html"


class OpportunityDocumentView(TemplateViewMixin):
    """
    View for displaying an opportunity document.
    """

    template_name = "proposal/opportunity/opportunity_document.html"

    def _get_opportunity_document(self, document_number: str) -> QuerySet:
        """
        Retrieve documents associated with the given opportunity document number.

        :prams document_number: For get opportunity by document number.
        :returns: A list of documents associated with the given opportunity document.
        """
        return Document.objects.filter(opportunity__document_number=document_number)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add document number and opportunity documents to the context."""
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        opportunity_obj = Opportunity.objects.filter(document_number=document_number).first()
        context["opportunity"] = opportunity_obj
        context["opportunity_document"] = self._get_opportunity_document(document_number)

        # Final Document
        context["new_material_master_data"] = FinalDocument._get_new_material_master_data(document_number)
        context["cost_variances_data"] = FinalDocument._get_cost_variances_data(document_number)
        context["netsuite_extract_data"] = FinalDocument._get_netsuite_extract_data(document_number)

        return context


class OpportunityListAjaxView(CustomDataTableMixin):
    """
    JSON DataTable view for Opportunities.
    """

    model = Opportunity

    def get_queryset(self):
        """
        Return list of opportunities.
        """
        return Opportunity.objects.all()

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

            if column_name:
                if values:
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


class OpportunityCreateFromCSVFormView(FormViewMixin):
    """
    View for importing Opportunities from a CSV or Excel file.
    """

    template_name = "proposal/opportunity/import_opportunity.html"
    form_class = ImportOpportunityCSVForm

    def form_valid(self, form):
        """
        Process the uploaded file and provide feedback.

        :param form: The submitted form containing the file data.
        :return: JSON response with success message or rendered form with errors.
        """
        csv_file = form.cleaned_data["csv_file"]
        response = import_opportunity_from_xlsx(csv_file)

        if response.get("error"):
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        return JsonResponse(
            {
                "redirect": reverse("proposal_app:opportunity:opportunity-list"),
                "message": "Opportunity Import Successful!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """
        Render the form with errors.

        :param form: The submitted form containing validation errors.
        :return: Rendered form with error messages.
        """
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

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Returns a dictionary od the context object.
        """
        context = super().get_context_data(**kwargs)

        document_number = self.kwargs.get("document_number")

        opportunity = Opportunity.objects.get(document_number=document_number)
        invoice = Invoice.objects.get(opportunity=opportunity)

        # Opportunity
        context["invoice"] = invoice
        context["stage"] = opportunity.estimation_stage

        # Task Mapping
        context["total_tasks"] = TaskMappingData._get_total_tasks(document_number)
        context["task_mapping_list"] = TaskMappingData._get_tasks(document_number)
        context["task_mapping_labor_list"] = TaskMappingData._get_labour_tasks(document_number)
        context["grand_total"] = TaskMappingData._get_task_total(document_number)
        context["labor_task_total"] = TaskMappingData._get_labor_task_total(document_number)

        # Generate Estimation
        context["task_product_list"] = GenerateEstimate._get_task_products(document_number)
        context["task_labor_list"] = GenerateEstimate._get_task_labor(document_number)
        context["total"] = GenerateEstimate._get_total(document_number)

        # Proposal creation
        context["grouped_proposals"] = ProposalCreationData._get_proposal_creation(document_number)
        context["proposal_total"] = ProposalCreationData._get_proposal_totals(document_number)

        # Final Document
        context["new_material_master_data"] = FinalDocument._get_new_material_master_data(document_number)
        context["cost_variances_data"] = FinalDocument._get_cost_variances_data(document_number)
        context["netsuite_extract_data"] = FinalDocument._get_netsuite_extract_data(document_number)
        return context


class UpdateOpportunityView(ViewMixin):
    """
    View to update opportunity fields.
    """

    def _update_field(self, opportunity_obj: Opportunity, field_name: str, value: str) -> dict:
        """
        Update a specified field of the opportunity.

        :param opportunity_obj: Opportunity instance to update.
        :param field_name: Name of the field to update.
        :param value: New value for the field.
        :returns: updated field success message
        """
        setattr(opportunity_obj, field_name, value)
        opportunity_obj.save()
        return {
            "status": "success",
            "message": f"{field_name.replace('_', ' ').capitalize()} updated successfully",
        }

    def _update_data(self, data: dict) -> dict:
        """
        Update opportunity fields based on incoming data.

        :param data: Parsed request data containing field information.
        :return: Response message indicating success or error.
        """
        try:
            opportunity_obj = Opportunity.objects.get(document_number=data["document_number"][0])
            field_mapping = {
                "job": "job",
                "job_name": "job_name",
                "project": "project",
                "ranch": "ranch_name",
                "tax_rate" : "tax_rate",
            }

            field_type = data["type"][0]
            if field_type in field_mapping:
                print(data["value"][0])
                return self._update_field(opportunity_obj, field_mapping[field_type], data["value"][0])

            if field_type == "term_and_condition":
                json_data = json.loads(data["value"][0])
                if opportunity_obj.term_and_condition != json_data:
                    opportunity_obj.term_and_condition = json_data
                    opportunity_obj.save()
                    messages.success(self.request, "Terms updated successfully")
                    return {
                        "status": "success",
                        "message": "Terms updated successfully",
                    }
                return {}  # Return empty response

            return ERROR_RESPONSE

        except Opportunity.DoesNotExist:
            LOGGER.error("Error: Opportunity Not Found")
            return ERROR_RESPONSE
        except Exception as e:
            LOGGER.error(f"Error [UpdateOpportunity][update_date] {e}")
            return ERROR_RESPONSE

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to update opportunity data.

        :param request: HTTP request object.
        :return: JsonResponse indicating success or error.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            response = self._update_data(data)
            return JsonResponse(response)

        except Exception as e:
            LOGGER.error(f"Error [UpdateOpportunity] {e}")
            return JsonResponse(ERROR_RESPONSE, status=400)


class UpdateStages(ViewMixin):
    """
    Update Opportunity Stages.
    """

    def post(self, request) -> JsonResponse:
        """
        Handle POST requests to update the opportunity stage.

        :param request: The HTTP request object containing the JSON body.
        :return: JsonResponse indicating success or failure of the operation.
        """
        data = self._parse_request_body(request)
        if isinstance(data, JsonResponse):
            return data  # Return error response if JSON parsing failed

        document_number = data.get("document_number")
        updated_stage = data.get("stage")

        if not document_number or not updated_stage:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        opportunity = get_object_or_404(Opportunity, document_number=document_number)
        return self._update_stage(opportunity, updated_stage)

    def _parse_request_body(self, request) -> JsonResponse:
        """
        Parse the JSON request body.

        :param request: The HTTP request object.
        :return: Parsed JSON data as a dictionary or JsonResponse with error.
        """
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            LOGGER.error("Error: Invalid JSON")
            return JsonResponse(ERROR_RESPONSE, status=400)

    def _update_stage(self, opportunity: Opportunity, updated_stage: str) -> JsonResponse:
        """
        Update the opportunity stage if the new stage is valid.

        :param opportunity: The Opportunity instance to be updated.
        :param updated_stage: The new stage to set for the opportunity.
        :return: JsonResponse indicating success or failure of the operation.
        """
        current_stage = opportunity.get_current_stage_constant()
        estimation_stage = getattr(Opportunity, updated_stage, None)

        if estimation_stage is None:
            return JsonResponse({"error": "Invalid stage"}, status=400)

        if current_stage < updated_stage:
            opportunity.estimation_stage = estimation_stage
            opportunity.updated_at = datetime.datetime.now()
            opportunity.save()
            return JsonResponse({"message": "Opportunity stage updated successfully"}, status=200)
        else:
            return JsonResponse({"message": "Opportunity stage lower than current stage"}, status=200)


class OpportunityFilterView(ViewMixin):
    """
    View to filter opportunities based on specified columns.
    """

    column_mapping = {
        "Document Number": "document_number",
        "Designer": "designer",
        "Estimator": "estimator",
        "Pump Electrical Designer": "pump_electrical_designer",
        "Design Estimation Note": "design_estimation_note",
        "Estimation Stage": "estimation_stage",
        "Updated At": "updated_at",
    }

    def get(self, request, column: str) -> JsonResponse:
        """
        Handle GET requests to filter opportunities by the specified column.

        :param request: The HTTP request object.
        :param column: The column name to filter by.
        :return: JSON response containing the filtered options or an error message.
        """
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