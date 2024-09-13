import csv
import datetime
import json
from collections import defaultdict
from io import StringIO
import urllib.parse

import pandas as pd
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.generic import CreateView, FormView, TemplateView, View
from django_datatables_too.mixins import DataTableMixin

from apps.proposal.product.models import Product
from apps.proposal.labour_cost.models import LabourCost
from apps.proposal.task.models import Task
from apps.proposal.vendor.models import Vendor
from apps.rental.mixin import ProposalDetailViewMixin, ProposalViewMixin

from .forms import AddTaskForm, ImportOpportunityCSVForm, UploadDocumentForm
from .models import (
    AssignedProduct,
    Document,
    GlueAndAdditionalMaterial,
    MaterialList,
    Opportunity,
    PreliminaryMaterialList,
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
                    print("values: ", values)
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
            tasks_with_products[task.id] = {
                "task": task,
                "assigned_products": assigned_products.filter(task_mapping_id=task.id),
            }

        return tasks_with_products

    def _get_labour_tasks(self, document_number):
        task = TaskMapping.objects.filter(opportunity__document_number=document_number)
        qs = task.filter(task__description__icontains="labor")
        return qs

    def get_context_data(self, **kwargs):
        """
        Returns a dictionary od the context object.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        opportunity = Opportunity.objects.get(document_number=document_number)
        context["stage"] = opportunity.estimation_stage
        context["task_mapping_list"] = self._get_tasks(document_number)
        context["task_mapping_labor_list"] = self._get_labour_tasks(document_number)
        return context


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
                Q(task__internal_id_icontains=self.search)
                | Q(task__name_icontains=self.search)
                | Q(task__description_icontains=self.search)
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

    template_name = "proposal/opportunity/select_task_code_model.html"

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
        from django.shortcuts import render

        return render(self.request, self.template_name, context, **response_kwargs)


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
            return f"<div class='text-center'><a href='{obj.document.url}' download><i class='icon-cloud-download'></i> File</a></div>"
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
        print("stage: ", stage)
        opportunity_object = Opportunity.objects.get(document_number=document_number)
        form.instance.opportunity = opportunity_object
        form.instance.stage = stage
        form.instance.comment = comment
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors:
            print("Error ==>> :", error)
        return super().form_invalid(form)

    def get_success_url(self):
        document_number = self.request.POST.get("document_number")
        print(f"document_number {type(document_number)}: {document_number}")
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
            print(f"updated_stage : {updated_stage}")

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
        print("options: ", options)
        return JsonResponse({"options": options})


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

        if uploaded_file.name.endswith(".Tmp"):

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
                Q(quantity_icontains=self.search)
                | Q(description_icontains=self.search)
                | Q(item_number_icontains=self.search)
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
                Q(quantity_icontains=self.search)
                | Q(description_icontains=self.search)
                | Q(item_number_icontains=self.search)
                | Q(category_icontains=self.search)
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
                Q(irricad_imported_quantities_icontains=self.search)
                | Q(glue_and_additional_mat_quantities_icontains=self.search)
                | Q(combined_quantities_from_both_import_icontains=self.search)
                | Q(description_icontains=self.search)
                | Q(item_number_icontains=self.search)
                | Q(category_icontains=self.search)
                | Q(bag_bundle_quantity_icontains=self.search)
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


class AssignProdLabor(TemplateView):
    """
    Import data from CSV or Excel files.
    """

    template_name = "proposal/opportunity/assign_prod_labor.html"

    def _get_products_data(self, task_mapping_id, document_number):
        all_products = PreliminaryMaterialList.objects.filter(opportunity__document_number=document_number)
        print("All Products =>>", all_products)

        assigned_item_codes = AssignedProduct.objects.filter(task_mapping__id=task_mapping_id).values_list(
            "item_code", flat=True
        )
        print("Assigned product ==>", assigned_item_codes)

        try:
            assigned_product_ids = [int(code) for code in assigned_item_codes]
        except ValueError:
            assigned_product_ids = []
        print("Assigned product ID's ==>", assigned_product_ids)

        available_products = all_products.exclude(item_number__in=assigned_product_ids)
        return available_products

    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get("items", "[]"))
        print("data ==>", data)
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
                prod_obj = PreliminaryMaterialList.objects.get(opportunity__document_number=document_number,item_number=i["internal_id"])

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
        input_type = data.get('type', [''])[0]
        id = data.get('id', [''])[0]
        value = data.get('value', [''])[0]
        print("value", value)

        try:
            assigned_prod = AssignedProduct.objects.get(id=id)
        except:
            task_mapping = TaskMapping.objects.get(id=id)

        if input_type == 'quantity':
            
            assigned_prod.quantity = value
            assigned_prod.save()

            response_data = {
                'status': 'success',
                'message': f'Quantity updated successfully'
            }
        elif input_type == 'vendor-quoted-cost':
            
            assigned_prod.vendor_quoted_cost = value
            assigned_prod.save()

            response_data = {
                'status': 'success',
                'message': f'Vendor quoted updated successfully'
            }
        elif input_type == 'comment':

            assigned_prod.comment = value
            assigned_prod.save()

            response_data = {
                'status': 'success',
                'message': f'Comment updated successfully'
            }

        elif input_type == 'vendor':
            
            vendor_value = Vendor.objects.get(id=value)
            assigned_prod.vendor = vendor_value.name
            assigned_prod.save()
            
            response_data = {
                'status': 'success',
                'message': f'Vendor updated successfully'
            }
        
        elif input_type == 'task':
            
            task = Task.objects.get(id=value)
            task_mapping.task = task
            task_mapping.save()

            response_data = {
                'status': 'success',
                'message': f'Task updated successfully'
            }
        
        elif input_type == 'labor-task':
            
            task = Task.objects.get(id=value)
            task_mapping.task = task
            task_mapping.save()

            response_data = {
                'status': 'success',
                'message': f'Labor Task updated successfully'
            }

        else:
            response_data = {
                'status': 'error',
                'message': 'Invalid type'
            }
        
        return response_data

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode('utf-8')
            data = urllib.parse.parse_qs(body_unicode)
            _response = self.update_fields(data)
            return JsonResponse(_response)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        

class AddProdRowView(View):
    """
    Add row product data
    """

    def format_data(self, input_data):
        # Initialize an empty dictionary to store the result
        result = {}

        # Iterate over the keys in the input data
        for key, value in input_data.items():
            # Extract the field name from the key
            parts = key.split('][')
            field_name = parts[1].split(']')[0]

            # Extract index and task_id
            index = parts[0].split('[')[-1]
            task_id = input_data.get(f'rows[{index}][task_id]', [None])[0]

            if task_id not in result:
                result[task_id] = []

            # Prepare the task data entry
            task_data = {field_name: value[0]}
            
            # Check if there's already an entry for this index
            existing_entry = next((entry for entry in result[task_id] if entry.get('index') == index), None)
            
            if existing_entry:
                existing_entry.update(task_data)
            else:
                task_data['index'] = index
                task_data['task_id'] = task_id
                result[task_id].append(task_data)
        
        for task_id, products in result.items():
            # print("task_id: ", task_id)
            # print("products:", products)
            try:
                task_mapping = TaskMapping.objects.get(id=task_id)
            except TaskMapping.DoesNotExist:
                print(f"TaskMapping with ID {task_id} does not exist.")
                return {"status": "error", "message": "Something went wrong please try again after some time."}

            for product in products:
                
                try:
                    product_obj = Product.objects.get(id=product.get('item_code', ''))
                    item_code = product_obj.internal_id
                    description = product_obj.description 
                except:
                    item_code = product.get('item_code', '')
                    description = product.get('description', '')

                vendor = Vendor.objects.get(id=product.get('vendor', ''))

                AssignedProduct.objects.create(
                    task_mapping=task_mapping,
                    quantity=float(product.get('quantity', 0)),
                    item_code=item_code,
                    description=description,
                    standard_cost=float(product.get('standardCost', 0)),
                    vendor_quoted_cost=float(product.get('quotedCost', None)),
                    vendor=vendor,
                    comment=product.get('comment', '')
                )

        return {"status": "success", "message": "Product added successfully"}

    def post(self, request, *args, **kwargs):
        try:
            body_unicode = request.body.decode('utf-8')
            data = urllib.parse.parse_qs(body_unicode)
            print("Data -=-==-=-=-=", data)
            response = self.format_data(data)
            # response = self.generate_prod_rows(data)
            return JsonResponse(response)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)


class DeleteAssignProdLabor(View):
    """
    View for delete the assigned product objects.
    """

    def post(self, request):
        assigned_prod_id = request.POST.get("id")
        AssignedProduct.objects.filter(id=assigned_prod_id).delete()
        return JsonResponse({"message": "Product Deleted Successfully.", "code": 200, "status": "success"})


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


class GenerateEstimateTable(ProposalViewMixin):
    """
    View class for rendering the estimate generation.
    """

    render_template_name = "proposal/generate_estimate_table.html"


# --Search Views
class ItemCodeSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', '')
        item_codes = Product.objects.filter(internal_id__icontains=search_term)[:15]
        item_code_list = [{'id': item_code.id, 'text': item_code.internal_id} for item_code in item_codes]
        return JsonResponse({'results': item_code_list})

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        data = urllib.parse.parse_qs(body_unicode)
        id =  data["value"][0]
        product_object = Product.objects.get(id=id)
        print("description", product_object.description)
        print("STD cost", product_object.std_cost)

        return JsonResponse(
            {
                "code": 200,
                "message": "success",
                "description":  product_object.description,
                "std_cost": product_object.std_cost,
            }
        )


class ItemDescriptionSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', '')
        item_descriptions = Product.objects.filter(description__icontains=search_term)[:15]
        item_description_list = [{'id': item_description.id, 'text': item_description.description} for item_description in item_descriptions]
        return JsonResponse({'results': item_description_list})


class VendorSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', '')
        vendors = Vendor.objects.filter(name__icontains=search_term)[:15]  # Limit results to 15
        vendor_list = [{'id': vendor.id, 'text': vendor.name} for vendor in vendors]
        return JsonResponse({'results': vendor_list})


class TaskSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', '')
        document_number = request.GET.get('document_number', None)

        mapped_task_ids = TaskMapping.objects.filter(
            opportunity__document_number=document_number,
            task_id__isnull=False
            ).values_list('task_id', flat=True)
        
        tasks = Task.objects.filter(
            name__icontains=search_term
        ).exclude(
            id__in=mapped_task_ids 
        ).exclude(
            description__icontains="labor"
        )[:15]  # Limit results to 15

        task_list = [{'id': task.id, 'text': task.name} for task in tasks]
        return JsonResponse({'results': task_list})


class LaborTaskSearchView(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', '')
        tasks = Task.objects.filter(
            name__icontains=search_term
        ).filter(
            description__icontains="labor"
        )[:15]  # Limit results to 15
        task_list = [{'id': task.id, 'text': task.name} for task in tasks]
        return JsonResponse({'results': task_list})


class LaborDescription(View):
    def get(self, request, *args, **kwargs):
        search_term = request.GET.get('q', '')
        descriptions = LabourCost.objects.filter(
            description__icontains=search_term
        )[:15]
        description_list = [{'id': description.id, 'text': description.description} for description in descriptions]
        return JsonResponse({'results': description_list})