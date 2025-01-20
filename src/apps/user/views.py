from typing import Any

from django.contrib import messages
from django.contrib.auth import logout
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import get_template
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.views.generic.edit import CreateView, UpdateView
from django_datatables_too.mixins import DataTableMixin

from apps.constants import LOGGER
from apps.mixin import AdminMixin, ProposalCreateViewMixin
from apps.user.models import User

from .forms import UserForm, UserUpdateForm
from django.http import JsonResponse  

def health_check(request):  
    return JsonResponse({'status': 'ok'}) 

class LoginView(TemplateView):
    """
    view for handles user login.

    This view renders the login template. If the user is already authenticated,
    it redirects them to the 'choose_screens' view. Otherwise, it proceeds to
    render the login page.
    """

    template_name = "user/login.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect("choose_screens")
        return super().dispatch(request, *args, **kwargs)


class LogoutView(View):
    """View for handling user logout."""

    def get(self, request, *args, **kwargs):
        """
        Logs out the user and redirects to the home page.
        """
        logout(request)
        return redirect("/")


class AuthorizationView(ProposalCreateViewMixin, AdminMixin):
    """
    View class for creating new user.
    """

    model = User
    form_class = UserForm
    render_template_name = "user/authorization.html"
    success_url = reverse_lazy("proposal:authorization")

    def form_valid(self, form):
        username = form.cleaned_data["username"]
        user = form.save(commit=False)
        user.set_password(form.cleaned_data["password"])
        user.save()
        messages.success(self.request, f'User "{username}" created successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors:
            LOGGER.error(f"Form Error: {error}")
        messages.error(
            self.request,
            "There was an error creating the user. Please check the form and try again.",
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_list"] = User.objects.all()
        return context


class AddUserView(AdminMixin, CreateView):
    """View for adding a new user."""

    form_class = UserForm
    template_name = "proposal/forms/authorization/add_user.html"

    def get_success_url(self):
        """Redirect to the authorization page on successful user creation."""
        return reverse_lazy("user:authorization")

    def form_valid(self, form):
        """Handle valid form submission by adding or updating a user."""
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
        application_types.add(User.PROPOSAL)  # Add Proposal if it's not already present

        user.application_type = list(application_types)
        user.is_superuser = form.cleaned_data["is_superuser"]
        user.save()

        messages.success(self.request, "The user has been successfully updated.")

    def _create_new_user(self, form):
        """Create a new user with the provided form data."""
        user = form.save(commit=False)
        user.application_type = [User.PROPOSAL]
        user.save()

        messages.success(self.request, "The user has been successfully added.")

    def form_invalid(self, form):
        """Render the form with errors if the submission is invalid."""
        return render(self.request, self.template_name, {"form": form}, status=201)


class UserAjaxListView(AdminMixin, DataTableMixin, View):
    """
    User list with ajax requests.
    """

    model = User

    def get_queryset(self):
        """Return queryset."""
        qs = User.objects.filter(application_type__contains=User.PROPOSAL)
        return qs

    def _get_actions(self, obj):
        """Get Action buttons for table."""
        t = get_template("proposal/partial/list_row_action_custom_url.html")

        edit_url = reverse(
            "user:edit-user",
            kwargs={"pk": obj.id},
        )

        delete_url = reverse(
            "user:ajax-user-delete",
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
                "class": "user-delete-btn",
                "title": obj.email,
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
                    "first_name": o.first_name,
                    "last_name": o.last_name,
                    "email": o.email,
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
    form_class = UserUpdateForm
    template_name = "proposal/forms/authorization/edit_user.html"

    def get_success_url(self):
        return reverse_lazy("user:authorization")

    def form_valid(self, form):
        messages.success(self.request, "User Updated successfully.")
        self.object = form.save(commit=True)
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


class CheckUserAccountTypeView(View):
    def get(self, request, *args, **kwargs):
        if "Rental" in request.user.application_type and "Proposal" in request.user.application_type:
            return redirect("choose_screens")
        elif "Proposal" in request.user.application_type:
            return redirect("proposal_app:opportunity:opportunity-list")
        return redirect("rental:map_view")
