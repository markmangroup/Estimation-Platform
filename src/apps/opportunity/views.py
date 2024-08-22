import datetime
import json

from django.db.models import Q
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.views.generic import CreateView, FormView, View
from django_datatables_too.mixins import DataTableMixin

from apps.proposal.mixin import ProposalDetailViewMixin, ProposalViewMixin
from apps.task.models import Task

from .forms import ImportOpportunityCSVForm, UploadDocumentForm
from .models import Document, Opportunity, SelectTaskCode
from .tasks import import_opportunity_from_xlsx


class OpportunityList(ProposalViewMixin):
    """
    View to display a list of Opportunities.
    Renders the template for the Opportunity list page.
    """

    render_template_name = "opportunity/opportunity_list.html"


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
            "opportunity:opportunity-detail",
            kwargs={"document_number": obj.document_number},
        )
        return f'<a href="{edit_url}">{obj.document_number}</a>'

    def _get_estimation_stage(self, obj):
        """
        Render the estimation stages for the Opportunity using a partial template.
        """
        t = get_template("partial/estimation_stages.html")
        return t.render({"o": obj})

    def _get_design_estimation_note(self, obj):
        """
        Render the design estimation note for the Opportunity using a partial template.
        """
        t = get_template("partial/design_estimation_note.html")
        return t.render({"o": obj})

    def _get_actions(self, obj):
        """
        Generate action buttons for the Opportunity with a link to the detail page.
        """
        t = get_template("partial/opportunity_detail_and_document_button.html")

        edit_url = reverse(
            "opportunity:opportunity-detail",
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
            print("filter_value: ", filter_value)

            column_filters = {
                0: "document_number",
                1: "designer",
                2: "estimator",
                3: "pump_electrical_designer",
                4: "design_estimation_note",
                5: "estimation_stage",
            }

            column_name = column_filters.get(column)
            print("column_name: ", column_name)
            if column_name:
                if values:
                    print("values: ", values)
                    qs = qs.filter(**{f"{column_name}__in": values})

                if filter_type and filter_value is not None:
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

    template_name = "opportunity/import_opportunity.html"
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
                    "redirect": reverse("opportunity:opportunity-list"),
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
    render_template_name = "opportunity/opportunity_detail.html"
    context_object_name = "opportunity"

    def get_object(self, queryset=None):
        """
        Override to retrieve the Opportunity object using document_number.
        """
        document_number = self.kwargs.get("document_number")
        return get_object_or_404(Opportunity, document_number=document_number)

    def get_context_data(self, **kwargs):
        """
        Returns a dictionary od the context object.
        """
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs.get("document_number")
        opportunity = Opportunity.objects.get(document_number=document_number)
        context["stage"] = opportunity.estimation_stage
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

    template_name = "opportunity/select_task_code_model.html"

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

                return JsonResponse(
                    {
                        "success_url": reverse("opportunity:opportunity-detail", args=(document_number,)),
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
        qs = Document.objects.filter(opportunity__document_number=document_number)
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
        return f"<a href='{obj.document.url}' download><i class='icon-cloud-download'></i> File</a>"

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "document": self._get_documents(o),
                    "created_at": o.created_at.strftime("%Y-%m-%d"),
                    "comment": o.comment,
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
        opportunity_object = Opportunity.objects.get(document_number=document_number)
        form.instance.opportunity = opportunity_object
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
        return reverse("opportunity:opportunity-detail", args=(document_number,))


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
    def get(self, request, column):
        print("column: ", column)
        choices = {
            "document_number": list(Opportunity.objects.values_list("document_number", flat=True).distinct()),
            "designer": list(Opportunity.objects.values_list("designer", flat=True).distinct()),
            "estimator": list(Opportunity.objects.values_list("estimator", flat=True).distinct()),
            "pump_electrical_designer": list(
                Opportunity.objects.values_list("pump_electrical_designer", flat=True).distinct()
            ),
            "design_estimation_note": list(
                Opportunity.objects.values_list("design_estimation_note", flat=True).distinct()
            ),
            "estimation_stage": list(Opportunity.objects.values_list("estimation_stage", flat=True).distinct()),
            "updated_at": list(
                Opportunity.objects.annotate(date=TruncDate("updated_at")).values_list("date", flat=True).distinct()
            ),
        }

        options = choices.get(column, [])
        print("options: ", options)
        return JsonResponse({"options": options})
