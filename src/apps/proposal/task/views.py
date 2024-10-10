from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse

from apps.mixin import CustomDataTableMixin, FormViewMixin, ProposalViewMixin
from apps.proposal.task.forms import ImportTaskForm
from apps.proposal.task.models import Task
from apps.proposal.task.tasks import import_task_from_file


class TaskListView(ProposalViewMixin):
    """
    View for displaying the task list in proposals.
    """

    render_template_name = "proposal/task/task_list.html"


class TaskListAjaxView(CustomDataTableMixin):
    """AJAX view for retrieving task data in a DataTable format."""

    model = Task
    
    def get_queryset(self):
        """
        Returns a list of tasks.
        """
        return Task.objects.all()

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


class TaskImportView(FormViewMixin):
    """
    View for importing tasks from CSV or Excel files.
    """

    template_name = "proposal/task/import_task.html"
    form_class = ImportTaskForm

    def form_valid(self, form):
        """
        Process valid form submission and import tasks.
        """
        csv_file = form.cleaned_data["csv_file"]
        # To check file size
        # file_size = csv_file.size

        response = import_task_from_file(csv_file)
        if response.get("error"):
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        return JsonResponse(
            {
                "redirect": reverse("proposal_app:task:task-list"),
                "message": "Task imported successfully!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """
        Handle invalid form submission.
        """
        return self.render_to_response(self.get_context_data(form=form), status=201)
