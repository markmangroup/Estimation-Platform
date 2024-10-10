from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse

from apps.mixin import CustomDataTableMixin, FormViewMixin, ProposalViewMixin
from apps.proposal.vendor.forms import ImportVendorForm
from apps.proposal.vendor.models import Vendor
from apps.proposal.vendor.tasks import import_vendor_from_file


# Create your views here.
class VendorListView(ProposalViewMixin):
    """
    View for displaying the list of vendors.
    """

    render_template_name = "proposal/vendor/vendor_list.html"


class VendorListAjaxView(CustomDataTableMixin):
    """
    Ajax view for retrieving vendor data for DataTables.
    """

    model = Vendor
    
    def get_queryset(self):
        """
        Returns a list of vendor.
        """
        return Vendor.objects.all()

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


class VendorImportView(FormViewMixin):
    """
    Handles the upload and import of vendor data from a CSV or Excel file.
    Validates the file format and data before importing.
    """

    template_name = "proposal/vendor/import_vendor.html"
    form_class = ImportVendorForm

    def form_valid(self, form):
        """Processes valid CSV/Excel file and imports vendor data."""
        csv_file = form.cleaned_data["csv_file"]
        response = import_vendor_from_file(csv_file)

        if response.get("error"):
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        return JsonResponse(
            {
                "redirect": reverse("proposal_app:vendor:vendor-list"),
                "message": "Vendor Import Successful!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """Handles invalid form submissions."""
        return self.render_to_response(self.get_context_data(form=form), status=201)
