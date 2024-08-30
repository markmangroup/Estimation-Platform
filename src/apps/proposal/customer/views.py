from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import FormView, View
from django_datatables_too.mixins import DataTableMixin

from apps.rental.mixin import ProposalViewMixin

from .forms import ImportCustomerCSVForm
from .models import Customer
from .tasks import import_customer_from_xlsx


class CustomerList(ProposalViewMixin):
    """
    View class for rendering the list of proposal customer.
    """

    render_template_name = "proposal/customer/customer_list.html"


class CustomerListAjaxView(DataTableMixin, View):
    model = Customer
    queryset = Customer.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(internal_id__icontains=self.search)
                | Q(customer_id__icontains=self.search)
                | Q(name__icontains=self.search)
                | Q(sales_rep__icontains=self.search)
                | Q(billing_address_1__icontains=self.search)
                | Q(billing_address_2__icontains=self.search)
                | Q(city__icontains=self.search)
                | Q(state__icontains=self.search)
                | Q(zip__icontains=self.search)
                | Q(country__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "internal_id": o.internal_id,
                    "customer_id": o.customer_id,
                    "name": o.name,
                    "sales_rep": o.sales_rep,
                    "billing_address_1": o.billing_address_1,
                    "billing_address_2": o.billing_address_2,
                    "city": o.city,
                    "state": o.state,
                    "zip": o.zip,
                    "country": o.country,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class CustomerCreateFromCSVFormView(FormView):
    template_name = "proposal/customer/import_customer.html"
    form_class = ImportCustomerCSVForm

    def form_valid(self, form):
        csv_file = form.cleaned_data["csv_file"]
        file = csv_file
        _response = import_customer_from_xlsx(file)
        if _response:
            if _response.get("error"):
                form.add_error("csv_file", _response["error"])
                return self.render_to_response(self.get_context_data(form=form), status=201)
        else:
            return JsonResponse(
                {
                    "redirect": reverse("proposal_app:customer:customer-list"),
                    "message": "Customer Imported successfully!!",
                    "status": "success",
                    "code": 200,
                }
            )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)
