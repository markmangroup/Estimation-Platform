from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import FormView, View
from django_datatables_too.mixins import DataTableMixin

from apps.proposal.task.forms import ImportTaskForm
from apps.proposal.task.models import Task
from apps.proposal.task.tasks import import_task_from_file
from apps.rental.mixin import ProposalViewMixin


class TaskListView(ProposalViewMixin):
    """
    View class for rendering the list of proposal task.
    """

    render_template_name = "proposal/task/task_list.html"


class TaskListAjaxView(DataTableMixin, View):
    model = Task
    queryset = Task.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(internal_id__icontains=self.search)
                | Q(name__icontains=self.search)
                | Q(description__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "internal_id": o.internal_id,
                    "name": o.name,
                    "description": o.description,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class TaskImportView(FormView):
    """
    Import data from CSV or Excel files.
    """

    template_name = "proposal/task/import_task.html"
    form_class = ImportTaskForm

    def form_valid(self, form):
        csv_file = form.cleaned_data["csv_file"]
        file = csv_file
        print(f"file Size {file.size}")
        _response = import_task_from_file(file)
        if _response.get("error"):
            form.add_error("csv_file", _response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)
        else:
            return JsonResponse(
                {
                    "redirect": reverse("proposal_app:task:task-list"),
                    "message": "Task Import Successfully!!",
                    "status": "success",
                    "code": 200,
                }
            )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)
