from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse

from apps.mixin import CustomDataTableMixin, FormViewMixin, ProposalViewMixin
from apps.proposal.product import forms, tasks
from apps.proposal.product.models import AdditionalMaterials, Product


# Create your views here.
class ProductListView(ProposalViewMixin):
    """
    View for displaying a list of products.
    """

    render_template_name = "proposal/product/product_list.html"


class ProductListAjaxView(CustomDataTableMixin):
    """
    AJAX view for displaying product master data in a DataTable.
    """

    model = Product

    def get_queryset(self):
        """
        Returns a list of product.
        """
        return Product.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(internal_id__icontains=self.search)
                | Q(family__icontains=self.search)
                | Q(parent__icontains=self.search)
                | Q(description__icontains=self.search)
                | Q(primary_units_type__icontains=self.search)
                | Q(primary_stock_unit__icontains=self.search)
                | Q(std_cost__icontains=self.search)
                | Q(preferred_vendor__icontains=self.search)
                | Q(type__icontains=self.search)
                | Q(name__icontains=self.search)
                | Q(display_name__icontains=self.search)
                | Q(tax_schedule__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "internal_id": o.internal_id,
                    "description": o.description,
                    "std_cost": o.std_cost,
                    "primary_units_type": o.primary_units_type,
                    "primary_stock_unit": o.primary_stock_unit,
                    "preferred_vendor": o.preferred_vendor,
                    "family": o.family,
                    "type": o.type,
                    "name": o.name,
                    "parent": o.parent,
                    "display_name": o.display_name,
                    "tax_schedule": o.tax_schedule,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class ProductImportView(FormViewMixin):
    """
    Import data from CSV or Excel files.
    """

    template_name = "proposal/product/import_product.html"
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
                "redirect": reverse("proposal_app:product:product-list"),
                "message": "Product imported successfully!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """Handle invalid form submission."""
        return self.render_to_response(self.get_context_data(form=form), status=201)


class AdditionalMaterialAjaxView(CustomDataTableMixin):
    """AJAX view for displaying additional material data in a DataTable."""

    model = AdditionalMaterials

    def get_queryset(self):
        """
        Returns a list of additional material.
        """
        return AdditionalMaterials.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(material_id__icontains=self.search)
                | Q(material_name__icontains=self.search)
                | Q(material_type__icontains=self.search)
                | Q(product_item_number__icontains=self.search)
                | Q(material_factor__icontains=self.search)
                | Q(additional_material_factor__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "material_id": o.material_id,
                    "material_name": o.material_name,
                    "material_type": o.material_type,
                    "product_item_number": o.product_item_number,
                    "material_factor": o.material_factor,
                    "additional_material_factor": o.additional_material_factor,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class AdditionalMaterialImportView(FormViewMixin):
    """Import data from CSV or Excel files."""

    template_name = "proposal/product/import_additional_material.html"
    form_class = forms.ImportMaterialForm

    def form_valid(self, form):
        """Handle valid form submission and import additional material."""
        csv_file = form.cleaned_data["csv_file"]
        response = tasks.import_additional_material_from_file(csv_file)

        if "error" in response:
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        messages.success(self.request, "Additional Material imported successfully!")
        return JsonResponse(
            {
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """Handle invalid form submission."""
        return self.render_to_response(self.get_context_data(form=form), status=201)
