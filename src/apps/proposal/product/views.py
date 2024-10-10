from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse

from apps.mixin import CustomDataTableMixin, FormViewMixin, ProposalViewMixin
from apps.proposal.product.forms import ImportProductForm
from apps.proposal.product.models import Product
from apps.proposal.product.tasks import import_product_from_file


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
    queryset = Product.objects.all()

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
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "internal_id": o.internal_id,
                    "family": o.family,
                    "parent": o.parent,
                    "description": o.description,
                    "primary_units_type": o.primary_units_type,
                    "primary_stock_unit": o.primary_stock_unit,
                    "std_cost": o.std_cost,
                    "preferred_vendor": o.preferred_vendor,
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
    form_class = ImportProductForm

    def form_valid(self, form):
        """Handle valid form submission and import products."""
        csv_file = form.cleaned_data["csv_file"]
        response = import_product_from_file(csv_file)

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
