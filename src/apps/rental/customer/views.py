from django.db.models import Q
from django.http import JsonResponse

from apps.mixin import (
    CustomDataTableMixin,
    FormViewMixin,
    WarehouseDetailViewMixin,
    WarehouseViewMixin,
)
from apps.rental.customer.forms import ImportCustomerCSVForm
from apps.rental.customer.models import RentalCustomer
from apps.rental.customer.tasks import (  # update_customer_lat_and_log,
    import_customer_from_xlsx,
)


class CustomerListView(WarehouseViewMixin):
    """View class for rendering the list of warehouses."""

    render_template_name = "rental/customer/customer_list.html"


class CustomerDetailsView(WarehouseDetailViewMixin):
    """View for customer details."""

    model = RentalCustomer
    render_template_name = "rental/map/map_customer_detail.html"
    context_object_name = "rental_customer_detail"


class CustomerListAjaxView(CustomDataTableMixin):
    """AJAX view for listing customers in a data table format."""

    model = RentalCustomer

    def get_queryset(self):
        """Returns a list of customers."""
        return RentalCustomer.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
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
        """Create row data for datatables."""
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
        """Get a dictionary of data."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class CustomerCreateFromCSVFormView(FormViewMixin):
    """View for importing customers from a CSV file."""

    template_name = "rental/customer/import_customer.html"
    form_class = ImportCustomerCSVForm

    def form_valid(self, form):
        """Handle valid form submissions."""
        csv_file = form.cleaned_data["csv_file"]
        response = import_customer_from_xlsx(csv_file)

        if response and response.get("error"):
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        # Update lng and lat for customers
        # update_customer_lat_and_log.delay()

        return JsonResponse(
            {
                "message": "Customers imported successfully!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """Handle invalid form submissions."""
        return self.render_to_response(self.get_context_data(form=form), status=201)
