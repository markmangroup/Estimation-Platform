from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse

from apps.mixin import CustomDataTableMixin, FormViewMixin, ProposalViewMixin

from .forms import ImportCustomerCSVForm
from .models import Customer
from .tasks import import_customer_from_xlsx


class CustomerList(ProposalViewMixin):
    """
    View to displaying the customer list.
    """

    render_template_name = "proposal/customer/customer_list.html"


class CustomerListAjaxView(CustomDataTableMixin):
    """AJAX view for listing customers in a data table format."""

    model = Customer
    
    def get_queryset(self):
        """
        Returns a list of customers
        """
        return Customer.objects.all()

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


class CustomerCreateFromCSVFormView(FormViewMixin):
    """
    View for importing customers from a CSV file.
    Handles file upload and returns a JSON response.
    """

    template_name = "proposal/customer/import_customer.html"
    form_class = ImportCustomerCSVForm

    def form_valid(self, form):
        csv_file = form.cleaned_data["csv_file"]
        response = import_customer_from_xlsx(csv_file)

        if response and response.get("error"):
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        return JsonResponse(
            {
                "redirect": reverse("proposal_app:customer:customer-list"),
                "message": "Customers imported successfully!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """Handle invalid form submissions."""
        return self.render_to_response(self.get_context_data(form=form), status=201)
