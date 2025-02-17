from django.db.models import Q
from django.http import JsonResponse

from apps.mixin import CustomDataTableMixin, FormViewMixin, WarehouseViewMixin
from apps.rental.account_manager.forms import ImportAccountManagerCSVForm
from apps.rental.account_manager.models import AccountManager
from apps.rental.account_manager.tasks import import_account_manager_from_xlsx


class AccountManagerView(WarehouseViewMixin):
    """View class for rendering the list of warehouses."""

    render_template_name = "rental/account_manager/account_managers.html"


class AccountManagerListAjaxView(CustomDataTableMixin):
    """AJAX view for listing account manager in a data table format."""

    model = AccountManager

    def get_queryset(self):
        """Returns a list of account manager."""
        return AccountManager.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(Q(name__icontains=self.search) | Q(email__icontains=self.search) | Q(manager_id__icontains=self.search))
        return qs

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            data.append(
                {   "manager id": o.manager_id,
                    "name": o.name,
                    "email": o.email,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """Get a dictionary of data."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class AccountManagerCreateFromCSVFormView(FormViewMixin):
    """View for importing account manager from a CSV file."""

    template_name = "rental/account_manager/import_account_manager.html"
    form_class = ImportAccountManagerCSVForm

    def form_valid(self, form):
        """Handle valid form submissions."""
        csv_file = form.cleaned_data["csv_file"]
        response = import_account_manager_from_xlsx(csv_file)
        print('response: ', response)

        if response and response.get("error"):
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        return JsonResponse(
            {
                "message": "Account Manager Imported Successfully!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """Handle invalid form submissions."""
        return self.render_to_response(self.get_context_data(form=form), status=201)
