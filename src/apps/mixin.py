from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)
from django_datatables_too.mixins import DataTableMixin


class AdminMixin(LoginRequiredMixin):
    """
    Base mixin for requiring admin login before accessing views.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect("proposal_app:opportunity:opportunity-list")
        return super().dispatch(request, *args, **kwargs)


class ProposalViewMixin(LoginRequiredMixin, TemplateView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalCreateViewMixin(LoginRequiredMixin, CreateView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalListViewMixin(LoginRequiredMixin, ListView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalUpdateViewMixin(LoginRequiredMixin, UpdateView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalDeleteViewMixin(LoginRequiredMixin, DeleteView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalDetailViewMixin(LoginRequiredMixin, DetailView):
    """
    Mixin For Rendering Detail Proposal Views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class WarehouseViewMixin(TemplateView):
    """
    Mixin for rendering warehouse-related views.
    """

    template_name = "rental/warehouse_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class CustomDataTableMixin(LoginRequiredMixin, DataTableMixin, View):
    """
    Mixin for a login-required DataTable view.
    """

    ...


class TemplateViewMixin(LoginRequiredMixin, TemplateView):
    """
    Mixin for a login-required Template View.
    """

    ...


class ListViewMixin(LoginRequiredMixin, ListView):
    """
    Mixin for a login-required List View.
    """

    ...


class DetailsViewMixin(LoginRequiredMixin, DetailView):
    """
    Mixin for a login-required List View.
    """

    ...


class CreateViewMixin(LoginRequiredMixin, CreateView):
    """
    Mixin for a login-required Create View.
    """

    ...


class UpdateViewMixin(LoginRequiredMixin, UpdateView):
    """
    Mixin for a login-required Update View.
    """

    ...


class DeleteViewMixin(LoginRequiredMixin, DeleteView):
    """
    Mixin for a login-required Delete View.
    """

    ...


class FormViewMixin(LoginRequiredMixin, FormView):
    """
    Mixin for a login-required Form view.
    """

    ...


class ViewMixin(LoginRequiredMixin, View):
    """
    Mixin for a login-required View.
    """

    ...
