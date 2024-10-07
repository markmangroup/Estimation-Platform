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


class LoginBaseMixin(LoginRequiredMixin):
    """
    Base mixin for requiring login before accessing views.
    """

    ...


class AdminMixin(LoginRequiredMixin):
    """
    Base mixin for requiring admin login before accessing views.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect("proposal_app:opportunity:opportunity-list")
        return super().dispatch(request, *args, **kwargs)


class ProposalViewMixin(LoginBaseMixin, TemplateView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalCreateViewMixin(LoginBaseMixin, CreateView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalListViewMixin(LoginBaseMixin, ListView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalUpdateViewMixin(LoginBaseMixin, UpdateView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalDeleteViewMixin(LoginBaseMixin, DeleteView):
    """
    Mixin for rendering proposal-related views.
    """

    template_name = "proposal/proposal_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context


class ProposalDetailViewMixin(LoginBaseMixin, DetailView):
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


class ProposalFormViewMixin(LoginRequiredMixin, FormView):
    """
    Mixin for a login-required Form view.
    """

    ...


class ViewMixin(LoginRequiredMixin, View):
    """
    Mixin for a login-required View.
    """

    ...
