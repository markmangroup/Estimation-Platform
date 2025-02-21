from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.urls import reverse

from apps.constants import ERROR_RESPONSE, LOGGER
from apps.mixin import CustomDataTableMixin, CustomViewMixin, ViewMixin
from apps.proposal.opportunity.tasks import generate_task_mapping_table
from apps.proposal.opportunity.views.generate_estimate import GenerateEstimate
from apps.proposal.opportunity.views.task_mapping import TaskMappingData
from apps.proposal.task.models import Task

from ..models import Opportunity, SelectTaskCode, TaskMapping


class SelectedTaskListAjaxView(CustomDataTableMixin):
    """AJAX view to return a list of selected tasks for DataTables."""

    model = SelectTaskCode

    def _get_actions(self, obj):
        """Generate action buttons for the Task to delete."""
        t = get_template("proposal/partial/list_row_action_custom_url.html")

        delete_url = reverse(
            "proposal_app:opportunity:ajax-delete-selected-task",
        )

        return t.render(
            {
                "delete_url": delete_url,
                "o": obj,
                "class": "delete-task",
                "title": obj.task.name,
            }
        )

    def _get_description(self, obj):
        """Make description editable."""
        task_mapping_object = TaskMapping.objects.filter(
            opportunity=obj.opportunity,
            task=obj.task,
        ).first()
        t = get_template("proposal/partial/edit_description.html")
        return t.render(
            {
                "o": obj,
                "task": task_mapping_object,
            }
        )

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
                | Q(task_description__icontains=self.search)
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
                    "task__description": self._get_description(o),
                    "action": self._get_actions(o),
                }
            )
        return sorted(data, key=lambda x: x["task__name"])


    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class TaskManagementView(ViewMixin):
    """
    Handle both rendering of the task selection form and task creation.
    """

    template_name = "proposal/opportunity/stage/select_task_code/select_task_code_model.html"

    def get(self, request, *args, **kwargs):
        """
        Render the task selection template with available tasks.

        :param request: The HTTP request object.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments, including 'document_number'.
        :return: Rendered response containing available tasks.
        """
        document_number = self.kwargs.get("document_number")
        context = self._get_context_data(document_number)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle task selection and creation.

        :param request: The HTTP request object containing form data.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JSON response indicating success or error status.
        """
        tasks = request.POST.getlist("task")
        document_number = request.POST.get("document_number")

        if not tasks or not document_number:
            return JsonResponse({"error": "Tasks and document number are required."}, status=400)

        opportunity = get_object_or_404(Opportunity, document_number=document_number)

        for task_name in tasks:
            task_instance = get_object_or_404(Task, name=task_name)
            SelectTaskCode.objects.create(opportunity=opportunity, task=task_instance)

        data = generate_task_mapping_table(opportunity=opportunity)

        # Render the updated HTML for the task mapping table
        html = render(request, "proposal/opportunity/stage/task_mapping/tasks.html", data)

        return JsonResponse(
            {
                "code": 201,
                "message": "Tasks added successfully!",
                "modal_to_close": "modelSelectTask",
                "html": html.content.decode("utf-8"),
            },
            status=201,
        )

    def _get_context_data(self, document_number: str) -> dict:
        """
        Returns context data with available tasks.

        :param document_number: The document number associated with the opportunity.
        :return: A dictionary containing available tasks and the document number.
        """
        opportunity = get_object_or_404(Opportunity, document_number=document_number)

        selected_task_ids = (
            SelectTaskCode.objects.filter(opportunity=opportunity)
            .exclude(task__description__icontains="labor")
            .values_list("task_id", flat=True)
        )
        available_tasks = Task.objects.exclude(id__in=selected_task_ids)

        return {
            "select_tasks": available_tasks,
            "document_number": document_number,
        }

    def render_to_response(self, context, **response_kwargs):
        """
        Render the response using the template specified.

        :param context: A dictionary containing the context data for rendering.
        :param response_kwargs: Additional keyword arguments for rendering.
        :return: Rendered response.
        """
        return render(self.request, self.template_name, context, **response_kwargs)


class UpdateDescription(ViewMixin):
    """
    View to handle updating the description of a task code.
    """

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle the POST request to update the task description.

        :param request (HttpRequest): The HTTP request object containing POST data.
        :param *args: Additional positional arguments.
        :param **kwargs: Additional keyword arguments.
        :return JsonResponse: A JSON response indicating success or failure with a status code.
        """
        task_code_id = request.POST.get("task_code_id")
        task_description = request.POST.get("task_description")

        try:
            select_task_code_obj = SelectTaskCode.objects.get(id=task_code_id)
            select_task_code_obj.task_description = task_description
            select_task_code_obj.save()
            return JsonResponse(
                {
                    "message": "Task description updated successfully",
                    "status": "OK",
                },
                status=201,
            )
        except Exception as e:
            LOGGER.error(f"-- An error occurred while updating description of task -- {e}")
            return JsonResponse(ERROR_RESPONSE, status=400)


class DeleteSelectedTask(CustomViewMixin):
    """
    View to delete assigned product objects.
    """

    def __post(self, task_id):
        """
        Handle the task deletion logic.

        :param task_id: The ID of the task to be deleted.
        """
        try:
            select_task_code = SelectTaskCode.objects.filter(id=task_id).first()
            task_mapping = TaskMapping.objects.filter(
                opportunity=select_task_code.opportunity,
                task=select_task_code.task,
                description=(
                    select_task_code.task_description
                    if select_task_code.task_description
                    else select_task_code.task.description
                ),
            )

            select_task_code.delete()
            task_mapping.delete()

            self._code = 200
            self._message = "Task Deleted Successfully"
            self._status = "success"

            # :: Deprecated ::
            # messages.info(self.request, "Task Deleted Successfully")

            data = generate_task_mapping_table(opportunity=select_task_code.opportunity)
            html = render(self.request, "proposal/opportunity/stage/task_mapping/tasks.html", data)

            extra_data = {"html": html.content.decode("utf-8")}

        except Exception as e:
            LOGGER.error(f"Select Task Code Delete Error: {e}")
            self._code = 400
            extra_data = {}

        return self.generate_response(extra_data)

    def post(self, request) -> JsonResponse:
        """
        Handle POST requests to delete an assigned product.

        :param request: The request object containing the ID of the assigned product to delete.
        """
        task_id = request.POST.get("id")
        return self.__post(task_id)
