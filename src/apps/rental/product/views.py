from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse

from apps.mixin import CustomDataTableMixin, FormViewMixin, WarehouseViewMixin
from apps.rental.product import forms, tasks
from apps.rental.product.models import RentalProduct


class RentalProductListView(WarehouseViewMixin):
    """
    View class for rendering the list of warehouse products.
    """

    render_template_name = "rental/product/product.html"

    def get_context_data(self, *args, **kwargs):
        """Get context data for template rendering."""

        context = super().get_context_data(*args, **kwargs)
        equipment_material_group = RentalProduct.objects.values("equipment_material_group").distinct()
        equipment_material_group = sorted(
            equipment_material_group, 
            key=lambda x: (not x['equipment_material_group'].isdigit(), x['equipment_material_group'] if not x['equipment_material_group'].isdigit() else int(x['equipment_material_group']))
        )
        equipment_name = RentalProduct.objects.values("equipment_name").distinct()
        context["equipment_material_group"] = equipment_material_group
        context["equipment_name"] = list(equipment_name)
        return context


class RentalProductListAjaxView(CustomDataTableMixin):
    """
    Rental product DataTable View
    """

    model = RentalProduct

    def get_queryset(self):
        """Returns a list of rental products."""
        qs = RentalProduct.objects.all()

        equipment_mat_grp = self.request.GET.getlist("equipment_mat_grp[]", [])
        name = self.request.GET.getlist("name[]", [])

        if equipment_mat_grp:
            qs = qs.filter(equipment_material_group__in=equipment_mat_grp)

        if name:
            qs = qs.filter(equipment_name__in=name)

        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(equipment_name__icontains=self.search)
                | Q(equipment_id__icontains=self.search)
                | Q(equipment_material_group__icontains=self.search)
                | Q(subtype__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            data.append(
                {
                    "equipment_id": o.equipment_id,
                    "equipment_material_group": o.equipment_material_group,
                    "equipment_name": o.equipment_name,
                    "subtype": o.subtype,
                }
            )
        print("data: ", data)
        return data

    def get(self, request, *args, **kwargs):
        """Get a dictionary of data."""
        context_data = self.get_context_data(request)
        print("context_data: ", context_data)
        return JsonResponse(context_data)


class RentalProductImportView(FormViewMixin):
    """
    Import data from CSV or Excel files.
    """

    template_name = "rental/product/import_product.html"
    form_class = forms.ImportProductForm

    def form_valid(self, form):
        """Handle valid form submission and import products."""
        csv_file = form.cleaned_data["csv_file"]
        response = tasks.import_product_from_file(csv_file)

        if "error" in response:
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        return JsonResponse(
            {
                "redirect": reverse("rental:rental_product:rental-product-list"),
                "message": "Product imported successfully!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """Handle invalid form submission."""
        return self.render_to_response(self.get_context_data(form=form), status=201)
