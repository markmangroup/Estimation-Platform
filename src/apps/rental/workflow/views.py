from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse

from apps.mixin import WarehouseViewMixin
from apps.user.models import Permissions, User

# Create your views here.


class Workflow(WarehouseViewMixin):
    """
    Handle the workflow for managing user permissions.
    """

    render_template_name = "rental/workflow/workflow.html"

    def get_context_data(self, **kwargs):
        """
        Retrieve the context data for rendering the workflow page.

        This includes all rental users and permissions, along with the users
        associated with each permission.

        :param kwargs: Any additional context parameters.
        :return: Context dictionary containing users, permissions, and the
                 users associated with each permission.
        """
        context = super().get_context_data(**kwargs)

        rental_users = User.objects.filter(application_type__contains=User.RENTAL)
        permissions = Permissions.objects.all()

        permission_users = {permission.id: list(permission.user_permissions.all()) for permission in permissions}

        context["users"] = rental_users
        context["permissions"] = permissions
        context["permission_users"] = permission_users

        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Handle the POST request to update user permissions.

        This method updates the users associated with a specific permission,
        adding or removing users based on the user's input.

        :param request: The HTTP request object.
        :param args: Any additional positional arguments.
        :param kwargs: Any additional keyword arguments.
        :return: JsonResponse with the status of the operation and the corresponding message.
        """
        permission_id = request.POST.get("permission_id")
        selected_users = request.POST.get("selected_users")

        if not permission_id:
            return JsonResponse({"status": "error", "message": "Permission ID is required"})

        try:
            permission = Permissions.objects.get(id=permission_id)
        except Permissions.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Permission not found"})

        if not selected_users:
            permission.user_permissions.clear()
            message = f'All users removed from the "{permission.name}" permission.'
            messages.success(self.request, message)
            return JsonResponse({"status": "success", "message": message})

        selected_users = set(map(int, selected_users.split(",")))
        current_users = set(permission.user_permissions.values_list("id", flat=True))

        users_to_add = selected_users - current_users
        users_to_remove = current_users - selected_users

        added_users_names = []
        removed_users_names = []

        users_to_add_queryset = User.objects.filter(id__in=users_to_add)
        users_to_remove_queryset = User.objects.filter(id__in=users_to_remove)

        for user in users_to_add_queryset:
            permission.user_permissions.add(user)
            added_users_names.append(user.full_name)

        for user in users_to_remove_queryset:
            permission.user_permissions.remove(user)
            removed_users_names.append(user.full_name)

        add_message = (
            f'Users {", ".join(added_users_names)} added to the "{permission.name}" permission.'
            if added_users_names
            else ""
        )
        remove_message = (
            f'Users {", ".join(removed_users_names)} removed from the "{permission.name}" permission.'
            if removed_users_names
            else ""
        )

        message = f"{add_message} {remove_message}".strip()
        messages.success(self.request, message)

        return JsonResponse({"status": "success", "message": message})
