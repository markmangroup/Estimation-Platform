from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import FormView, View
from django_datatables_too.mixins import DataTableMixin

from apps.proposal.mixin import ProposalViewMixin
from apps.vendor.forms import ImportVendorForm
from apps.vendor.models import Vendor
from apps.vendor.tasks import import_vendor_from_file


# Create your views here.
class VendorListView(ProposalViewMixin):
    """
    View class for rendering the list of proposal vendor.
    """

    render_template_name = "proposal/vendor/vendor_list.html"


class VendorListAjaxView(DataTableMixin, View):
    """
    Handles AJAX requests for vendor list data.

    Filters and prepares vendor data for DataTables based on search input.
    """

    model = Vendor
    queryset = Vendor.objects.all()

    def filter_queryset(self, qs):
        """Filters queryset based on search criteria."""
        if self.search:
            return qs.filter(Q(internal_id__icontains=self.search) | Q(name__icontains=self.search))
        return qs

    def prepare_results(self, qs):
        """Prepares data for DataTables."""
        data = []
        for o in qs:
            data.append(
                {
                    "internal_id": o.internal_id,
                    "name": o.name,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """Returns JSON response with vendor data."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class VendorImportView(FormView):
    """
    Handles the upload and import of vendor data from a CSV or Excel file.

    Validates the file format and data before importing.
    """

    template_name = "proposal/vendor/import_vendor.html"
    form_class = ImportVendorForm

    def form_valid(self, form):
        """Processes valid CSV/Excel file and imports vendor data."""
        csv_file = form.cleaned_data["csv_file"]
        file = csv_file
        _response = import_vendor_from_file(file)
        if _response.get("error"):
            # messages.error(self.request, _response["error"])
            form.add_error("csv_file", _response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)
        else:
            return JsonResponse(
                {
                    "redirect": reverse("vendor:vendor-list"),
                    "message": "Vendor Import Successfully!!",
                    "status": "success",
                    "code": 200,
                }
            )

    def form_invalid(self, form):
        """Handles invalid form submissions."""
        return self.render_to_response(self.get_context_data(form=form), status=201)
