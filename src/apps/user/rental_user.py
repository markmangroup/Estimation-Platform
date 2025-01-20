from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.urls import reverse, reverse_lazy
from django.views.generic.base import View
from django.views.generic.edit import CreateView, UpdateView
from django_datatables_too.mixins import DataTableMixin

from apps.mixin import AdminMixin
from apps.user.models import Permissions, User

from .forms import RentalUserForm, RentalUserUpdateForm


class AddUserView(AdminMixin, CreateView):
    """View for adding a new user."""

    form_class = RentalUserForm
    template_name = "rental/authorization/add_user.html"

    def get_success_url(self):
        """Redirect to the user list page on successful user creation."""
        return reverse_lazy("rental:user_list")

    def form_valid(self, form):
        """
        Handle valid form submission by adding or updating a user.
        """
        user = self._get_user(form)

        if user:
            self._update_existing_user(user, form)
        else:
            self._create_new_user(form)

        return HttpResponse("success")

    def _get_user(self, form):
        """Retrieve user based on form data."""
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        email = form.cleaned_data["email"]

        return User.objects.filter(email=email, first_name=first_name, last_name=last_name).first()

    def _update_existing_user(self, user, form):
        """Update an existing user with the provided form data."""
        application_types = set(user.application_type)  # Use a set for faster membership testing
        application_types.add(User.RENTAL)  # Ensure RENTAL is included
        user.application_type = list(application_types)
        user.mobile = form.cleaned_data["mobile"]
        user.is_superuser = form.cleaned_data["is_superuser"]
        user.save()

        messages.success(self.request, "The user has been successfully updated.")

    def _create_new_user(self, form):
        """Create a new user with the provided form data."""
        user = form.save(commit=False)
        user.application_type = [User.RENTAL]
        user.save()

        messages.success(self.request, "The user has been successfully added.")

    def form_invalid(self, form):
        """
        Render the form with errors if the submission is invalid.
        """
        return render(self.request, self.template_name, {"form": form}, status=201)


class UserAjaxListView(AdminMixin, DataTableMixin, View):
    """
    User list with ajax requests.
    """

    model = User

    def get_queryset(self):
        """Return queryset."""
        qs = User.objects.filter(application_type__contains=User.RENTAL)
        return qs

    def _get_permissions(self, obj):
        """Get Permissions for the given object."""
        t = get_template("rental/partial/permissions.html")

        # Split the comma-separated permissions into a list
        permissions_list = obj.permissions.values_list("name", flat=True)

        return t.render({"o": obj, "permissions": permissions_list})

    def _get_actions(self, obj):
        """Get Action buttons for table."""
        t = get_template("rental/partial/list_row_action_custom_url.html")

        edit_url = reverse(
            "user:rental-edit-user",
            kwargs={"pk": obj.id},
        )

        delete_url = reverse(
            "user:ajax-rental-user-delete",
        )

        data_target = "#update_user_modal"
        hx_target = "#update_user_modal_body"

        return t.render(
            {
                "edit_url": edit_url,
                "delete_url": delete_url,
                "data_target": data_target,
                "hx_target": hx_target,
                "o": obj,
                "request": self.request,
            }
        )

    def filter_queryset(self, qs):
        """Return the list of items for this view."""

        if self.search:
            return qs.filter(Q(username__icontains=self.search) | Q(email__icontains=self.search))
        return qs

    def prepare_results(self, qs):
        """Prepare Data for display"""

        data = []
        for o in qs:
            data.append(
                {
                    "username": f"{o.first_name} {o.last_name}",
                    "email": o.email,
                    "mobile": o.mobile if o.mobile else "-",
                    "permission": self._get_permissions(o),
                    "action": self._get_actions(o),
                }
            )

        return data

    def get(self, request, *args, **kwargs):
        """Handle GET request."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class UpdateUserView(AdminMixin, UpdateView):
    """Update User View"""

    model = User
    form_class = RentalUserUpdateForm
    template_name = "rental/authorization/edit_user.html"

    def get_success_url(self):
        return reverse_lazy("rental:user_list")

    def form_valid(self, form):
        permissions = form.cleaned_data["permissions"]

        permission_ids = [permission.id for permission in permissions]
        permission_objects = Permissions.objects.filter(id__in=permission_ids)

        fetched_permission_ids = set(permission_objects.values_list("id", flat=True))
        missing_permission_ids = set(permission_ids) - fetched_permission_ids

        if missing_permission_ids:
            raise ValidationError(f"Some permissions are missing: {', '.join(map(str, missing_permission_ids))}")

        self.object = form.save(commit=False)
        self.object.permissions.set(permission_objects)

        self.object.save()

        messages.success(self.request, "User Updated successfully.")
        return HttpResponse("success")

    def form_invalid(self, form):
        return render(self.request, self.template_name, {"form": form}, status=201)


class DeleteUserView(AdminMixin, View):
    """
    View for delete the user objects.
    """

    def post(self, request):
        user_id = request.POST.get("id")
        current_user = request.user
        user = User.objects.filter(id=user_id).first()

        if current_user == user:
            messages.info(
                request,
                "Access Denied: You do not have the necessary permissions to access this application. Please contact your provider for assistance",
            )
            user.delete()
            return JsonResponse(
                {
                    "code": "111",
                    "message": "Access Denied: You do not have the necessary permissions to access this application. Please contact your provider for assistance",
                }
            )

        user.delete()
        return JsonResponse({"code": "200", "message": "User Deleted Successfully."})
