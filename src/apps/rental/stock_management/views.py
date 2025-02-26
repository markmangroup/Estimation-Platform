import datetime
import json
from django import forms
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.urls import reverse
from django.views import View
from apps.mixin import CustomDataTableMixin, FormViewMixin, UpdateViewMixin, WarehouseViewMixin
from apps.rental.product.models import RentalProduct
from apps.rental.stock_management import tasks
from apps.rental.stock_management import forms
from apps.rental.stock_management.forms import StockAdjustmentForm
from apps.rental.stock_management.models import StockAdjustment
from django.template.loader import get_template
from django.template.loader import render_to_string


# Create your views here.
class StockManagementListView(WarehouseViewMixin):
    """
    View class for rendering the list of warehouse products.
    """

    render_template_name = "rental/stock_managment/stock_managment.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context["equipment_ids"] = StockAdjustment.objects.values_list(
            "rental_product__equipment_id", flat=True
        ).distinct()
        context["equipment_material_groups"] = StockAdjustment.objects.values_list(
            "rental_product__equipment_material_group", flat=True
        ).distinct()
        context["equipment_names"] = StockAdjustment.objects.values_list(
            "rental_product__equipment_name", flat=True
        ).distinct()
        context["locations"] = StockAdjustment.objects.values_list("location", flat=True).distinct()
        return context


class StockManagementListAjaxView(CustomDataTableMixin):
    """
    A view that provides an AJAX response for listing stock adjustments in the rental product management system.
    This view returns data for the DataTable interface, allowing dynamic filtering by equipment ID, material group,
    equipment name, and location.
    """

    model = StockAdjustment

    def get_queryset(self):
        """Returns a list of rental products."""

        qs = StockAdjustment.objects.all()

        equipment_ids = self.request.GET.getlist("equipment_id[]", [])
        if equipment_ids:
            qs = qs.filter(rental_product__equipment_id__in=equipment_ids)

        material_groups = self.request.GET.getlist("equipment_material_group[]", [])
        if material_groups:
            qs = qs.filter(rental_product__equipment_material_group__in=material_groups)

        equipment_names = self.request.GET.getlist("equipment_name[]", [])
        if equipment_names:
            qs = qs.filter(rental_product__equipment_name__in=equipment_names)

        locations = self.request.GET.getlist("location[]", [])
        if locations:
            qs = qs.filter(location__in=locations)

        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""

        if self.search:
            return qs.filter(
                Q(quantity__icontains=self.search)
                | Q(location__icontains=self.search)
                | Q(rental_product__equipment_id__icontains=self.search)
                | Q(rental_product__equipment_material_group__icontains=self.search)
                | Q(rental_product__equipment_name__icontains=self.search)
            )
        return qs

    def _get_actions(self, obj):
        """Get Action buttons for table."""

        t = get_template("rental/stock_managment/action_custom_url.html")

        edit_url = reverse(
            "rental:stock_management:rental-stock-management-edit",
            kwargs={"pk": obj.id},
        )
        print("edit_url: ", edit_url)

        return t.render(
            {
                "edit_url": edit_url,
                "o": obj,
                "request": self.request,
            }
        )

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            data.append(
                {
                    "equipment_id": o.rental_product.equipment_id if o.rental_product else None,
                    "equipment_material_group": o.rental_product.equipment_material_group if o.rental_product else None,
                    "equipment_name": o.rental_product.equipment_name if o.rental_product else None,
                    "quantity": o.quantity,
                    "location": o.location,
                    "actions": self._get_actions(o),
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """Get a dictionary of data."""
        context_data = self.get_context_data(request)
        print("context_data: ", context_data)
        return JsonResponse(context_data)


class StockManagementEditView(UpdateViewMixin):
    """
    View for editing stock adjustments. This view handles the updating of stock adjustment data
    and provides JSON responses for success or failure after form submission.

    """

    model = StockAdjustment
    form_class = StockAdjustmentForm
    template_name = "rental/stock_managment/stock_edit.html"
    context_object_name = "stock_adjustment"

    def get_object(self):
        return get_object_or_404(StockAdjustment, pk=self.kwargs["pk"])

    def form_valid(self, form):
        self.object = form.save(commit=True)
        response_data = {
            "success": True,
            "message": "Stock Updated successfully.",
        }
        return JsonResponse(response_data)

    def form_invalid(self, form):
        response_data = {
            "success": False,
            "message": "Form validation failed. Please correct the errors.",
            "errors": form.errors,
        }
        return JsonResponse(response_data, status=400)


class MassStockUploadView(FormViewMixin):
    """
    View for handling the mass upload of stock adjustments from CSV or Excel files.
    The file is processed, and stock adjustments are imported based on the provided data.
    """

    template_name = "rental/stock_managment/import_mass_stock.html"
    form_class = forms.ImportStockAdjustmentForm

    def form_valid(self, form):
        """Handle valid form submission and import products."""

        csv_file = form.cleaned_data["csv_file"]
        response = tasks.import_stock_adjustment_from_file(csv_file)

        if "error" in response:
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        records = response.get("records", [])
        modal_content = self.prepare_modal_content(records)

        return JsonResponse(
            {
                "status": "success",
                "records": records,
                "modal_content": modal_content,
                "message": "File uploaded successfully and processed.",
                "skipped_records": response["skipped_records"],
            }
        )

    def form_invalid(self, form):
        """Handle invalid form submission."""
        return self.render_to_response(self.get_context_data(form=form), status=201)

    def prepare_modal_content(self, records):
        """
        Prepare the modal content (table rows) dynamically from the records.

        Returns:
            str: Rendered HTML string for the modal content, displaying the processed records.
        """
        reason_choices = [choice[1] for choice in StockAdjustment.REASON_CHOICES]
        context = {"records": []}

        for record in records:
            id = record.get("Internal ID")
            if not id:
                continue

            try:
                rental_product = RentalProduct.objects.get(equipment_id=id)
            except RentalProduct.DoesNotExist:
                continue

            stock_adjustments = StockAdjustment.objects.filter(rental_product=rental_product)
            current_quantity = sum([adjustment.quantity for adjustment in stock_adjustments])

            new_quantity = record.get("Quantity")
            if new_quantity > current_quantity:
                plus = new_quantity - current_quantity
                minus = 0
            elif current_quantity > new_quantity:
                minus = current_quantity - new_quantity
                plus = 0
            else:
                plus = 0
                minus = 0
                new_quantity = 0
            date_str = record.get("Date")

            if date_str:
                try:
                    date_obj = datetime.datetime.strptime(date_str, "%d/%m/%y")
                    date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    # If date parsing fails, default to today's date
                    date = datetime.datetime.now().strftime("%Y-%m-%d")
            else:
                # If no date is provided, use today's date
                date = datetime.datetime.now().strftime("%Y-%m-%d")

            context["records"].append(
                {
                    "internal_id": record["Internal ID"],
                    "location": record["Location"],
                    "date": date,
                    "current_quantity": current_quantity,
                    "new_quantity": new_quantity,
                    "plus": plus,
                    "minus": minus,
                    "reason_choices": reason_choices,
                }
            )
        return render_to_string("rental/stock_managment/confirmation_mass_stock.html", context)


class SaveMassStockAdjustmentsView(View):
    def post(self, request, *args, **kwargs):
        try:
            records = json.loads(request.POST.get("records"))
            print("records: ", records)

            for record in records:
                internal_id = record["internal_id"]

                rental_product = RentalProduct.objects.get(equipment_id=internal_id)
                location = record.get("location", "")
                reason = record.get("reason", "other")
                comment = record.get("comment", "")
                date = record.get("date", None)
                quantity_str = record.get("quantity", "")

                if date:
                    date = date.strip("“”")
                    datetime.datetime.strptime(date, "%Y-%m-%d")

                if not quantity_str or not quantity_str.isdigit():
                    quantity = 0
                else:
                    quantity = int(quantity_str)

                stock_adjustments = StockAdjustment.objects.filter(rental_product=rental_product)

                if stock_adjustments.exists():
                    for stock_adjustment in stock_adjustments:
                        stock_adjustment.quantity = quantity
                        stock_adjustment.comment = comment
                        stock_adjustment.reason = reason
                        stock_adjustment.date = date
                        stock_adjustment.location = location
                        stock_adjustment.save()
                else:
                    stock_adjustment = StockAdjustment.objects.create(
                        rental_product=rental_product,
                        quantity=quantity,
                        reason=reason,
                        comment=comment,
                        location=location,
                        date=date,
                    )
                    print(f"Stock Adjustment created: {stock_adjustment}")

            return JsonResponse({"status": "success", "message": "Stock adjustments have been saved successfully."})

        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error saving stock adjustments: {str(e)}"})
