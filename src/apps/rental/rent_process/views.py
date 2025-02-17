from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import get_template
from django.urls import reverse

from apps.mixin import CustomDataTableMixin, FormViewMixin, WarehouseViewMixin
from apps.rental.rent_process import forms, tasks
from apps.rental.rent_process.models import Delivery, Order, RecurringOrder, ReturnOrder


# Create your views here.
class OrderListView(WarehouseViewMixin):
    """View class for rendering the list of warehouses."""

    render_template_name = "rental/rent_process/order_list.html"


class RentalOrderImportView(FormViewMixin):
    """
    Import data from CSV or Excel files.
    """

    template_name = "rental/rent_process/import_order.html"
    form_class = forms.ImportOrderCSVForm

    def form_valid(self, form):
        """Handle valid form submission and import products."""
        csv_file = form.cleaned_data["csv_file"]
        response = tasks.import_order_from_file(csv_file)

        if "error" in response:
            form.add_error("csv_file", response["error"])
            return self.render_to_response(self.get_context_data(form=form), status=201)

        return JsonResponse(
            {
                "redirect": reverse("rental:rent_process:order-list-ajax"),
                "message": "Order imported successfully!",
                "status": "success",
                "code": 200,
                "skipped_records": response["skipped_records"],
            }
        )

    def form_invalid(self, form):
        """Handle invalid form submission."""
        return self.render_to_response(self.get_context_data(form=form), status=201)


class OrderListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Warehouse in a data table format."""

    def get_queryset(self):
        """Returns a queryset of orders."""
        return Order.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(order_id__icontains=self.search)
                | Q(customer__name__icontains=self.search)
                | Q(rent_amount__icontains=self.search)
                | Q(account_manager__name__icontains=self.search)
                | Q(repeat_start_date__icontains=self.search)
                | Q(repeat_end_date__icontains=self.search)
                | Q(updated_at__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            delivery_ids = list(Delivery.objects.filter(order=o).values_list("delivery_id", flat=True))
            if o.repeat_type in ["Weekly", "Monthly", "Yearly", "Recurring"]:
                recurring = "Recurring"
            else:
                recurring = "One Time"
            data.append(
                {
                    "order_id": self._get_order_id(o),
                    "delivery_id": self._get_delivery_id(delivery_ids) if delivery_ids else " - ",
                    "status": self._get_estimation_stage(delivery_ids) if delivery_ids else " - ",
                    "customer": o.customer.name,
                    "order_amount": o.rent_amount,
                    "account_manager": o.account_manager.name,
                    "start_date": o.rental_start_date.strftime("%d/%m/%Y") if o.rental_start_date else " - ",
                    "end_date": o.rental_end_date.strftime("%d/%m/%Y") if o.rental_end_date else " - ",
                    "recurring_type": recurring,
                    "last_updated_date": o.updated_at.strftime("%d/%m/%Y"),
                    "actions": self._get_actions(o),
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """Get a dictionary of data."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

    def _get_estimation_stage(self, delivery_ids):
        """
        Render the estimation stages for the deliveries using a partial template.
        """
        t = get_template("rental/rent_process/estimation_stages.html")
        deliveries = Delivery.objects.filter(delivery_id__in=delivery_ids)
        return t.render({"deliveries": deliveries})

    def _get_order_id(self, obj):
        """
        Create a link to the Opportunity detail page with the document number.
        """
        detail_url = reverse(
            "rental:rent_process:order-detail",
            kwargs={"order_id": obj.order_id},
        )
        return f'<a href="{detail_url}">{obj.order_id}</a>'

    def _get_delivery_id(self, delivery_ids):
        """
        Create links to the Opportunity detail pages for all delivery IDs in a table format.
        """
        table = '<table class="table bordered">'
        table += "<tbody>"
        for delivery_id in delivery_ids:
            edit_url = reverse(
                "rental:rent_process:delivery-detail",
                kwargs={"delivery_id": delivery_id},
            )
            table += f'<tr><td><a href="{edit_url}">{delivery_id}</a></td></tr>'
        table += "</tbody></table>"
        return table

    def _get_actions(self, obj):
        """
        Generate action buttons for the Opportunity with a link to the detail page.
        """
        t = get_template("rental/rent_process/rent_process_action.html")

        time_line_url = reverse(
            "rental:rent_process:order-detail",
            kwargs={"order_id": obj.order_id},
        )
        delete_url = reverse(
            "rental:rent_process:order-detail",
            kwargs={"order_id": obj.order_id},
        )
        process_url = reverse(
            "rental:rent_process:order-detail",
            kwargs={"order_id": obj.order_id},
        )
        return t.render(
            {
                "delete_url": delete_url,
                "process_url": process_url,
                "time_line_url": time_line_url,
                "o": obj,
                "request": self.request,
            }
        )


class OrderDetailview(FormViewMixin):
    pass


class DeliveryDetailview(FormViewMixin):
    pass


# class RecurringOrderListAjaxView(CustomDataTableMixin):
#     """AJAX view for listing Warehouse in a data table format."""

#     def _get_recurring_order_id(self, obj):
#         """
#         Create a link to the Opportunity detail page with the document number.
#         """
#         edit_url = reverse(
#             "rental:rent_process:reccuring-order-detail",
#             kwargs={"recurring_order_id": obj.recurring_order_id},
#         )
#         return f'<a href="{edit_url}">{obj.recurring_order_id}</a>'

#     def _get_orignal_order_id(self, obj):
#         """
#         Create a link to the Opportunity detail page with the document number.
#         """
#         edit_url = reverse(
#             "rental:rent_process:order-detail",
#             kwargs={"order_id": obj},
#         )
#         return f'<a href="{edit_url}">{obj}</a>'

#     def _get_actions(self, obj):
#         """
#         Generate action buttons for the Opportunity with a link to the detail page.
#         """
#         t = get_template("rental/rent_process/rent_process_action.html")

#         edit_url = reverse(
#             "rental:rent_process:reccuring-order-detail",
#             kwargs={"recurring_order_id": obj.recurring_order_id},
#         )
#         delete_url = reverse(
#             "rental:rent_process:reccuring-order-detail",
#             kwargs={"recurring_order_id": obj.recurring_order_id},
#         )
#         return t.render(
#             {
#                 "edit_url": edit_url,
#                 "delete_url": delete_url,
#                 "o": obj,
#                 "request": self.request,
#             }
#         )

#     def get_queryset(self):
#         """Returns a queryset of orders."""
#         return RecurringOrder.objects.all()

#     def filter_queryset(self, qs):
#         """Return the list of items for this view."""
#         if self.search:
#             return qs.filter(
#                 Q(recurring_order_id__icontains=self.search) |
#                 Q(order__order_id__icontains=self.search) |
#                 Q(order__customer__name__icontains=self.search) |
#                 Q(order__rent_amount__icontains=self.search) |
#                 Q(order__account_manager__name__icontains=self.search) |
#                 Q(order__repeat_start_date__icontains=self.search) |
#                 Q(order__repeat_end_date__icontains=self.search)
#             )
#         return qs

#     def prepare_results(self, qs):
#         """Create row data for datatables."""
#         data = []
#         for o in qs:
#             number_of_orders = o.order.calculate_total_repeat_orders()
#             data.append(
#                 {
#                     "order_id": self._get_orignal_order_id(o.order.order_id),
#                     "recurring_order_id": self._get_recurring_order_id(o),
#                     "customer": o.order.customer.name,
#                     "order_amount": o.order.rent_amount,
#                     "account_manager": o.order.account_manager.name,
#                     "recurring_type": o.order.repeat_type,
#                     "repeat_start_date": o.order.repeat_start_date.strftime("%d/%m/%Y") if o.order.repeat_start_date else None,
#                     "repeat_end_date": o.order.repeat_end_date.strftime("%d/%m/%Y") if o.order.repeat_end_date else None,
#                     "number_of_orders": number_of_orders,
#                     "actions": self._get_actions(o),
#                 }
#             )
#         return data

#     def get(self, request, *args, **kwargs):
#         """Get a dictionary of data."""
#         context_data = self.get_context_data(request)
#         return JsonResponse(context_data)

# class ReturnOrderListAjaxView(CustomDataTableMixin):
#     """AJAX view for listing Warehouse in a data table format."""

#     def _get_actions(self, obj):
#         """
#         Generate action buttons for the Opportunity with a link to the detail page.
#         """
#         t = get_template("rental/rent_process/rent_process_action.html")

#         time_line_url = reverse(
#             "rental:rent_process:order-detail",
#             kwargs={"order_id": obj.order.order_id}
#         )
#         edit_url = reverse(
#             "rental:rent_process:order-detail",
#             kwargs={"order_id": obj.order.order_id}
#         )
#         process_url = reverse(
#             "rental:rent_process:order-detail",
#             kwargs={"order_id": obj.order.order_id}
#         )
#         return t.render(
#             {
#                 "time_line_url": time_line_url,
#                 "edit_url": edit_url,
#                 "process_url": process_url,
#                 "o": obj,
#                 "request": self.request,
#             }
#         )

#     def _get_estimation_stage(self, delivery_ids):
#         """
#         Render the estimation stages for the deliveries using a partial template.
#         """
#         t = get_template("rental/rent_process/estimation_stages.html")
#         deliveries = Delivery.objects.filter(delivery_id__in=delivery_ids)
#         return t.render({"deliveries": deliveries})

#     def _get_order_id(self, obj):
#         """
#         Create a link to the Opportunity detail page with the document number.
#         """
#         edit_url = reverse(
#             "rental:rent_process:order-detail",
#             kwargs={"order_id": obj.order_id},
#         )
#         return f'<a href="{edit_url}">{obj.order_id}</a>'

#     def get_queryset(self):
#         """Returns a queryset of orders."""
#         return ReturnOrder.objects.all()

#     def filter_queryset(self, qs):
#         """Return the list of items for this view."""
#         if self.search:
#             return qs.filter(
#                 Q(order__order_id__icontains=self.search) |
#                 Q(delivery__delivery_id__icontains=self.search) |
#                 Q(delivery__delivery_status__icontains=self.search) |
#                 Q(order__customer__name__icontains=self.search) |
#                 Q(order__account_manager__name__icontains=self.search) |
#                 Q(order__repeat_start_date__icontains=self.search) |
#                 Q(order__repeat_end_date__icontains=self.search) |
#                 Q(order__updated_at__icontains=self.search)
#             )
#         return qs

#     def prepare_results(self, qs):
#         """Create row data for datatables."""
#         data = []
#         for o in qs:
#             delivery_ids = list(ReturnOrder.objects.filter(delivery=o.delivery.delivery_id).values_list('delivery_id', flat=True))
#             data.append(
#                 {
#                     "order_id": self._get_order_id(o.order),
#                     "delivery_id": o.delivery.delivery_id,
#                     "status": self._get_estimation_stage(delivery_ids),
#                     "customer": o.order.customer.name,
#                     "account_manager": o.order.account_manager.name,
#                     "start_date": o.order.rental_start_date.strftime("%d/%m/%Y") if o.order.rental_start_date else " - ",
#                     "end_date": o.order.rental_end_date.strftime("%d/%m/%Y") if o.order.rental_end_date else " - ",
#                     "last_updated_date": o.updated_at.strftime("%d/%m/%Y"),
#                     "actions": self._get_actions(o),
#                 }
#             )
#         return data

#     def get(self, request, *args, **kwargs):
#         """Get a dictionary of data."""
#         context_data = self.get_context_data(request)
#         return JsonResponse(context_data)

# class RecurringOrderDetail(FormViewMixin):
#     pass
