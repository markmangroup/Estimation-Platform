from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import FormView, View
from django_datatables_too.mixins import DataTableMixin

from apps.rental.mixin import ProposalViewMixin

from .forms import ImportLabourCostCSVForm
from .models import LabourCost
from .tasks import import_labour_cost_from_xlsx


class LabourCostList(ProposalViewMixin):
    """
    View for labor cost master data.
    """

    render_template_name = "proposal/labour_cost/labor_cost_list.html"


class LabourCostListAjaxView(DataTableMixin, View):
    """
    DataTable for labor cost master data.
    """

    model = LabourCost
    queryset = LabourCost.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        # If a search term, filter the query
        if self.search:
            return qs.filter(
                Q(labour_task__icontains=self.search)
                | Q(local_labour_rates__icontains=self.search)
                | Q(out_of_town_labour_rates__icontains=self.search)
                | Q(description__icontains=self.search)
                | Q(notes__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "labour_task": o.labour_task,
                    "local_labour_rates": o.local_labour_rates,
                    "out_of_town_labour_rates": o.out_of_town_labour_rates,
                    "description": o.description,
                    "notes": o.notes,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class LabourCostCreateFromCSVFormView(FormView):
    """
    View to import data from CSV or Excel files.
    """

    template_name = "proposal/labour_cost/import_labour_cost.html"
    form_class = ImportLabourCostCSVForm

    def form_valid(self, form):
        """
        Handle a valid form submission.

        :param form: The submitted form instance with validated data.
        :return: JsonResponse indicating success or an error.
        """
        csv_file = form.cleaned_data["csv_file"]
        # print("File size:", csv_file.size)  # Log the size of the uploaded file for debugging

        response = import_labour_cost_from_xlsx(csv_file)

        if "error" in response:
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        return JsonResponse(
            {
                "redirect": reverse("proposal_app:labour_cost:labour-cost-list"),
                "message": "Labour Cost imported successfully!",
                "status": "success",
                "code": 200,
            }
        )

    def form_invalid(self, form):
        """
        Handle an invalid form submission.

        :param form: The submitted form instance with errors.
        :return: Response with the rendered form and a status code.
        """
        return self.render_to_response(self.get_context_data(form=form), status=201)
