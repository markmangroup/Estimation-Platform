from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)


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
            return redirect("opportunity:opportunity-list")
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


class WarehouseViewMixin(LoginBaseMixin, TemplateView):
    """
    Mixin for rendering warehouse-related views.
    """

    template_name = "warehouse/warehouse_wrapper.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_name"] = self.render_template_name
        return context
