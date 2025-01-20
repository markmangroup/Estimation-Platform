from django.db.models import Q
from django.http import JsonResponse

from apps.mixin import (
    CustomDataTableMixin,
    FormViewMixin,
    WarehouseDetailViewMixin,
    WarehouseViewMixin,
)
from apps.rental.warehouse.forms import ImportWarehouseCSVForm
from apps.rental.warehouse.models import RentalWarehouse
from apps.rental.warehouse.tasks import (  # update_warehouse_lat_and_log,
    import_warehouse_from_xlsx,
)


class WarehouseView(WarehouseViewMixin):
    """
    View class for rendering the list of warehouses.
    """

    render_template_name = "rental/warehouse/warehouse_list.html"


class WarehouseDetailsView(WarehouseDetailViewMixin):
    """View for warehouse details."""

    model = RentalWarehouse
    render_template_name = "rental/map/map_warehouse_detail.html"
    context_object_name = "rental_warehouse_detail"


class WarehouseListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Warehouse in a data table format."""

    model = RentalWarehouse

    def get_queryset(self):
        """Returns a list of warehouse."""
        return RentalWarehouse.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(Q(location__icontains=self.search) | Q(address__icontains=self.search))
        return qs

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            data.append(
                {
                    "location": o.location,
                    "address": o.address,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """Get a dictionary of data."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class WarehouseCreateFromCSVFormView(FormViewMixin):
    """View for importing warehouse from a CSV file."""

    template_name = "rental/warehouse/import_warehouse.html"
    form_class = ImportWarehouseCSVForm

    def form_valid(self, form):
        """Handle valid form submissions."""
        csv_file = form.cleaned_data["csv_file"]
        response = import_warehouse_from_xlsx(csv_file)

        if response and response.get("error"):
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        # Update lng and lat for warehouse
        # update_warehouse_lat_and_log.delay()

        return JsonResponse(
            {
                "message": "Warehouse Imported Successfully!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """Handle invalid form submissions."""
        return self.render_to_response(self.get_context_data(form=form), status=201)
