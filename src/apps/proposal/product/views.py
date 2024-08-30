from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import FormView, View
from django_datatables_too.mixins import DataTableMixin

from apps.proposal.product.forms import ImportProductForm
from apps.proposal.product.models import Product
from apps.proposal.product.tasks import import_product_from_file
from apps.rental.mixin import ProposalViewMixin


# Create your views here.
class ProductListView(ProposalViewMixin):
    """
    View class for rendering the list of proposal product.
    """

    render_template_name = "proposal/product/product_list.html"


class ProductListAjaxView(DataTableMixin, View):
    """
    DataTable for Product master data.
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


class ProductImportView(FormView):
    """
    Import data from CSV or Excel files.
    """

    template_name = "proposal/product/import_product.html"
    form_class = ImportProductForm

    def form_valid(self, form):
        csv_file = form.cleaned_data["csv_file"]
        file = csv_file
        _response = import_product_from_file(file)
        if _response.get("error"):
            # messages.error(self.request, _response["error"])
            form.add_error("csv_file", _response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)
        else:
            return JsonResponse(
                {
                    "redirect": reverse("proposal_app:product:product-list"),
                    "message": "Product Imported successfully!!",
                    "status": "success",
                    "code": 200,
                }
            )

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form), status=201)
