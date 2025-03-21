import datetime
import json
from typing import Any, Dict

from django.contrib import messages
from django.db.models import Q, Sum
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template, render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from isodate import parse_date
from apps.rental.account_manager.models import AccountManager
from apps.rental.warehouse.models import RentalWarehouse

from apps.constants import ERROR_RESPONSE, LOGGER
from apps.mixin import (
    AdminMixin,
    CreateViewMixin,
    CustomDataTableMixin,
    DetailView,
    FormViewMixin,
    UpdateViewMixin,
    View,
    ViewMixin,
    WarehouseDetailViewMixin,
    WarehouseViewMixin,
)
from apps.rental.customer.models import RentalCustomer
from apps.rental.product.models import RentalProduct
from apps.rental.rent_process import forms, tasks
from apps.rental.rent_process.models import (
    Delivery,
    Document,
    Order,
    OrderFormPermissionModel,
    OrderItem,
    RecurringOrder,
    ReturnDelivery,
    ReturnDeliveryItem,
    ReturnOrder,
)
from apps.rental.stock_management.models import StockAdjustment

from .forms import (
    OrderForm,
    OrderFormPermissionForm,
    OrderItemForm,
    OrderItemFormSet,
    UpdateOrderForm,
    UpdateOrderItemForm,
)


class OrderListView(WarehouseViewMixin):
    """View class for rendering the list of order."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["form"] = OrderForm
            context["order_item_formset"] = OrderItemFormSet(self.request.POST)
        else:
            context["form"] = OrderForm
            formset = OrderItemFormSet()
            for form in formset.forms:
                form.fields["product"].queryset = RentalProduct.objects.all()
            context["order_item_formset"] = formset
        context["permission"] = OrderFormPermissionModel.objects.all()
        return context

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
            qs = qs.filter(
                Q(order_id__icontains=self.search)
                | Q(customer__name__icontains=self.search)
                | Q(account_manager__name__icontains=self.search)
                | Q(delivery_order__delivery_status__icontains=self.search)
            ).distinct()
        return qs

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            delivery_ids = list(
                Delivery.objects.filter(order=o).values_list("unique_delivery_id", flat=True).distinct()
            )
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
        deliveries = Delivery.objects.filter(unique_delivery_id__in=delivery_ids).distinct("unique_delivery_id")
        return t.render({"deliveries": deliveries})

    def _get_order_id(self, obj):
        """
        Create a link to the Opportunity detail page with the document number.
        """
        detail_url = reverse(
            "rental:rent_process:order-overview",
            kwargs={"order_id": obj.order_id},
        )
        return f'<a href="{detail_url}">{obj.order_id}</a>'

    def _get_delivery_id(self, delivery_ids):
        """
        Create links to the Opportunity detail pages for all delivery IDs in a table format.
        """
        order_id = (
            Delivery.objects.filter(unique_delivery_id__in=delivery_ids)
            .values_list("order__order_id", flat=True)
            .distinct()
            .first()
        )
        table = '<table class="table bordered">'
        table += "<tbody>"
        for delivery_id in delivery_ids:
            edit_url = reverse(
                "rental:rent_process:order-process",
                kwargs={"order_id": order_id},
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
            "rental:rent_process:order-process",
            kwargs={"order_id": obj.order_id},
        )
        delete_url = reverse(
            "rental:rent_process:order-delete",
        )
        process_url = reverse(
            "rental:rent_process:order-process",
            kwargs={"order_id": obj.order_id},
        )
        hx_target = ""
        data_target = ""
        # edit_url = reverse(
        #     "rental:rent_process:order-update",
        #     kwargs={"pk": obj.pk},
        # )

        return t.render(
            {
                "delete_url": delete_url,
                # "edit_url": edit_url,
                "process_url": process_url,
                "time_line_url": time_line_url,
                "hx_target": hx_target,
                "order_id": obj.order_id,
                "data_target": data_target,
                "o": obj,
                "request": self.request,
                "class": "rent-process-delete-btn",
                "title": obj.order_id,
            }
        )


class OrderOverview(WarehouseDetailViewMixin):
    """
    View to display detailed information about an Opportunity.
    """

    model = Order
    render_template_name = "rental/rent_process/order_overview.html"
    context_object_name = "orders"

    def get_object(self, queryset=None):
        """
        Override to retrieve the Opportunity object using document_number.
        """
        order_id = self.kwargs.get("order_id")
        return get_object_or_404(Order, order_id=order_id)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Returns a dictionary of the context object.
        """
        context = super().get_context_data(**kwargs)

        order_id = self.kwargs.get("order_id")
        order = Order.objects.get(order_id=order_id)
        delivery = Delivery.objects.filter(order__order_id=order_id)
        recurring_order = RecurringOrder.objects.filter(order__order_id=order_id)
        order_items = OrderItem.objects.filter(order__order_id=order_id)
        rent_details = []
        for item in order_items:
            quantity = item.quantity
            price = item.per_unit_price
            start_date = item.order.rental_start_date
            end_date = item.order.rental_end_date
            rent = tasks.calculation_of_rent_amount(quantity, price, start_date, end_date)
            rent_details.append({"item_id": item.id, "rent": rent})

        context["order"] = order
        context["deliverys"] = delivery
        context["recurring_order"] = recurring_order
        context["order_items"] = order_items
        context["rent_details"] = rent_details
        print(f"└─ ➡ ┌─ context: {context}")
        return context


class DeliveryDetailview(FormViewMixin):
    pass


class OrderProcessview(WarehouseDetailViewMixin):
    model = Order
    render_template_name = "rental/orders/rental_order.html"

    def get_object(self, queryset=None):
        order_id = self.kwargs.get("order_id")
        return get_object_or_404(Order, order_id=order_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get("order_id")
        order_obj = Order.objects.filter(order_id=order_id).first()
        deliveries = Delivery.objects.filter(order__order_id=order_id).select_related("product")
        delivery_dict = {}

        for delivery in deliveries:
            if delivery.unique_delivery_id:
                if delivery.unique_delivery_id not in delivery_dict:
                    delivery_dict[delivery.unique_delivery_id] = {
                        "products": [],
                        "total_qty": 0,
                        "contract_start_date": delivery.contract_start_date,
                        "delivery_date": delivery.delivery_date,
                        "delivery_status": delivery.delivery_status,
                    }

                delivery_dict[delivery.unique_delivery_id]["products"].append(
                    {
                        "equipment_name": delivery.product.equipment_name,
                        "equipment_id": delivery.product.equipment_id,
                        "quantity": delivery.delivery_qty,
                    }
                )
                delivery_dict[delivery.unique_delivery_id]["total_qty"] += delivery.delivery_qty

        context["delivery_dict"] = delivery_dict
        context["stage"] = order_obj.order_status
        context["order_obj"] = order_obj

        return context


def overview_model(request, order_id):
    context = {}
    order = Order.objects.get(order_id=order_id)
    delivery = Delivery.objects.filter(order__order_id=order_id)
    recurring_order = RecurringOrder.objects.filter(order__order_id=order_id)
    order_items = OrderItem.objects.filter(order__order_id=order_id)
    rent_details = []
    for item in order_items:
        quantity = item.quantity
        price = item.per_unit_price
        start_date = item.order.rental_start_date
        end_date = item.order.rental_end_date
        rent = tasks.calculation_of_rent_amount(quantity, price, start_date, end_date)
        rent_details.append({"item_id": item.id, "rent": rent})

    context["order"] = order
    context["deliverys"] = delivery
    context["recurring_order"] = recurring_order
    context["order_items"] = order_items
    context["rent_details"] = rent_details
    html = render_to_string("rental/rent_process/order_detail_overview.html", context, request=request)
    return JsonResponse({"html": html})


def create_delivery_modal(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    order_items = OrderItem.objects.filter(order=order)
    pending_order_items = []

    for item in order_items:
        delivered_qty = (
            Delivery.objects.filter(order=order, product=item.product).aggregate(Sum("delivery_qty"))[
                "delivery_qty__sum"
            ]
            or 0
        )
        remaining_qty = item.quantity - delivered_qty

        if remaining_qty > 0:
            pending_order_items.append({"order_item": item, "remaining_qty": remaining_qty})

    context = {"order": order, "order_items": pending_order_items}
    html = render_to_string("rental/rent_process/delivery_table.html", context, request=request)
    return JsonResponse({"html": html})


class DeliveryCreateView(CreateViewMixin):
    form_class = forms.DeliveryForm

    def form_valid(self, form):
        order_number = self.request.POST.get("order")

        try:
            order = Order.objects.get(order_id=order_number)
        except Order.DoesNotExist:
            return JsonResponse({"success": False, "error": "Order not found"}, status=404)

        pickup_date = form.cleaned_data["pickup_date"]
        delivery_date = form.cleaned_data["delivery_date"]
        shipping_carrier = form.cleaned_data["shipping_carrier"]
        pickup_site = form.cleaned_data["pickup_site"]
        delivery_site = form.cleaned_data["delivery_site"]
        products_json = self.request.POST.get("products")
        po_number = form.cleaned_data["po_number"]

        try:
            products = json.loads(products_json)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid product data format"}, status=400)

        unique_delivery_id = tasks.generate_delivery_id(order)
        for product in products:
            product_id = product.get("productId")
            quantity = product.get("quantity")
            try:
                product_id = int(product_id)
                quantity = int(quantity)
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid product ID or quantity"}, status=400)

            try:
                order_item = OrderItem.objects.get(id=product_id, order=order)
            except OrderItem.DoesNotExist:
                return JsonResponse(
                    {"success": False, "error": f"OrderItem with ID {product_id} not found for Order {order_number}"},
                    status=404,
                )

            delivery = Delivery.objects.create(
                unique_delivery_id=unique_delivery_id,
                po_number=po_number if po_number else None,
                order=order,
                product=order_item.product,
                delivery_qty=quantity,
                pickup_date=pickup_date,
                delivery_date=delivery_date,
                shipping_carrier=shipping_carrier,
                pickup_site=pickup_site,
                delivery_site=delivery_site,
            )
            delivery.save()

        return JsonResponse({"message": "Delivery Created Successfully!"}, status=200)

    def form_invalid(self, form):
        print(form.errors)
        return JsonResponse({"success": False, "errors": form.errors}, status=400)


class RecurringOrderListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Warehouse in a data table format."""

    def _get_recurring_order_id(self, obj):
        """
        Create a link to the Opportunity detail page with the document number.
        """
        recurring_order = RecurringOrder.objects.get(recurring_order_id=obj.recurring_order_id)
        order_id = recurring_order.order.order_id if recurring_order.order else None
        edit_url = reverse(
            "rental:rent_process:order-process",
            kwargs={"order_id": order_id},
        )
        return f'<a href="{edit_url}">{obj.recurring_order_id}</a>'

    def _get_orignal_order_id(self, obj):
        """
        Create a link to the Opportunity detail page with the document number.
        """
        edit_url = reverse(
            "rental:rent_process:order-overview",
            kwargs={"order_id": obj},
        )
        return f'<a href="{edit_url}">{obj}</a>'

    def _get_actions(self, obj):
        """
        Generate action buttons for the Opportunity with a link to the detail page.
        """
        t = get_template("rental/rent_process/rent_process_action.html")

        edit_url = reverse(
            "rental:rent_process:reccuring-order-edit",
            kwargs={"pk": obj.recurring_order_id},
        )
        delete_url = reverse("rental:rent_process:reccuring-order-delete")
        data_target = "#update_recurring_order"
        hx_target = "#update_recurring_order_body"
        return t.render(
            {
                "edit_url": edit_url,
                "delete_url": delete_url,
                "o": obj,
                "data_target": data_target,
                "hx_target": hx_target,
                "request": self.request,
                "class": "rent-process-delete-btn",
                "title": obj.recurring_order_id,
            }
        )

    def get_queryset(self):
        """Returns a queryset of orders."""
        return RecurringOrder.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(recurring_order_id__icontains=self.search)
                | Q(order__order_id__icontains=self.search)
                | Q(order__customer__name__icontains=self.search)
                | Q(order__rent_amount__icontains=self.search)
                | Q(order__account_manager__name__icontains=self.search)
                | Q(order__repeat_start_date__icontains=self.search)
                | Q(order__repeat_end_date__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            number_of_orders = RecurringOrder.objects.filter(order=o.order).count()
            data.append(
                {
                    "order_id": self._get_orignal_order_id(o.order.order_id),
                    "recurring_order_id": self._get_recurring_order_id(o),
                    "customer": o.order.customer.name,
                    "order_amount": o.order.rent_amount,
                    "account_manager": o.order.account_manager.name,
                    "recurring_type": o.order.repeat_type,
                    "repeat_start_date": (o.start_date.strftime("%d/%m/%Y") if o.start_date else None),
                    "repeat_end_date": (o.end_date.strftime("%d/%m/%Y") if o.end_date else None),
                    "number_of_orders": number_of_orders,
                    "actions": self._get_actions(o),
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """Get a dictionary of data."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class ReturnOrderListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Warehouse in a data table format."""

    def _get_actions(self, obj):
        """
        Generate action buttons for the Opportunity with a link to the detail page.
        """
        t = get_template("rental/rent_process/rent_process_action.html")
        time_line_url = None
        if obj.delivery:
            time_line_url = reverse(
                "rental:rent_process:order-history", kwargs={"delivery_id": obj.delivery.delivery_id}
            )
        else:
            time_line_url = ""
        edit_url = reverse("rental:rent_process:return-order-edit", kwargs={"pk": obj.order.order_id})
        process_url = reverse("rental:rent_process:order-process", kwargs={"order_id": obj.order.order_id})
        data_target = "#update_return_order"
        hx_target = "#update_return_order_body"
        return t.render(
            {
                "time_line_url": time_line_url,
                "return_edit_url": edit_url,
                "process_url": process_url,
                "o": obj,
                "order_id": obj.order.order_id,
                "data_target": data_target,
                "hx_target": hx_target,
                "request": self.request,
            }
        )

    def _get_estimation_stage(self, delivery_ids):
        """
        Render the estimation stages for the deliveries using a partial template.
        """
        if delivery_ids:
            t = get_template("rental/rent_process/estimation_stages.html")
            deliveries = Delivery.objects.filter(delivery_id__in=delivery_ids)
            return t.render({"deliveries": deliveries})
        else:
            return ""

    def _get_order_id(self, obj):
        """
        Create a link to the Opportunity detail page with the document number.
        """
        edit_url = reverse(
            "rental:rent_process:order-overview",
            kwargs={"order_id": obj.order_id},
        )
        return f'<a href="{edit_url}">{obj.order_id}</a>'

    def get_queryset(self):
        """Returns a queryset of orders."""
        return ReturnOrder.objects.all()

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(order__order_id__icontains=self.search)
                | Q(delivery__delivery_id__icontains=self.search)
                | Q(delivery__delivery_status__icontains=self.search)
                | Q(order__customer__name__icontains=self.search)
                | Q(order__account_manager__name__icontains=self.search)
                | Q(order__repeat_start_date__icontains=self.search)
                | Q(order__repeat_end_date__icontains=self.search)
                | Q(order__updated_at__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            if o.delivery:
                delivery_ids = list(
                    ReturnOrder.objects.filter(delivery=o.delivery.delivery_id).values_list("delivery_id", flat=True)
                )
            else:
                delivery_ids = None
            data.append(
                {
                    "order_id": self._get_order_id(o.order),
                    "delivery_id": o.delivery.unique_delivery_id if o.delivery else "",
                    "status": self._get_estimation_stage(delivery_ids),
                    "customer": o.order.customer.name,
                    "account_manager": o.order.account_manager.name,
                    "start_date": (
                        o.order.rental_start_date.strftime("%d/%m/%Y") if o.order.rental_start_date else " - "
                    ),
                    "end_date": o.order.rental_end_date.strftime("%d/%m/%Y") if o.order.rental_end_date else " - ",
                    "last_updated_date": o.updated_at.strftime("%d/%m/%Y"),
                    "actions": self._get_actions(o),
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """Get a dictionary of data."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class RecurringOrderOverview(FormViewMixin):
    pass


class RecurringOrderDelete(AdminMixin, View):
    """
    View for delete the user objects.
    """

    def post(self, request):
        order_id = request.POST.get("id")
        recurring_order = RecurringOrder.objects.filter(recurring_order_id=order_id)
        if recurring_order.exists():
            recurring_order.delete()
            return JsonResponse({"code": "200", "message": "Recurring Order Deleted Successfully."})
        return JsonResponse({"code": "404", "message": "Recurring Order not found."})


class RecurringOrderEdit(UpdateViewMixin):
    model = RecurringOrder
    form_class = forms.RecurringOrderEditForm
    template_name = "rental/rent_process/edit_recurring_order.html"
    context_object_name = "recurring_order"

    def get_initial(self):
        initial_data = super().get_initial()
        order = self.object.order

        initial_data["customer"] = order.customer.name
        initial_data["pick_up_location"] = order.pick_up_location
        initial_data["rental_start_date"] = order.rental_start_date
        order_items = order.orders.all()

        initial_data["no_of_product"] = sum(item.quantity for item in order_items)
        initial_data["rent_amount"] = order.rent_amount
        initial_data["repeat_type"] = order.repeat_type

        if order.repeat_start_date and order.repeat_end_date:
            repeat_date_range = (
                f"{order.repeat_start_date.strftime('%Y-%m-%d')} - {order.repeat_end_date.strftime('%Y-%m-%d')}"
            )
            initial_data["repeat_date_range"] = repeat_date_range
        return initial_data

    def form_valid(self, form):
        self.object = form.save(commit=True)
        order = self.object.order
        if order:
            order.repeat_type = form.cleaned_data.get("order__repeat_type", order.repeat_type)
            repeat_date_range = form.cleaned_data.get("repeat_date_range", "")
            if repeat_date_range:
                try:
                    start_date_str, end_date_str = repeat_date_range.split(" - ")
                    order.repeat_start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
                    order.repeat_end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
                except ValueError:
                    messages.error(
                        self.request, "Invalid date range format. Please use the format 'YYYY-MM-DD - YYYY-MM-DD'."
                    )
                    return HttpResponse("error")
            order.save()
        messages.success(self.request, "Recurring Order updated successfully.")
        return HttpResponse("success")

    def form_invalid(self, form):
        return render(
            self.request, self.template_name, {"form": form, "recurring_order": self.get_object()}, status=201
        )


class OrderDelete(AdminMixin, View):
    """
    View for delete the user objects.
    """

    def post(self, request):
        order_id = request.POST.get("id")
        order = Order.objects.filter(order_id=order_id)
        if order.exists():
            order.delete()
            return JsonResponse({"code": "200", "message": "Order Deleted Successfully."})
        return JsonResponse({"code": "404", "message": "Order not found."})


class OrderCreate(CreateViewMixin):
    model = Order
    form_class = OrderForm
    template_name = "rental/rent_process/create_order.html"
    success_url = reverse_lazy("rental:rent_process_order_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        OrderItemFormSet = inlineformset_factory(Order, OrderItem, form=OrderItemForm, extra=1)
        rental_products = RentalProduct.objects.all()
        # rental_customers = RentalCustomer.objects.only("id", "name")
        if self.request.POST:
            context["order_item_formset"] = OrderItemFormSet(self.request.POST)
        else:
            formset = OrderItemFormSet()
            formset.empty_form.fields["product"].queryset = rental_products
            context["order_item_formset"] = formset

        # context["form"].fields["customer"].queryset = rental_customers
        context["permission"] = OrderFormPermissionModel.objects.first()
        return context

    def form_valid(self, form):
        order = form.save()

        OrderItemFormSet = inlineformset_factory(Order, OrderItem, form=OrderItemForm, extra=1)
        order_item_formset = OrderItemFormSet(self.request.POST, instance=order)
        if not order_item_formset.is_valid():
            return self.form_invalid(form)
        if order_item_formset.is_valid():
            order_item_formset.save()
            ReturnOrder.objects.create(order=order)
            is_recurring = self.request.POST.get("recurring_order")
            repeat_type = self.request.POST.get("repeat_type")
            repeat_value = self.request.POST.get("repeat_value", 0)
            repeat_start_date = order.repeat_start_date
            print("repeat_start_date: ", repeat_start_date)
            repeat_end_date = order.repeat_end_date
            print("repeat_end_date: ", repeat_end_date)

            if is_recurring == "on" and repeat_type and int(repeat_value) > 0 and repeat_start_date and repeat_end_date:
                start_date = repeat_start_date
                repeat_type = repeat_type.lower()
                print("repeat_type: ", repeat_type)
                print("start_date: ", start_date)

                if repeat_type == "weekly":
                    interval = 7
                elif repeat_type == "monthly":
                    interval = 30
                elif repeat_type == "yearly":
                    interval = 365
                else:
                    messages.error(self.request, "Invalid repeat type")
                    return self.form_invalid(form)

                last_end_date = repeat_end_date

                for i in range(int(repeat_value)):
                    next_start_date = start_date + datetime.timedelta(days=interval * i)
                    print("next_start_date: ", next_start_date)
                    next_end_date = next_start_date + datetime.timedelta(days=interval - 1)
                    print("next_end_date: ", next_end_date)

                    # Use the date object directly for repeat_end_date
                    defined_repeat_end = repeat_end_date
                    next_end_date = min(next_end_date, defined_repeat_end)

                    RecurringOrder.objects.create(
                        order=order,
                        start_date=next_start_date,
                        end_date=next_end_date,
                    )

                    print(f"Recurring Order {i+1}: {next_start_date} to {next_end_date}")
                    last_end_date = next_end_date

                print("Before order.repeat_end_date: ", order.repeat_end_date)
                order.rental_end_date = last_end_date
                order.repeat_end_date = last_end_date
                order.save()
                print("After order.repeat_end_date: ", order.repeat_end_date)
            total_rent_amount = sum((item.quantity or 0) * (item.per_unit_price or 0) for item in order.orders.all())
            order.rent_amount = total_rent_amount
            order.save()
            messages.success(self.request, "Order Created Successfully")
            return JsonResponse({"status": "success"})
        else:
            print("OrderItem FormSet Errors:===============+>>>>>fgfdgfd", order_item_formset.errors)
            return self.form_invalid(form)

    def form_invalid(self, form):
        print("OrderItem FormSet Errors:===============+>>>>>sdfsdfsdfdsfsdfd", form.errors)
        print("Selected Customer ID: ", form.cleaned_data.get("customer"))
        print("Selected Account Manager ID: ", form.cleaned_data.get("account_manager"))
        print("Selected Pick-up Location ID: ", form.cleaned_data.get("pick_up_location"))
        print("Incoming POST Data: ", self.request.POST)
        for i in form.errors:
            print('--------------->>i: ', i)

        messages.error(self.request, "Please correct the errors in the form.")
        return self.render_to_response(self.get_context_data(form=form))


class BaseOrderItemFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        # For extra forms (i >= initial_form_count), allow them to be empty.
        if i >= self.initial_form_count():
            form.empty_permitted = True
        return form


class OrderUpdateView(UpdateViewMixin):
    model = Order
    form_class = UpdateOrderForm
    template_name = "rental/rent_process/update_order.html"
    success_url = reverse_lazy("rental:rent_process_order_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_obj = self.object

        OrderItemFormSet = inlineformset_factory(
            Order, OrderItem, form=UpdateOrderItemForm, extra=0, can_delete=True, formset=BaseOrderItemFormSet
        )

        if self.request.POST:
            context["order_item_formset"] = OrderItemFormSet(self.request.POST, instance=order_obj)
        else:
            formset = OrderItemFormSet(instance=order_obj)

            for form in formset.forms:
                if form.instance.pk and form.instance.product:
                    form.fields["equipment_id"].queryset = RentalProduct.objects.filter(
                        Q(equipment_id=form.instance.product.equipment_id) | 
                        Q(equipment_id__in=RentalProduct.objects.values_list("equipment_id", flat=True)[:7])
                    )
                    form.fields["equipment_name"].queryset = RentalProduct.objects.filter(
                        Q(equipment_id=form.instance.product.equipment_id) |  # ✅ Compare using ID
                        Q(equipment_id__in=RentalProduct.objects.values_list("equipment_id", flat=True)[:7])
                    )


            context["order_item_formset"] = formset


        # Ensure Select2 fields retain selected values outside queryset limit
        if order_obj:
            context["selected_customer"] = order_obj.customer.id if order_obj.customer else None
            context["selected_account_manager"] = order_obj.account_manager.id if order_obj.account_manager else None
            context["selected_pick_up_location"] = order_obj.pick_up_location if order_obj.pick_up_location else None

        context["permission"] = OrderFormPermissionModel.objects.first()
        context["order_obj"] = order_obj
        return context

    def form_valid(self, form):
        order = form.save(commit=False)  # Save order but don't commit yet

        # Define the formset for handling OrderItems
        OrderItemFormSet = inlineformset_factory(
            Order, OrderItem, form=UpdateOrderItemForm, extra=0, can_delete=True, formset=BaseOrderItemFormSet
        )

        order_item_formset = OrderItemFormSet(self.request.POST, instance=order)

        if not order_item_formset.is_valid():
            print("Formset errors:", order_item_formset.errors)
            return self.form_invalid(form)

        order.save()

        submitted_order_item_ids = set()

        # Iterate through formset and process each form
        for item_form in order_item_formset.forms:
            if item_form.cleaned_data.get("DELETE", False):
                print(f"Deleting order item ID: {item_form.instance.pk}")
                if item_form.instance.pk:
                    item_form.instance.delete()
                continue

            if item_form.instance.pk:
                print(f"Updating existing OrderItem ID: {item_form.instance.pk}")
                submitted_order_item_ids.add(item_form.instance.pk)
            else:
                print("Creating new OrderItem...")

            item = item_form.save(commit=False)
            item.order = order  # Ensure OrderItem is linked to the order
            item.save()
            submitted_order_item_ids.add(item.pk)  # Store new item's ID

        # Delete any old OrderItems not in the formset
        OrderItem.objects.filter(order=order).exclude(pk__in=submitted_order_item_ids).delete()

        # Process recurring order logic
        order.recurring_orders.all().delete()

        recurring = self.request.POST.get("recurring_order") == "on"
        repeat_type = self.request.POST.get("repeat_type")
        repeat_value = self.request.POST.get("repeat_value", 0)
        repeat_start_date = order.repeat_start_date
        repeat_end_date = order.repeat_end_date if not recurring else self.request.POST.get("repeat_end_date")

        if recurring and repeat_type and int(repeat_value) > 0 and repeat_start_date and repeat_end_date:
            start_date = repeat_start_date
            repeat_type = repeat_type.lower()

            interval_map = {"weekly": 7, "monthly": 30, "yearly": 365}
            interval = interval_map.get(repeat_type)

            if not interval:
                messages.error(self.request, "Invalid repeat type")
                return self.form_invalid(form)

            # Convert repeat_end_date to datetime.date if it's a string
            if isinstance(repeat_end_date, str):
                repeat_end_date = datetime.datetime.strptime(repeat_end_date, "%Y-%m-%d").date()

            last_end_date = repeat_end_date

            for i in range(int(repeat_value)):
                next_start_date = start_date + datetime.timedelta(days=interval * i)
                next_end_date = min(next_start_date + datetime.timedelta(days=interval - 1), repeat_end_date)

                RecurringOrder.objects.create(
                    order=order,
                    start_date=next_start_date,
                    end_date=next_end_date,
                )
                last_end_date = next_end_date

            order.rental_end_date = last_end_date
            order.repeat_end_date = last_end_date
            order.save()
        # Update total rent amount
        total_rent_amount = sum((item.quantity or 0) * (item.per_unit_price or 0) for item in order.orders.all())
        order.rent_amount = total_rent_amount
        order.save()

        messages.success(self.request, "Order Updated Successfully")
        return HttpResponse("success")

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors in the form.")
        return self.render_to_response(self.get_context_data(form=form))


class OrderPermissionCreateUpdateView(View):
    template_name = "rental/rent_process/order_form_permission.html"
    success_url = reverse_lazy("rental:rent_process:order-list")

    def get(self, request, *args, **kwargs):
        user = self.request.user
        obj, created = OrderFormPermissionModel.objects.get_or_create(defaults={})
        form = OrderFormPermissionForm(instance=obj)
        return render(request, self.template_name, {"form": form, "user": user})

    def post(self, request, *args, **kwargs):
        user = self.request.user
        obj, created = OrderFormPermissionModel.objects.get_or_create(defaults={})
        form = OrderFormPermissionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(self.request, "Order permissions updated successfully.")
            return HttpResponse("success")
        return render(request, self.template_name, {"form": form, "user": user})


class ReturnOrderEdit(UpdateViewMixin):
    model = ReturnOrder
    form_class = forms.ReturnOrderEditForm
    template_name = "rental/rent_process/edit_return_order.html"
    context_object_name = "return_order"

    def get_object(self, queryset=None):
        return get_object_or_404(ReturnOrder, order__order_id=self.kwargs["pk"])

    def form_valid(self, form):
        return_order = self.get_object()
        order = return_order.order
        if order:
            order.rental_start_date = self.request.POST.get("rental_start_date", order.rental_start_date)
            order.rental_end_date = self.request.POST.get("rental_end_date", order.rental_end_date)
            order.save()
        messages.success(self.request, "Return Order updated successfully.")
        return HttpResponse("success")

    def form_invalid(self, form):
        return render(self.request, self.template_name, {"form": form, "return_order": self.get_object()}, status=201)


class OrderHistory(DetailView):
    model = Delivery
    template_name = "rental/rent_process/timeline.html"
    context_object_name = "time_line"

    def get_object(self, queryset=None):
        delivery_id = self.kwargs.get("delivery_id")
        print("Order History accessed")
        return get_object_or_404(Delivery, delivery_id=delivery_id)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        delivery_id = self.kwargs.get("delivery_id")
        deliveries = Delivery.objects.filter(delivery_id=delivery_id)
        context["deliveries"] = deliveries
        return context


class UploadDocument(CreateViewMixin):
    """
    View to handle document uploads associated with an opportunity.
    """

    model = Document
    form_class = forms.UploadDocumentForm
    template_name = "rental/file_upload.html"

    def form_valid(self, form):
        print("form_valid: ")
        """
        Process a valid form submission for document upload.

        :param form: The submitted form with valid data.
        :return: Redirect to the success URL.
        """
        order_id = self.request.POST.get("order_order_id")
        print("order_id: ", order_id)
        comment = self.request.POST.get("comment")
        print("comment: ", comment)
        stage = self.request.POST.get("stage")
        print("stage: ", stage)

        # Retrieve the associated Opportunity object
        order_object = get_object_or_404(Order, order_id=order_id)
        print("order_object: ", order_object)

        # Set form instance attributes
        form.instance.order = order_object
        form.instance.stage = stage
        form.instance.comment = comment

        # Save the document
        form.save()

        return super().form_valid(form)

    def form_invalid(self, form):
        print("form_invalid: ")
        """
        Handle an invalid form submission.

        :param form: The submitted form with errors.
        :return: Render the form with errors.
        """
        for field, errors in form.errors.items():
            for error in errors:
                LOGGER.error(f"Error in {field}: {error}")
        return super().form_invalid(form)

    def get_success_url(self):
        """
        Define the URL to redirect to upon successful document upload.

        :return: The success URL for the opportunity detail view.
        """
        self.request.POST.get("order_id")
        return reverse("rental:rent_process:order-list")


class DocumentListAjaxView(CustomDataTableMixin):
    """AJAX view to list documents in a DataTable format."""

    model = Document

    def get_queryset(self):
        order_id = self.kwargs.get("order_id")
        stage = self.kwargs.get("stage")
        qs = Document.objects.filter(order__order_id=order_id, stage=stage)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(document__icontains=self.search)
                | Q(comment__icontains=self.search)
                | Q(created_at__icontains=self.search)
            )
        return qs

    def _get_documents(self, obj):
        if obj.document:
            return f"<div class='text-center'><a href='{obj.file_path}' target='_blank' download><i class='icon-cloud-download'></i> {obj.document.name}</a></div>"
        else:
            return "<div class='text-center'>-</div>"

    def _get_comments(self, obj):
        if obj.comment:
            return f"<div class='text-center'>{obj.comment}</div>"
        else:
            return "<div class='text-center'>-</div>"

    def _get_created_at(self, obj):
        if obj.created_at:
            created_at = obj.created_at.strftime("%m-%d-%Y")
            return f"<div class='text-center'>{created_at}</div>"
        else:
            return "<div class='text-center'>-</div>"

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "document": self._get_documents(o),
                    "created_at": self._get_created_at(o),
                    "comment": self._get_comments(o),
                }
            )
        print("data:-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- ", data)
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class UpdateStages(ViewMixin):
    """
    Update Order Stages.
    """

    def post(self, request) -> JsonResponse:
        """
        Handle POST requests to update the Order stage.

        :param request: The HTTP request object containing the JSON body.
        :return: JsonResponse indicating success or failure of the operation.
        """
        data = self._parse_request_body(request)
        if isinstance(data, JsonResponse):
            return data

        order_id = data.get("order_id")
        updated_stage = data.get("stage")

        if not order_id or not updated_stage:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        order = get_object_or_404(Order, order_id=order_id)
        return self._update_stage(order, updated_stage)

    def _parse_request_body(self, request) -> JsonResponse:
        """
        Parse the JSON request body.

        :param request: The HTTP request object.
        :return: Parsed JSON data as a dictionary or JsonResponse with error.
        """
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            LOGGER.error("Error: Invalid JSON")
            return JsonResponse(ERROR_RESPONSE, status=400)

    def _update_stage(self, order: Order, updated_stage: str) -> JsonResponse:
        """
        Update the order stage if the new stage is valid.

        :param order: The order instance to be updated.
        :param updated_stage: The new stage to set for the order.
        :return: JsonResponse indicating success or failure of the operation.
        """
        current_stage = order.get_current_stage_constant()
        order_status = getattr(Order, updated_stage, None)

        if order_status is None:
            return JsonResponse({"error": "Invalid stage"}, status=400)

        if current_stage < updated_stage:
            order.order_status = order_status
            order.updated_at = datetime.datetime.now()
            order.save()
            return JsonResponse({"message": "order stage updated successfully"}, status=200)
        else:
            return JsonResponse({"message": "order stage lower than current stage"}, status=200)


class DeliveryCheckoutListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Deliveries in a DataTable format."""

    def get_queryset(self):
        """Returns a queryset of deliveries."""

        order_id = self.kwargs.get("order_id")

        delivery_objs = (
            Delivery.objects.select_related("product", "order")
            .filter(
                delivery_status__in=[Delivery.STAGE_2, Delivery.STAGE_3, Delivery.STAGE_4], order__order_id=order_id
            )
            .order_by("delivery_qty")
        )

        return delivery_objs

    def filter_queryset(self, qs):
        """Return filtered queryset based on search input."""
        if self.search:
            return qs.filter(
                Q(order__order_id__icontains=self.search)
                | Q(unique_delivery_id__icontains=self.search)
                | Q(delivery_status__icontains=self.search)
                | Q(order__customer__name__icontains=self.search)
            )
        return qs

    def _get_checkout_date(self, delivery_obj):

        # Get today's date in YYYY-MM-DD format
        today_date = now().date().isoformat()  # YYYY-MM-DD format
        check_out_date = delivery_obj.check_out_date.isoformat() if delivery_obj.check_out_date else None

        # Render the partial template with delivery object and today_date
        t = get_template("rental/rent_process/delivery_checkout_date.html")
        return t.render({"delivery_obj": delivery_obj, "today_date": today_date, "check_out_date": check_out_date})

    def prepare_results(self, qs):
        """Format delivery data for DataTables with grouped deliveries."""
        qs = sorted(qs, key=lambda x: x.delivery_qty)

        delivery_map = {}

        for delivery in qs:
            delivery_id = delivery.unique_delivery_id

            if delivery_id not in delivery_map:
                delivery_map[delivery_id] = {
                    "delivery_id": delivery_id,
                    "delivery_pk": delivery.unique_delivery_id,
                    "total_qty": 0,
                    "checkout_date": self._get_checkout_date(delivery),
                    "delivery_date": delivery.delivery_date.strftime("%d %B, %Y") if delivery.delivery_date else "-",
                    "products": "",
                    # "actions": self._get_actions(delivery),
                }

            delivery_map[delivery_id]["total_qty"] += delivery.delivery_qty

            product_index = len(delivery_map[delivery_id]["products"].split("<tr>")) - 1
            product_row = self._get_product_row(delivery, product_index + 1)

            delivery_map[delivery_id]["products"] += product_row

            print(
                f"delivery_id: {delivery_id} | total_delivery: {delivery_map[delivery_id]['total_qty']} | delivery.delivery_qty: {delivery.delivery_qty}"
            )

        data = []
        for value in delivery_map.values():
            if value["products"]:
                value["products"] = self._wrap_product_table(
                    value["products"], value["delivery_id"], value["delivery_pk"]
                )
            data.append(value)

        return data

    def _get_product_row(self, delivery, index):
        """Generate a table row for an individual product with a dynamic Sr No."""
        if not delivery.product:
            return ""

        selected_none = "" if delivery.delivery_status in [Delivery.STAGE_3, Delivery.STAGE_4] else "selected"
        selected_checkout = "selected" if delivery.delivery_status == "Check Out" else ""

        return f"""
            <tr>
                <td>{index}</td>
                <td>{delivery.product.equipment_id}</td>
                <td>{delivery.product.equipment_name}</td>
                <td>
                    <input type="text" id="quantity-{delivery.product.equipment_id}" data-delivery-unique_id="{delivery.unique_delivery_id}" data-delivery-pk="{delivery.pk}"
                        data-value="{delivery.delivery_qty}" value="{delivery.delivery_qty}"
                        class="form-control checkout-qty wizard-required">
                    <small class="quantityMessage text-danger"></small>
                </td>
                <td>
                    <select name="status" class="select2 form-control wizard-required another-select-checkout"
                            data-delivery-id="{delivery.unique_delivery_id}" data-delivery-pk="{delivery.pk}">
                        <option value="" disabled {selected_none}>None</option>
                        <option value="Check Out" {selected_checkout}>Check Out</option>
                    </select>
                </td>
            </tr>
        """

    def _wrap_product_table(self, rows, delivery_id, delivery_pk):
        print("delivery_pk: ", delivery_pk)
        """Wrap product rows in a full table structure with a unique ID."""
        return f"""
            <table class="table table-striped table-bordered checkout-products-table"
                id="checkout-products-table-{delivery_id}" data-table-id="{delivery_pk}">
                <thead>
                    <tr class="text-center">
                        <th colspan="5" class="align-top">Items Information</th>
                    </tr>
                    <tr>
                        <th>Sr No</th>
                        <th>Equipment ID</th>
                        <th>Items</th>
                        <th>Quantity</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody class="table-striped">
                    {rows}
                </tbody>
            </table>
        """

    def get_ordering(self, qs):
        """Handle ordering for DataTable columns."""
        column_map = {
            "0": "unique_delivery_id",
            "1": "delivery_qty",
            "2": "contract_start_date",
            "3": "delivery_date",
        }
        order_column_index = self.request.GET.get("order[0][column]", "0")
        order_by = column_map.get(order_column_index, "unique_delivery_id")
        return qs.order_by(order_by)

    def get(self, request, *args, **kwargs):
        """Return JSON response for DataTables."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

    def get_context_data(self, request):
        try:
            context = super().get_context_data(request)
            return context
        except Exception as e:
            return {"error": str(e)}


# class DeliveryStockUpdateView(View):
#     def post(self, request, *args, **kwargs):
#         try:
#             data = json.loads(request.body)
#             print(f"Received data: {data}")

#             checked_out_tables = data.get("checkedOutTables", [])
#             print("checked_out_tables: ", checked_out_tables)

#             if not checked_out_tables:
#                 return JsonResponse({"success": False, "error": "No fully checked-out tables found."})

#             delivery_ids = self._get_delivery_ids_from_tables(checked_out_tables)
#             print("delivery_ids: ", delivery_ids)

#             if not delivery_ids:
#                 return JsonResponse({"success": False, "error": "No valid deliveries found for these tables."})

#             delivery_objs = Delivery.objects.filter(unique_delivery_id__in=delivery_ids)
#             print("delivery_objs:", list(delivery_objs))

#             if not delivery_objs.exists():
#                 return JsonResponse({"success": False, "error": "No matching deliveries found in the database."})

#             for delivery_obj in delivery_objs:
#                 stockadjustment_obj = StockAdjustment.objects.filter(rental_product=delivery_obj.product).first()
#                 if delivery_obj.delivery_status == Delivery.STAGE_2:
#                     if stockadjustment_obj:
#                         stockadjustment_obj.quantity -= delivery_obj.delivery_qty
#                         stockadjustment_obj.save()
#                 # delivery_obj.delivery_status = Delivery.STAGE_3
#                 # delivery_obj.save()

#             print(f"Deliveries {delivery_ids} updated successfully to {Delivery.STAGE_3}")
#             return JsonResponse({"success": True, "message": f"Deliveries {delivery_ids} updated successfully."})

#         except json.JSONDecodeError:
#             return JsonResponse({"success": False, "error": "Invalid JSON data"})

#         except Exception as e:
#             print(f"Unexpected error: {str(e)}")
#             return JsonResponse({"success": False, "error": "An unexpected error occurred"})

#     def _get_delivery_ids_from_tables(self, table_ids):
#         print("table_ids: ", table_ids)
#         return table_ids


class UpdateCheckoutDateView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            delivery_id = data.get("delivery_id")
            print("delivery_id: ", delivery_id)
            checkout_date = data.get("checkout_date")
            print("checkout_date: ", checkout_date)

            if not delivery_id or not checkout_date:
                return JsonResponse({"success": False, "error": "Invalid data received."})

            # Ensure the date format is correct
            try:
                checkout_date = datetime.datetime.strptime(checkout_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid date format."})

            # Fetch and update the delivery object
            deliverys = Delivery.objects.filter(unique_delivery_id=delivery_id)
            print("deliverys: ", deliverys)
            if not deliverys:
                return JsonResponse({"success": False, "error": "Delivery not found."})
            for delivery in deliverys:
                delivery.check_out_date = checkout_date
                delivery.save()

            print(f"Updated delivery {delivery_id} with new date: {checkout_date}")
            return JsonResponse({"success": True, "message": "Checkout date updated successfully."})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data."})
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"})


class UpdateQuantityView(View):
    def post(self, request, *args, **kwargs):
        """Update delivery quantities based on AJAX data."""
        try:
            data = json.loads(request.body)
            updated_quantities = data.get("updatedQuantities", [])

            if not updated_quantities:
                return JsonResponse({"success": False, "error": "No data provided"}, status=400)

            for item in updated_quantities:
                delivery_pk = item.get("delivery_pk")
                new_quantity = item.get("new_quantity")
                delivery_unique_id = item.get("delivery_unique_id")

                if not delivery_pk or new_quantity is None or not delivery_unique_id:
                    return JsonResponse({"success": False, "error": "Missing required fields"}, status=400)

                try:
                    delivery_obj = Delivery.objects.get(delivery_id=delivery_pk, unique_delivery_id=delivery_unique_id)

                    # Prevent updates if the status is STAGE_1 or STAGE_2
                    if delivery_obj.delivery_status in [Delivery.STAGE_1, Delivery.STAGE_2]:
                        delivery_obj.delivery_qty = new_quantity
                        delivery_obj.save()
                        return JsonResponse({"success": True, "message": "Updated quantities successfully"})

                    # If the delivery is in STAGE_3 or beyond, check all deliveries under unique_delivery_id
                    all_deliveries = Delivery.objects.filter(unique_delivery_id=delivery_unique_id)
                    if all(
                        delivery.delivery_status
                        in [
                            Delivery.STAGE_3,
                            Delivery.STAGE_4,
                            Delivery.STAGE_5,
                            Delivery.STAGE_6,
                            Delivery.STAGE_7,
                            Delivery.STAGE_8,
                        ]
                        for delivery in all_deliveries
                    ):

                        # Calculate the difference in quantity
                        quantity_difference = delivery_obj.delivery_qty - new_quantity

                        stock_adjustment = StockAdjustment.objects.filter(rental_product=delivery_obj.product).first()
                        if stock_adjustment:
                            if quantity_difference > 0:
                                # Reduce stock if the new quantity is smaller
                                print(
                                    f"Reducing Stock: Product: {delivery_obj.product.equipment_name}, "
                                    f"Old Quantity: {stock_adjustment.quantity}, "
                                    f"Reduce By: {quantity_difference}"
                                )

                                stock_adjustment.quantity += quantity_difference

                            elif quantity_difference < 0:
                                # Increase stock if the new quantity is larger
                                increase_by = abs(quantity_difference)
                                print(
                                    f"Increasing Stock: Product: {delivery_obj.product.equipment_name}, "
                                    f"Old Quantity: {stock_adjustment.quantity}, "
                                    f"Increase By: {increase_by}"
                                )

                                stock_adjustment.quantity -= increase_by

                            stock_adjustment.save()
                            print(f"New Stock Quantity: {stock_adjustment.quantity}")

                    # Update the delivery quantity
                    delivery_obj.delivery_qty = new_quantity
                    delivery_obj.save()

                except Delivery.DoesNotExist:
                    return JsonResponse(
                        {"success": False, "error": f"Delivery with ID {delivery_pk} not found"}, status=404
                    )

            return JsonResponse({"success": True, "message": "Updated quantities successfully"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)


class PickupTicketListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Deliveries in a DataTable format."""

    def _get_actions(self, obj):
        """Generate action buttons for delivery orders."""
        t = get_template("rental/orders/delivery_order_actions.html")
        edit_url = ""
        remove_url = ""
        return t.render(
            {
                "edit_url": edit_url,
                "remove_url": remove_url,
                "delivery": obj,
                "request": self.request,
            }
        )

    def get_queryset(self):
        """Returns a queryset of deliveries."""
        order_id = self.kwargs.get("order_id")
        return Delivery.objects.select_related("product", "order").filter(order__order_id=order_id)

    def filter_queryset(self, qs):
        """Return filtered queryset based on search input."""
        if self.search:
            return qs.filter(
                Q(order__order_id__icontains=self.search)
                | Q(unique_delivery_id__icontains=self.search)
                | Q(delivery_status__icontains=self.search)
                | Q(order__customer__name__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Format delivery data for DataTables with grouped deliveries."""
        delivery_map = {}

        for delivery in qs:
            delivery_id = delivery.unique_delivery_id
            delivery_pk = delivery.unique_delivery_id
            if delivery_id not in delivery_map:
                delivery_map[delivery_id] = {
                    "delivery_id": delivery_id,
                    "delivery_pk": delivery_pk,
                    "total_qty": 0,
                    "pickup_date": delivery.pickup_date.strftime("%d %B, %Y") if delivery.pickup_date else "-",
                    "delivery_date": delivery.delivery_date.strftime("%d %B, %Y") if delivery.delivery_date else "-",
                    "products": "",
                    "actions": self._get_actions(delivery),
                }

            delivery_map[delivery_id]["total_qty"] += delivery.delivery_qty

            product_index = len(delivery_map[delivery_id]["products"].split("<tr>")) - 1
            product_row = self._get_product_row(delivery, product_index + 1)

            delivery_map[delivery_id]["products"] += product_row

            print(
                f" delivery_pk: {delivery_pk} | delivery_id: {delivery_id} | total_delivery: {delivery_map[delivery_id]['total_qty']} | delivery.delivery_qty: {delivery.delivery_qty}"
            )

        data = []
        for value in delivery_map.values():
            if value["products"]:
                value["products"] = self._wrap_product_table(value["products"], delivery_id, value["delivery_pk"])
            data.append(value)

        return data

    def _get_product_row(self, delivery, index):
        """Generate a table row for an individual product with a dynamic Sr No."""
        if not delivery.product:
            return ""

        selected_status = "None" if delivery.delivery_status == "Create Delivery" else "Loaded"
        disable_none = "disabled" if selected_status == "Loaded" else ""

        return f"""
            <tr>
                <td>{index}</td>
                <td>{delivery.product.equipment_id}</td>
                <td>{delivery.product.equipment_name}</td>
                <td>{delivery.delivery_qty}</td>
                <td>
                    <select class="select2 form-control wizard-required another-select-Loaded" data-delivery-id="{delivery.unique_delivery_id}">
                        <option value="None" {disable_none}>None</option>
                        <option value="Loaded" {'selected' if selected_status == "Loaded" else ""}>Loaded</option>
                    </select>
                </td>
            </tr>
        """

    def _wrap_product_table(self, rows, delivery_id, delivery_pk):
        """Wrap product rows in a full table structure."""
        return f"""
            <table class="table table-striped table-bordered pickup-products-table" id="pickup-products-table-{delivery_id}" data-table-id="{delivery_pk}">
                <thead>
                    <tr class="text-center">
                        <th colspan="5" class="align-top">Items Information</th>
                    </tr>
                    <tr>
                        <th>Sr No</th>
                        <th>Equipment ID</th>
                        <th>Items</th>
                        <th>Quantity</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody class="table-striped">
                    {rows}
                </tbody>
            </table>"""

    def get_ordering(self, qs):
        """Handle ordering for DataTable columns."""
        column_map = {
            "0": "unique_delivery_id",
            "1": "delivery_qty",
            "2": "pickup_date",
            "3": "delivery_date",
        }
        order_column_index = self.request.GET.get("order[0][column]", "0")
        order_by = column_map.get(order_column_index, "unique_delivery_id")
        return qs.order_by(order_by)

    def get(self, request, *args, **kwargs):
        """Return JSON response for DataTables."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

    def get_context_data(self, request):
        try:
            context = super().get_context_data(request)
            return context
        except Exception as e:
            return {"error": str(e)}


class UpdatePickupDateView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.POST.get("deliveries", "[]"))
            print("data: ", data)

            for item in data:
                delivery_id = item.get("delivery_id")
                new_pickup_date = item.get("pickup_date")
                print("new_pickup_date: ", new_pickup_date)
                new_status = item.get("status")

                try:
                    deliveries = Delivery.objects.filter(unique_delivery_id=delivery_id)
                    if deliveries.exists():
                        for delivery in deliveries:
                            if new_pickup_date:
                                print("=====================new pickup date ")
                                delivery.pickup_date = parse_date(new_pickup_date)
                                delivery.save()
                            if new_status:
                                print("new_status: in if ", new_status)
                                delivery.delivery_status = delivery.STAGE_2
                            delivery.save()

                except Delivery.DoesNotExist:
                    continue

            return JsonResponse({"message": "Pickup Date & Status updated successfully!!"}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"})


class DeliveryListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Deliveries in a DataTable format."""

    def _get_actions(self, obj):
        """Generate action buttons for delivery orders."""
        t = get_template("rental/orders/delivery_order_actions.html")
        edit_url = ""
        remove_url = ""
        return t.render(
            {
                "edit_url": edit_url,
                "remove_url": remove_url,
                "delivery": obj,
                "request": self.request,
            }
        )

    def get_queryset(self):
        """Returns a queryset of deliveries for the given order_id in the URL."""
        order_id = self.kwargs.get("order_id")
        return Delivery.objects.select_related("product", "order").filter(order__order_id=order_id)

    def filter_queryset(self, qs):
        """Return filtered queryset based on search input."""
        if self.search:
            return qs.filter(
                Q(order__order_id__icontains=self.search)
                | Q(unique_delivery_id__icontains=self.search)
                | Q(delivery_status__icontains=self.search)
                | Q(order__customer__name__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Format delivery data for DataTables with grouped deliveries."""
        delivery_map = {}

        for delivery in qs:
            delivery_id = delivery.unique_delivery_id

            if delivery_id not in delivery_map:
                delivery_map[delivery_id] = {
                    "delivery_id": delivery_id,
                    "total_qty": 0,  # Reset for each delivery_id
                    "contract_start_date": (
                        delivery.contract_start_date.strftime("%d %B, %Y") if delivery.contract_start_date else "-"
                    ),
                    "delivery_date": delivery.delivery_date.strftime("%d %B, %Y") if delivery.delivery_date else "-",
                    "products": "",  # Store products as a formatted table
                    "actions": self._get_actions(delivery),
                }

            # Accumulate total delivery **per delivery_id**
            delivery_map[delivery_id]["total_qty"] += delivery.delivery_qty

            product_index = len(delivery_map[delivery_id]["products"].split("<tr>")) - 1
            product_row = self._get_product_row(delivery, product_index + 1)

            delivery_map[delivery_id]["products"] += product_row

            print(
                f"delivery_id: {delivery_id} | total_delivery: {delivery_map[delivery_id]['total_qty']} | delivery.delivery_qty: {delivery.delivery_qty}"
            )

        data = []
        for value in delivery_map.values():
            if value["products"]:
                value["products"] = self._wrap_product_table(value["products"])
            data.append(value)

        return data

    def _get_product_row(self, delivery, index):
        """Generate a table row for an individual product with a dynamic Sr No."""
        if not delivery.product:
            return ""
        return f"""
            <tr>
                <td>{index}</td>
                <td>{delivery.product.equipment_id}</td>
                <td>{delivery.product.equipment_name}</td>
                <td>{delivery.delivery_qty}</td>
            </tr>
        """

    def _wrap_product_table(self, rows):
        """Wrap product rows in a full table structure."""
        return f"""
            <table class="table table-striped table-bordered">
                <thead>
                    <tr class="text-center">
                       <th colspan="5" class="align-top fw-bold">Items Information</th>

                    </tr>
                    <tr>
                        <th>Sr No</th>
                        <th>Equipment ID</th>
                        <th>Items</th>
                        <th>Quantity</th>
                    </tr>
                </thead>
                <tbody class="table-striped">
                    {rows}
                </tbody>
            </table>"""

    def get_ordering(self, qs):
        """Handle ordering for DataTable columns."""
        column_map = {
            "0": "unique_delivery_id",
            "1": "delivery_qty",
            "2": "contract_start_date",
            "3": "delivery_date",
        }
        order_column_index = self.request.GET.get("order[0][column]", "0")
        order_by = column_map.get(order_column_index, "unique_delivery_id")
        return qs.order_by(order_by)

    def get(self, request, *args, **kwargs):
        """Return JSON response for DataTables."""
        context_data = self.get_context_data(request)
        print("context_data: ", context_data)
        return JsonResponse(context_data)

    def get_context_data(self, request):
        try:
            context = super().get_context_data(request)
            return context
        except Exception as e:
            return {"error": str(e)}


class CheckDeliveryStatusView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            delivery_id = data.get("delivery_id")
            delivery_pk = data.get("delivery_pk")
            order_id = data.get("order_id")
            global_status_change = data.get("global_status_change", False)

            # **Single Delivery Update**
            if delivery_id:
                return self.update_single_delivery(delivery_id, delivery_pk)

            # **Global Order-Wide Update**
            elif order_id and global_status_change:
                return self.update_global_deliveries(order_id)

            return JsonResponse({"success": False, "error": "Invalid request parameters"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"})

    def update_single_delivery(self, delivery_id, delivery_pk):
        """Handles updating a single delivery's status"""
        delivery = Delivery.objects.filter(unique_delivery_id=delivery_id, pk=delivery_pk).first()

        if delivery:
            previous_status = delivery.delivery_status  # Store old status before updating
            delivery.delivery_status = Delivery.STAGE_3
            delivery.save()

            print(
                f"Updated Single Delivery: {delivery.pk}, Old Status: {previous_status}, New Status: {delivery.delivery_status}"
            )

            # Reduce stock only if it was in STAGE_2 before changing
            if previous_status == Delivery.STAGE_2:
                self.update_delivery_stock(delivery.unique_delivery_id)

            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": f"Delivery with ID {delivery_id} not found"})

    def update_global_deliveries(self, order_id):
        """Handles global status change for all deliveries under an order"""
        delivery_objs = Delivery.objects.filter(order__order_id=order_id)

        if not delivery_objs.exists():
            return JsonResponse({"success": False, "error": "No deliveries exist for this order"})

        # Get unique_delivery_id values where all deliveries are in STAGE_2
        unique_ids_to_update = {
            unique_id
            for unique_id in delivery_objs.values_list("unique_delivery_id", flat=True).distinct()
            if Delivery.objects.filter(unique_delivery_id=unique_id).exclude(delivery_status=Delivery.STAGE_2).count()
            == 0
        }

        if not unique_ids_to_update:
            return JsonResponse({"success": False, "error": "No valid deliveries found for updating"})

        # Bulk update deliveries to STAGE_3
        updated_rows = Delivery.objects.filter(
            unique_delivery_id__in=unique_ids_to_update, delivery_status=Delivery.STAGE_2
        ).update(delivery_status=Delivery.STAGE_3)

        # Reduce stock for affected deliveries
        for unique_id in unique_ids_to_update:
            self.update_delivery_stock(unique_id)

        return JsonResponse(
            {"success": True, "updated_deliveries": list(unique_ids_to_update), "updated_rows": updated_rows}
        )

    def update_delivery_stock(self, unique_delivery_id):
        """Reduces stock only if all deliveries under unique_delivery_id are in STAGE_3"""
        print(f"Stock Adjustment Check Started for unique_delivery_id: {unique_delivery_id}")

        # Fetch all deliveries under this unique_delivery_id
        deliveries = Delivery.objects.filter(unique_delivery_id=unique_delivery_id)

        # Check if ALL deliveries are in STAGE_3
        if not all(delivery.delivery_status == Delivery.STAGE_3 for delivery in deliveries):
            print(f"Stock reduction skipped: Not all deliveries in STAGE_3 for unique_delivery_id {unique_delivery_id}")
            return

        print(
            f"All deliveries in STAGE_3. Proceeding with stock reduction for unique_delivery_id: {unique_delivery_id}"
        )

        # Now proceed with stock reduction
        for delivery in deliveries:
            stock_adjustment = StockAdjustment.objects.filter(rental_product=delivery.product).first()
            if stock_adjustment:
                print(
                    f"Reducing Stock: Product: {delivery.product.equipment_name}, "
                    f"Old Quantity: {stock_adjustment.quantity}, "
                    f"Reduce By: {delivery.delivery_qty}"
                )

                stock_adjustment.quantity -= delivery.delivery_qty
                stock_adjustment.save()

                print(f"New Stock Quantity: {stock_adjustment.quantity}")

        print(f"Stock Adjustment Completed for unique_delivery_id: {unique_delivery_id}")


class DeliveredToCustomerListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Deliveries in a DataTable format."""

    def get_queryset(self):
        """Returns a queryset of deliveries."""

        order_id = self.kwargs.get("order_id")

        delivery_objs = (
            Delivery.objects.select_related("product", "order")
            .filter(delivery_status__in=[Delivery.STAGE_3, Delivery.STAGE_4], order__order_id=order_id)
            .order_by("delivery_qty")
        )

        return delivery_objs

    def filter_queryset(self, qs):
        """Return filtered queryset based on search input."""
        if self.search:
            return qs.filter(
                Q(order__order_id__icontains=self.search)
                | Q(unique_delivery_id__icontains=self.search)
                | Q(delivery_status__icontains=self.search)
                | Q(order__customer__name__icontains=self.search)
            )
        return qs

    def _get_contract_start_date(self, delivery_obj):

        # Get today's date in YYYY-MM-DD format
        today_date = now().date().isoformat()  # YYYY-MM-DD format
        contract_start_date = delivery_obj.contract_start_date.isoformat() if delivery_obj.contract_start_date else None

        # Render the partial template with delivery object and today_date
        t = get_template("rental/rent_process/delivery_contract_start_date.html")
        return t.render(
            {"delivery_obj": delivery_obj, "today_date": today_date, "contract_start_date": contract_start_date}
        )

    def prepare_results(self, qs):
        """Format delivery data for DataTables with grouped deliveries."""
        qs = sorted(qs, key=lambda x: x.delivery_qty)

        delivery_map = {}

        for delivery in qs:
            delivery_id = delivery.unique_delivery_id

            if delivery_id not in delivery_map:
                delivery_map[delivery_id] = {
                    "delivery_id": delivery_id,
                    "delivery_pk": delivery.unique_delivery_id,
                    "total_qty": 0,
                    "contract_start_date": self._get_contract_start_date(delivery),
                    "delivery_date": delivery.delivery_date.strftime("%d %B, %Y") if delivery.delivery_date else "-",
                    "products": "",
                    # "actions": self._get_actions(delivery),
                }

            delivery_map[delivery_id]["total_qty"] += delivery.delivery_qty

            product_index = len(delivery_map[delivery_id]["products"].split("<tr>")) - 1
            product_row = self._get_product_row(delivery, product_index + 1)

            delivery_map[delivery_id]["products"] += product_row

            print(
                f"delivery_id: {delivery_id} | total_delivery: {delivery_map[delivery_id]['total_qty']} | delivery.delivery_qty: {delivery.delivery_qty}"
            )

        data = []
        for value in delivery_map.values():
            if value["products"]:
                value["products"] = self._wrap_product_table(
                    value["products"], value["delivery_id"], value["delivery_pk"]
                )
            data.append(value)

        return data

    def _get_product_row(self, delivery, index):
        """Generate a table row for an individual product with a dynamic Sr No."""
        if not delivery.product:
            return ""

        selected_none = "" if delivery.delivery_status == "Delivered To Customer" else "selected"
        selected_checkout = "selected" if delivery.delivery_status == "Delivered To Customer" else ""

        return f"""
            <tr>
                <td>{index}</td>
                <td>{delivery.product.equipment_id}</td>
                <td>{delivery.product.equipment_name}</td>
                <td>
                    <input type="text" id="quantity-{delivery.product.equipment_id}" data-delivery-unique_id="{delivery.unique_delivery_id}" data-delivery-pk="{delivery.pk}"
                        data-value="{delivery.delivery_qty}" value="{delivery.delivery_qty}"
                        class="form-control delivered-to-customer-qty wizard-required">
                    <small class="quantityMessage text-danger"></small>
                </td>
                <td>
                    <select name="status" class="select2 form-control wizard-required another-select-delivered-to-customer"
                            data-delivery-id="{delivery.unique_delivery_id}" data-delivery-pk="{delivery.pk}">
                        <option value="" disabled {selected_none}>None</option>
                        <option value="Delivered To Customer" {selected_checkout}>Delivered</option>
                    </select>
                </td>
            </tr>
        """

    def _wrap_product_table(self, rows, delivery_id, delivery_pk):
        print("delivery_pk: ", delivery_pk)
        """Wrap product rows in a full table structure with a unique ID."""
        return f"""
            <table class="table table-striped table-bordered delivered-to-customer-products-table"
                id="delivered-to-customer-products-table-{delivery_id}" data-table-id="{delivery_pk}">
                <thead>
                    <tr class="text-center">
                        <th colspan="5" class="align-top">Items Information</th>
                    </tr>
                    <tr>
                        <th>Sr No</th>
                        <th>Equipment ID</th>
                        <th>Items</th>
                        <th>Quantity</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody class="table-striped">
                    {rows}
                </tbody>
            </table>
        """

    def get_ordering(self, qs):
        """Handle ordering for DataTable columns."""
        column_map = {
            "0": "unique_delivery_id",
            "1": "delivery_qty",
            "2": "contract_start_date",
            "3": "delivery_date",
        }
        order_column_index = self.request.GET.get("order[0][column]", "0")
        order_by = column_map.get(order_column_index, "unique_delivery_id")
        return qs.order_by(order_by)

    def get(self, request, *args, **kwargs):
        """Return JSON response for DataTables."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

    def get_context_data(self, request):
        try:
            context = super().get_context_data(request)
            return context
        except Exception as e:
            return {"error": str(e)}


class UpdateDeliveredToCustomerDateView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            delivery_id = data.get("delivery_id")
            contract_start_date = data.get("contract_start_date")

            if not delivery_id or not contract_start_date:
                return JsonResponse({"success": False, "error": "Invalid data received."})

            # Ensure the date format is correct
            try:
                contract_start_date = datetime.datetime.strptime(contract_start_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid date format."})

            # Fetch and update the delivery object
            deliverys = Delivery.objects.filter(unique_delivery_id=delivery_id)

            if not deliverys:
                return JsonResponse({"success": False, "error": "Delivery not found."})
            for delivery in deliverys:
                delivery.contract_start_date = contract_start_date
                delivery.save()

            print(f"Updated delivery {delivery_id} with new date: {contract_start_date}")
            return JsonResponse({"success": True, "message": "Contract Start date updated successfully."})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data."})
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"})


class UpdateDeliveredToCustomerStatusView(View):
    def post(self, request, *args, **kwargs):
        try:
            # Parse incoming JSON data
            data = json.loads(request.body)
            delivery_id = data.get("delivery_id")
            delivery_pk = data.get("delivery_pk")
            order_id = data.get("order_id")
            global_status_change = data.get("global_status_change", False)

            # **Single Delivery Update**
            if delivery_id and delivery_pk:
                return self.update_single_delivery(delivery_id, delivery_pk)

            # **Global Order-Wide Update**
            elif order_id and global_status_change:
                return self.update_global_deliveries(order_id, delivery_id)

            # If neither condition is met, return invalid parameters error
            return JsonResponse({"success": False, "error": "Invalid request parameters"})

        except json.JSONDecodeError:
            # Handle case where the body isn't valid JSON
            return JsonResponse({"success": False, "error": "Invalid JSON data"})

        except Exception as e:
            # General error handling to catch unexpected issues
            return JsonResponse({"success": False, "error": f"An error occurred: {str(e)}"})

    def update_single_delivery(self, delivery_id, delivery_pk):
        """Handles updating a single delivery's status"""
        try:
            delivery = Delivery.objects.filter(unique_delivery_id=delivery_id, pk=delivery_pk).first()

            if not delivery:
                return JsonResponse(
                    {"success": False, "error": f"Delivery with ID {delivery_id} and PK {delivery_pk} not found"}
                )

            previous_status = delivery.delivery_status
            delivery.delivery_status = Delivery.STAGE_4
            delivery.save()

            print(
                f"Updated Single Delivery: {delivery.pk}, Old Status: {previous_status}, New Status: {delivery.delivery_status}"
            )

            return JsonResponse(
                {
                    "success": True,
                    "updated_delivery": {
                        "id": delivery.pk,
                        "old_status": previous_status,
                        "new_status": delivery.delivery_status,
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": f"Failed to update delivery: {str(e)}"})

    def update_global_deliveries(self, order_id, delivery_id):
        """Handles global status change for all deliveries under an order"""
        try:
            deliveries_to_update = Delivery.objects.filter(
                order__order_id=order_id, unique_delivery_id__in=delivery_id, delivery_status=Delivery.STAGE_3
            )

            updated_count = deliveries_to_update.update(delivery_status=Delivery.STAGE_4)

            if updated_count == 0:
                return JsonResponse({"success": False, "error": "No deliveries found to update."})

            updated_deliveries = list(deliveries_to_update)
            updated_delivery_info = [
                {"id": delivery.pk, "old_status": delivery.delivery_status, "new_status": Delivery.STAGE_4}
                for delivery in updated_deliveries
            ]

            return JsonResponse(
                {"success": True, "updated_deliveries": updated_delivery_info, "updated_count": updated_count}
            )

        except Exception as e:
            return JsonResponse({"success": False, "error": f"Failed to update global deliveries: {str(e)}"})


class ReturnDeliveryModalView(View):
    model = Order
    template_name = "rental/rent_process/return_delivery_table.html"

    def get(self, request, *args, **kwargs):
        order_id = self.kwargs["order_id"]
        return_order = ReturnOrder.objects.filter(order__order_id=order_id).first()
        return_order_created_at = return_order.created_at if return_order else None
        delivered_items = (
            Delivery.objects.filter(order__order_id=order_id, delivery_status=Delivery.STAGE_4)
            .values("product")
            .annotate(total_delivered_qty=Sum("delivery_qty"))
        )

        pending_return_items = []

        for item in delivered_items:
            product_id = item["product"]
            total_delivered_qty = item["total_delivered_qty"]

            # Get already returned quantity
            returned_qty = (
                ReturnDeliveryItem.objects.filter(
                    return_delivery__return_order__order__order_id=order_id, product_id=product_id
                ).aggregate(Sum("return_qty"))["return_qty__sum"]
                or 0
            )

            remaining_qty = total_delivered_qty - (returned_qty)
            if remaining_qty > 0:
                product_obj = RentalProduct.objects.get(pk=product_id)
                pending_return_items.append(
                    {
                        "product_id": product_obj.equipment_id,
                        "product_name": product_obj.equipment_name,
                        "delivered_qty": total_delivered_qty,
                        "returned_qty": returned_qty,
                        "remaining_qty": remaining_qty,
                    }
                )

        context = {
            "order": order_id,
            "order_items": pending_return_items,
            "return_order_created_at": return_order_created_at,
            "return_order_obj":return_order
        }
        return render(request, self.template_name, context)


class CreateReturnDeliveryView(ViewMixin):
    def post(self, request, *args, **kwargs):
        try:
            print(request.POST)
            return_order_id = request.POST.get("order_id")
            return_order = ReturnOrder.objects.get(order__order_id=return_order_id)
            returned_pickup_date = request.POST.get("returned_pickup_date")
            returned_delivery_date = request.POST.get("returned_delivery_date")
            returned_pickup_site = request.POST.get("returned_pickup_site")
            returned_delivery_site = request.POST.get("returned_delivery_site")
            return_po_number = request.POST.get("return_po_number")
            shipping_carrier = request.POST.get("shipping_carrier")
            deliver_to_customer = request.POST.get("createcheckbox") == "on"
            today_date = datetime.datetime.now().date()
            removal_date = today_date + datetime.timedelta(days=5)

            order = request.POST.get("order") or None
            if order:
                order = Order.objects.filter(order_id=order).first()
                if not order:
                    return JsonResponse({"status": "error", "message": "Invalid Order ID. Order does not exist."})
                if order.order_id == return_order_id:
                    return JsonResponse(
                        {"status": "error", "message": "Order ID and Return Order ID cannot be the same."}
                    )

            success_message = ""
            if deliver_to_customer and order:
                selected_products_json = request.POST.get("selected_products")
                selected_products = json.loads(selected_products_json)

                for item in selected_products:
                    product_id = item["id"]
                    qty = item["quantity"]
                    product = RentalProduct.objects.get(equipment_id=product_id)
                    unique_delivery_id = tasks.generate_delivery_id(order)
                    Delivery.objects.create(
                        unique_delivery_id=unique_delivery_id,
                        order=order,
                        product=product,
                        delivery_qty=int(qty),
                        delivery_date=returned_delivery_date,
                        contract_start_date=today_date,
                        pickup_date=returned_pickup_date,
                        pickup_site=returned_pickup_site,
                        delivery_site=returned_delivery_site,
                        po_number=return_po_number,
                        shipping_carrier=shipping_carrier,
                        delivery_status=Delivery.STAGE_1,
                        direct_delivery=True,
                    )

                    return_delivery = ReturnDelivery.objects.create(
                        return_order=return_order,
                        returned_pickup_date=returned_pickup_date,
                        returned_delivery_date=returned_delivery_date,
                        returned_pickup_site=returned_pickup_site,
                        contract_end_date=today_date,
                        returned_delivery_site=returned_delivery_site,
                        return_po_number=return_po_number,
                        removal_date=removal_date,
                        shipping_carrier=shipping_carrier,
                        deliver_to_customer=deliver_to_customer,
                        direct_delivery=True,
                    )

                    print("ReturnDelivery: create Successfully   ")
                    product = RentalProduct.objects.get(equipment_id=product_id)
                    ReturnDeliveryItem.objects.create(
                        return_delivery=return_delivery, product=product, return_qty=int(qty)
                    )
                    print("ReturnDeliveryItem: create Successfully   ")
                    success_message = "Delivery Created Successfully!"
            else:
                return_delivery = ReturnDelivery.objects.create(
                    return_order=return_order,
                    returned_pickup_date=returned_pickup_date,
                    returned_delivery_date=returned_delivery_date,
                    returned_pickup_site=returned_pickup_site,
                    returned_delivery_site=returned_delivery_site,
                    return_po_number=return_po_number,
                    shipping_carrier=shipping_carrier,
                    contract_end_date=today_date,
                    removal_date=removal_date,
                    deliver_to_customer=deliver_to_customer,
                )

                selected_products_json = request.POST.get("selected_products")
                selected_products = json.loads(selected_products_json)

                for item in selected_products:
                    product_id = item["id"]
                    qty = item["quantity"]

                    product = RentalProduct.objects.get(equipment_id=product_id)
                    ReturnDeliveryItem.objects.create(
                        return_delivery=return_delivery, product=product, return_qty=int(qty)
                    )
                success_message = "Return Delivery Created Successfully!"

            return JsonResponse({"status": "success", "message": success_message})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})


class CreateReturnDeliveryListAjaxView(CustomDataTableMixin):
    """AJAX view for listing  Return delivery  in a DataTable format."""

    def _get_actions(self, obj):
        """Generate action buttons for delivery orders."""
        t = get_template("rental/orders/return_delivery_actions.html")
        edit_url = reverse("rental:rent_process:return-delivery-edit", kwargs={"pk": obj})
        remove_url = "#"
        return t.render(
            {
                "edit_url": edit_url,
                "remove_url": remove_url,
                "delivery": obj,
                "request": self.request,
            }
        )

    def get_queryset(self):
        """Returns a queryset of deliveries for the given order_id in the URL."""
        order_id = self.kwargs.get("order_id")
        return_orders = ReturnOrder.objects.filter(order__order_id=order_id)
        return_deliveries = ReturnDelivery.objects.filter(return_order__in=return_orders).exclude(direct_delivery=True)
        return_items = ReturnDeliveryItem.objects.filter(
            return_delivery__in=return_deliveries,
            return_status__in=[
                ReturnDeliveryItem.STAGE_5,
                ReturnDeliveryItem.STAGE_6,
                ReturnDeliveryItem.STAGE_7,
                ReturnDeliveryItem.STAGE_8,
            ],
        )
        return return_items

    def filter_queryset(self, qs):
        """Return filtered queryset based on search input."""
        if self.search:
            return qs.filter(
                Q(return_delivery__return_order__order__order_id__icontains=self.search)
                | Q(return_delivery__return_unique_id__icontains=self.search)
                | Q(return_status__icontains=self.search)
                | Q(return_delivery__return_order__customer__name__icontains=self.search)
            )
        return qs

    def _get_returned_pickup_date(self, return_delivery_obj):

        today_date = now().date().isoformat()
        returned_pickup_date = (
            return_delivery_obj.returned_pickup_date.isoformat() if return_delivery_obj.returned_pickup_date else None
        )

        t = get_template("rental/rent_process/delivery_returned_pickup_date.html")
        return t.render(
            {
                "return_delivery_obj": return_delivery_obj,
                "today_date": today_date,
                "returned_pickup_date": returned_pickup_date,
            }
        )

    def prepare_results(self, qs):
        """Format delivery data for DataTables with grouped deliveries."""
        qs = sorted(qs, key=lambda x: x.return_qty)

        return_map = {}
        for return_item in qs:
            return_delivery = return_item.return_delivery
            return_id = return_delivery.return_unique_id

            if return_id not in return_map:
                return_map[return_id] = {
                    "return_id": return_id,
                    "delivery_id": return_delivery.pk,
                    "total_qty": 0,
                    "contract_end_date": (
                        return_delivery.contract_end_date.strftime("%d %B, %Y")
                        if return_delivery.contract_end_date
                        else "-"
                    ),
                    "returned_pickup_date": self._get_returned_pickup_date(return_delivery),
                    "removal_date": (
                        return_delivery.removal_date.strftime("%d %B, %Y") if return_delivery.removal_date else "-"
                    ),
                    "actions": self._get_actions(return_id),
                    "products": "",
                }

            return_map[return_id]["total_qty"] += return_item.return_qty
            item_index = len(return_map[return_id]["products"].split("<tr>")) - 1
            item_row = self._get_item_row(return_item, item_index + 1)
            return_map[return_id]["products"] += item_row

        data = []
        for value in return_map.values():
            if value["products"]:
                value["products"] = self._wrap_item_table(value["products"], value["return_id"], value["delivery_id"])
            data.append(value)

        return data

    def _get_item_row(self, return_item, index):
        """Generate a table row for an individual return item with a dynamic Sr No."""

        if not return_item.product:
            return ""

        return f"""
            <tr>
                <td>{index}</td>
                <td>{return_item.product.equipment_id if return_item.product else '-'}</td>
                <td>{return_item.product.equipment_name}</td>
                <td>
                    <input type="text" name="delivery_site" class="form-control delivery-site-input"
                        value="{return_item.return_delivery.returned_delivery_site if return_item.return_delivery else ''}"
                        data-return-delivery-id="{return_item.return_delivery.return_unique_id if return_item.return_delivery else ''}">
                </td>
                <td>
                    <input type="number" name="quantity" class="form-control quantity-input"
                        value="{return_item.return_qty}" min="1"
                        data-return-delivery-item-pk="{return_item.pk}">
                </td>
            </tr>
        """

    def _wrap_item_table(self, rows, return_id, delivery_id):
        """Wrap item rows in a full table structure with a unique ID."""
        return f"""
            <table class="table table-striped table-bordered return-pick-up-ticket-items-table"
                id="return-items-table-{return_id}" data-table-id="{delivery_id}">
                <thead>
                    <tr class="text-center">
                        <th colspan="5" class="align-top">Items Information</th>
                    </tr>
                    <tr>
                        <th>Sr No</th>
                        <th>Internal Id</th>
                        <th>Items</th>
                        <th>Delivery Site</th>
                        <th>Quantity</th>
                    </tr>
                </thead>
                <tbody class="table-striped">
                    {rows}
                </tbody>
            </table>
        """

    def get_ordering(self, qs):
        """Handle ordering for DataTable columns."""
        column_map = {
            "0": "return_delivery__return_unique_id",
            "1": "return_qty",
            "2": "return_delivery__removal_date",
        }
        order_column_index = self.request.GET.get("order[0][column]", "0")
        order_by = column_map.get(order_column_index, "return_delivery__return_unique_id")
        return qs.order_by(order_by)

    def get(self, request, *args, **kwargs):
        """Return JSON response for DataTables."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

    def get_context_data(self, request):
        try:
            context = super().get_context_data(request)
            return context
        except Exception as e:
            return {"error": str(e)}


class ReturnDeliveryUpdateView(ViewMixin):
    def get(self, request, *args, **kwargs):
        # obj = get_object_or_404(ReturnDelivery, return_unique_id=self.kwargs["pk"]).exclude(direct_delivery=True)
        obj = get_object_or_404(
            ReturnDelivery.objects.exclude(direct_delivery=True), return_unique_id=self.kwargs["pk"]
        )
        return_items = obj.return_items.all
        context = {
            "obj": obj,
            "return_items": return_items,
        }
        return render(request, "rental/orders/update_return_delivery.html", context)

    def post(self, request, *args, **kwargs):
        obj = get_object_or_404(ReturnDelivery, return_unique_id=self.kwargs["pk"])
        removal_date = request.POST.get("removal_date")
        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else {}
        except json.JSONDecodeError:
            data = {}

        selected_products = data.get("selected_products", [])
        deliver_to_customer = data.get("deliver_to_customer", False)
        order = data.get("order")
        return_order_id = order
        print("return_order_id: ", return_order_id)
        if deliver_to_customer:
            return_order = ReturnOrder.objects.get(order__order_id=return_order_id)
        if order:
            order = Order.objects.filter(order_id=order).first()
            if not order:
                return JsonResponse({"status": "error", "message": "Invalid Order ID. Order does not exist."})
        else:
            order = None

        if removal_date:
            obj.removal_date = removal_date
            obj.save()
            return JsonResponse({"status": "success", "message": "Removal date updated successfully!"})

        if deliver_to_customer:
            for product in selected_products:
                product_id = product.get("id")
                quantity = product.get("quantity")
                product1 = RentalProduct.objects.get(equipment_id=product_id)
                return_item = ReturnDeliveryItem.objects.filter(return_delivery=obj, product_id=product_id).first()
                update_qty = return_item.return_qty - int(quantity)
                if return_item:
                    return_item.return_qty = update_qty
                    return_item.save()

                unique_delivery_id = tasks.generate_delivery_id(order)
                product_id = RentalProduct.objects.get(equipment_id=product_id)
                Delivery.objects.create(
                    unique_delivery_id=unique_delivery_id,
                    order=order,
                    product=product_id,
                    delivery_qty=quantity,
                    delivery_date=obj.returned_delivery_date,
                    pickup_date=obj.returned_pickup_date,
                    pickup_site=obj.returned_pickup_site,
                    delivery_site=obj.returned_delivery_site,
                    po_number=obj.return_po_number,
                    shipping_carrier=obj.shipping_carrier,
                    delivery_status=Delivery.STAGE_1,
                    direct_delivery=True,
                )
                return_delivery = ReturnDelivery.objects.create(
                    return_order=return_order,
                    returned_pickup_date=obj.returned_pickup_date,
                    returned_delivery_date=obj.returned_delivery_date,
                    returned_pickup_site=obj.returned_pickup_site,
                    returned_delivery_site=obj.returned_delivery_site,
                    return_po_number=obj.return_po_number,
                    removal_date=obj.removal_date,
                    shipping_carrier=obj.shipping_carrier,
                    deliver_to_customer=deliver_to_customer,
                    direct_delivery=True,
                )

                ReturnDeliveryItem.objects.create(
                    return_delivery=return_delivery, product=product1, return_qty=int(quantity)
                )

            # obj.deliver_to_customer = True
            # obj.save()
            return JsonResponse({"status": "success", "message": "Delivery created successfully for customer!"})

        else:
            for product in selected_products:
                product_id = product.get("id")
                quantity = product.get("quantity")

                return_item = ReturnDeliveryItem.objects.filter(return_delivery=obj, product_id=product_id).first()
                if return_item:
                    return_item.return_qty = quantity
                    return_item.save()

            return JsonResponse({"status": "success", "message": "products quantity updated successfully!"})


class UpdateReturnDeliverySiteView(ViewMixin):
    """Class-Based View for updating Delivery Site"""

    def post(self, request, *args, **kwargs):
        return_delivery_id = request.POST.get("return_delivery_id")
        new_delivery_site = request.POST.get("new_delivery_site")

        try:
            return_delivery = ReturnDelivery.objects.get(return_unique_id=return_delivery_id)
            return_delivery.returned_delivery_site = new_delivery_site
            return_delivery.save()
            return JsonResponse({"status": "success", "message": "Delivery site updated successfully!"})
        except ReturnDelivery.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Return Delivery not found!"})


class UpdateReturnDeliveryQtyView(ViewMixin):
    """Class-Based View for updating Quantity"""

    def post(self, request, *args, **kwargs):
        return_delivery_item_pk = request.POST.get("return_delivery_item_pk")
        new_quantity = request.POST.get("new_quantity")

        try:
            return_item = ReturnDeliveryItem.objects.get(pk=return_delivery_item_pk)
            return_item.return_qty = new_quantity
            return_item.save()
            return JsonResponse({"status": "success", "message": "Quantity updated successfully!"})
        except ReturnDeliveryItem.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Return Item not found!"})


class ReturnPickupListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Return Pickups in a DataTable format."""

    def get_queryset(self):
        """Returns a queryset of return deliveries based on order."""
        order_id = self.kwargs.get("order_id")

        return_orders = ReturnOrder.objects.filter(order__order_id=order_id)
        return_deliveries = ReturnDelivery.objects.filter(return_order__in=return_orders).exclude(direct_delivery=True)
        return_items = ReturnDeliveryItem.objects.filter(
            return_delivery__in=return_deliveries,
            return_status__in=[
                ReturnDeliveryItem.STAGE_5,
                ReturnDeliveryItem.STAGE_6,
                ReturnDeliveryItem.STAGE_7,
                ReturnDeliveryItem.STAGE_8,
            ],
        )

        return return_items

    def _get_returned_pickup_date(self, return_delivery_obj):

        today_date = now().date().isoformat()
        returned_pickup_date = (
            return_delivery_obj.returned_pickup_date.isoformat() if return_delivery_obj.returned_pickup_date else None
        )

        t = get_template("rental/rent_process/delivery_returned_pickup_date.html")
        return t.render(
            {
                "return_delivery_obj": return_delivery_obj,
                "today_date": today_date,
                "returned_pickup_date": returned_pickup_date,
            }
        )

    def filter_queryset(self, qs):
        """Return filtered queryset based on search input."""
        if self.search:
            return qs.filter(
                Q(return_delivery__return_order__order__order_id__icontains=self.search)
                | Q(return_delivery__return_unique_id__icontains=self.search)
                | Q(return_status__icontains=self.search)
                | Q(return_delivery__return_order__customer__name__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Format return delivery data for DataTables with grouped items."""
        qs = sorted(qs, key=lambda x: x.return_qty)

        return_map = {}
        for return_item in qs:
            return_delivery = return_item.return_delivery
            return_id = return_delivery.return_unique_id

            if return_id not in return_map:
                return_map[return_id] = {
                    "return_id": return_id,
                    "delivery_id": return_delivery.pk,
                    "total_qty": 0,
                    # "returned_pickup_date": (
                    #     return_delivery.returned_pickup_date.strftime("%d %B, %Y")
                    #     if return_delivery.returned_pickup_date
                    #     else "-"
                    # ),
                    "returned_pickup_date": self._get_returned_pickup_date(return_delivery),
                    "delivery_date": (
                        return_delivery.removal_date.strftime("%d %B, %Y") if return_delivery.removal_date else "-"
                    ),
                    "products": "",
                }

            return_map[return_id]["total_qty"] += return_item.return_qty
            item_index = len(return_map[return_id]["products"].split("<tr>")) - 1
            item_row = self._get_item_row(return_item, item_index + 1)
            return_map[return_id]["products"] += item_row

        data = []
        for value in return_map.values():
            if value["products"]:
                value["products"] = self._wrap_item_table(value["products"], value["return_id"], value["delivery_id"])
            data.append(value)

        return data

    def _get_item_row(self, return_item, index):
        """Generate a table row for an individual return item with a dynamic Sr No."""
        selected_none = (
            ""
            if return_item.return_status
            in [ReturnDeliveryItem.STAGE_6, ReturnDeliveryItem.STAGE_7, ReturnDeliveryItem.STAGE_8]
            else "selected"
        )
        selected_return_pick_up_ticket = "selected" if return_item.return_status == "Return Pick Up Ticket" else ""
        if not return_item.product:
            return ""

        return f"""
            <tr>
                <td>{index}</td>
                <td>{return_item.product.equipment_id if return_item.product else '-'}</td>
                <td>{return_item.product.equipment_name}</td>
                <td>
                    {return_item.return_qty}
                </td>
                <td>
                    <select name="status" class="select2 form-control wizard-required another-select-return-pick-up-ticket"
                            data-return-delivery-id="{return_item.return_delivery.return_unique_id}" data-return-delivery-item-pk="{return_item.pk}">
                        <option value="" disabled {selected_none}>None</option>
                        <option value="Return Pick Up Ticket" {selected_return_pick_up_ticket}>Loaded</option>
                    </select>
                </td>
            </tr>
        """

    def _wrap_item_table(self, rows, return_id, delivery_id):
        """Wrap item rows in a full table structure with a unique ID."""
        return f"""
            <table class="table table-striped table-bordered return-pick-up-ticket-items-table"
                id="return-items-table-{return_id}" data-table-id="{delivery_id}">
                <thead>
                    <tr class="text-center">
                        <th colspan="5" class="align-top">Return Items Information</th>
                    </tr>
                    <tr>
                        <th>Sr No</th>
                        <th>Internal Id</th>
                        <th>Items</th>
                        <th>Quantity</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody class="table-striped">
                    {rows}
                </tbody>
            </table>
        """

    def get_ordering(self, qs):
        """Handle ordering for DataTable columns."""
        column_map = {
            "0": "return_delivery__return_unique_id",
            "1": "return_qty",
            "2": "return_delivery__returned_pickup_site",
        }
        order_column_index = self.request.GET.get("order[0][column]", "0")
        order_by = column_map.get(order_column_index, "return_delivery__return_unique_id")
        return qs.order_by(order_by)

    def get(self, request, *args, **kwargs):
        """Return JSON response for DataTables."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

    def get_context_data(self, request):
        try:
            context = super().get_context_data(request)
            return context
        except Exception as e:
            return {"error": str(e)}


class UpdateReturnPickupDateView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            delivery_id = data.get("delivery_id")
            returned_pickup_date = data.get("returned_pickup_date")

            if not delivery_id or not returned_pickup_date:
                return JsonResponse({"success": False, "error": "Invalid data received."})

            # Ensure the date format is correct
            try:
                returned_pickup_date = datetime.datetime.strptime(returned_pickup_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid date format."})

            # Fetch and update the delivery object
            return_deliverys = ReturnDelivery.objects.filter(return_unique_id=delivery_id)
            if not return_deliverys:
                return JsonResponse({"success": False, "error": "Delivery not found."})
            for return_delivery in return_deliverys:
                return_delivery.returned_pickup_date = returned_pickup_date
                return_delivery.save()

            print(f"Updated return_delivery {delivery_id} with new date: {returned_pickup_date}")
            return JsonResponse({"success": True, "message": "Checkout date updated successfully."})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data."})
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"})


class ReturnPickupStatusView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        return_delivery_id = data.get("return_delivery_id")
        return_delivery_item_pk = data.get("return_delivery_item_pk")
        order_id = data.get("order_id")
        global_status_change = data.get("global_status_change", False)
        try:
            # **Single Delivery Update**
            if return_delivery_id:
                return self.update_single_delivery(return_delivery_item_pk)

            # **Global Order-Wide Update**
            elif order_id and global_status_change:
                return self.update_global_deliveries(return_delivery_id)

            return JsonResponse({"success": False, "error": "Invalid request parameters"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"})

    def update_single_delivery(self, return_delivery_item_pk):
        """Handles updating a single delivery's status"""
        delivery = ReturnDeliveryItem.objects.filter(pk=return_delivery_item_pk).first()

        if delivery:
            delivery.return_status = ReturnDeliveryItem.STAGE_6
            delivery.save()

            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": f"Delivery with ID {return_delivery_item_pk} not found"})

    def update_global_deliveries(self, return_delivery_id):
        """Handles global status change for all deliveries under an order"""
        delivery_objs = ReturnDeliveryItem.objects.filter(return_delivery__return_unique_id=return_delivery_id)

        for delivery_obj in delivery_objs:
            delivery_obj.return_status = ReturnDeliveryItem.STAGE_6
            delivery_obj.save()

        return JsonResponse(
            {
                "success": True,
            }
        )


class CheckInListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Return Pickups in a DataTable format."""

    def get_queryset(self):
        """Returns a queryset of return deliveries based on order."""
        order_id = self.kwargs.get("order_id")

        return_orders = ReturnOrder.objects.filter(order__order_id=order_id)
        return_deliveries = ReturnDelivery.objects.filter(return_order__in=return_orders).exclude(direct_delivery=True)
        return_items = ReturnDeliveryItem.objects.filter(
            return_delivery__in=return_deliveries,
            return_status__in=[ReturnDeliveryItem.STAGE_6, ReturnDeliveryItem.STAGE_7, ReturnDeliveryItem.STAGE_8],
        )

        return return_items

    def _get_check_in_date(self, return_delivery_obj):
        # Get today's date in ISO format
        today_date = datetime.datetime.utcnow().date().isoformat()

        # Get the check-in date from the return_delivery_obj, if available
        check_in_date = return_delivery_obj.check_in_date
        if check_in_date:
            check_in_date = check_in_date.date().isoformat()  # Strip time and timezone

        # Render the template with the provided context
        t = get_template("rental/rent_process/delivery_check_in_date.html")
        return t.render(
            {"return_delivery_obj": return_delivery_obj, "today_date": today_date, "check_in_date": check_in_date}
        )

    def filter_queryset(self, qs):
        """Return filtered queryset based on search input."""
        if self.search:
            return qs.filter(
                Q(return_delivery__return_order__order__order_id__icontains=self.search)
                | Q(return_delivery__return_unique_id__icontains=self.search)
                | Q(return_status__icontains=self.search)
                | Q(return_delivery__return_order__customer__name__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Format return delivery data for DataTables with grouped items."""
        qs = sorted(qs, key=lambda x: x.return_qty)

        return_map = {}
        for return_item in qs:
            return_delivery = return_item.return_delivery
            return_id = return_delivery.return_unique_id

            if return_id not in return_map:
                return_map[return_id] = {
                    "return_id": return_id,
                    "delivery_id": return_delivery.pk,
                    "total_qty": 0,
                    # "returned_pickup_date": (
                    #     return_delivery.returned_pickup_date.strftime("%d %B, %Y")
                    #     if return_delivery.returned_pickup_date
                    #     else "-"
                    # ),
                    "returned_pickup_date": self._get_check_in_date(return_delivery),
                    "products": "",
                }

            return_map[return_id]["total_qty"] += return_item.return_qty
            item_index = len(return_map[return_id]["products"].split("<tr>")) - 1
            item_row = self._get_item_row(return_item, item_index + 1)
            return_map[return_id]["products"] += item_row

        data = []
        for value in return_map.values():
            if value["products"]:
                value["products"] = self._wrap_item_table(value["products"], value["return_id"], value["delivery_id"])
            data.append(value)

        return data

    def _get_item_row(self, return_item, index):
        """Generate a table row for an individual return item with a dynamic Sr No."""
        # selected_none = "" if return_item.return_status in [ReturnDeliveryItem.STAGE_6] else "selected"
        # selected_return_pick_up_ticket = "selected" if return_item.return_status == "Return Pick Up Ticket" else ""
        if not return_item.product:
            return ""
        stock_adjustments = return_item.product.stock_adjustments.all()  # This returns a queryset
        stock_adjustments_pk = (
            stock_adjustments.first().pk if stock_adjustments.exists() else ""
        )  # Access the first element's pk
        stock_adjustments_stock = (
            stock_adjustments.first().quantity if stock_adjustments.exists() else ""
        )  # Access the first element's pk
        return f"""
            <tr>
                <td>{index}</td>
                <td>{return_item.product.equipment_id if return_item.product else '-'}</td>
                <td>{return_item.product.equipment_name}</td>
                <td>
                    <input type="text"
                        id="quantity-{return_item.product.equipment_id}"
                        data-return-delivery-unique_id="{return_item.return_delivery.return_unique_id}"
                        data-pick-up-ticket-items-pk="{return_item.pk}"
                        data-stock-id="{stock_adjustments_pk}"
                        data-value="{return_item.return_qty}"
                        data-current-stock="{stock_adjustments_stock}"
                        value="{return_item.return_qty}"
                        class="form-control check-in-qty wizard-required">
                    <small class="quantityMessage text-danger"></small>
                </td>
            </tr>
        """

    def _wrap_item_table(self, rows, return_id, delivery_id):
        """Wrap item rows in a full table structure with a unique ID."""
        return f"""
            <table class="table table-striped table-bordered return-pick-up-ticket-items-table"
                id="return-items-table-{return_id}" data-table-id="{delivery_id}">
                <thead>
                    <tr class="text-center">
                        <th colspan="5" class="align-top">Return Items Information</th>
                    </tr>
                    <tr>
                        <th>Sr No</th>
                        <th>Internal Id</th>
                        <th>Items</th>
                        <th>Quantity</th>
                    </tr>
                </thead>
                <tbody class="table-striped">
                    {rows}
                </tbody>
            </table>
        """

    def get_ordering(self, qs):
        """Handle ordering for DataTable columns."""
        column_map = {
            "0": "return_delivery__return_unique_id",
            "1": "return_qty",
            "2": "return_delivery__return_date",
        }
        order_column_index = self.request.GET.get("order[0][column]", "0")
        order_by = column_map.get(order_column_index, "return_delivery__return_unique_id")
        return qs.order_by(order_by)

    def get(self, request, *args, **kwargs):
        """Return JSON response for DataTables."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

    def get_context_data(self, request):
        try:
            context = super().get_context_data(request)
            return context
        except Exception as e:
            return {"error": str(e)}


class UpdateCheckInDateView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            delivery_id = data.get("delivery_id")
            check_in_date = data.get("check_in_date")

            if not delivery_id or not check_in_date:
                return JsonResponse({"success": False, "error": "Invalid data received."})

            # Ensure the date format is correct
            try:
                check_in_date = datetime.datetime.strptime(check_in_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid date format."})

            # Fetch and update the delivery object
            return_deliverys = ReturnDelivery.objects.filter(return_unique_id=delivery_id)
            if not return_deliverys:
                return JsonResponse({"success": False, "error": "Delivery not found."})
            for return_delivery in return_deliverys:
                return_delivery.check_in_date = check_in_date
                return_delivery.save()

            print(f"Updated return_delivery {delivery_id} with new date: {check_in_date}")
            return JsonResponse({"success": True, "message": "Checkout date updated successfully."})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data."})
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"})


class ReturnDeliveryItemMismatchUpdateView(View):
    def post(self, request, pk):
        # Retrieve plus and minus quantities from POST data.
        pulse_quantity = request.POST.get("pulse_quantity")
        minus_quantity = request.POST.get("minus_quantity")
        print("pulse_quantity:", pulse_quantity)
        print("minus_quantity:", minus_quantity)

        if pulse_quantity is None or minus_quantity is None:
            return JsonResponse({"success": False, "message": "Plus or minus quantity missing."}, status=400)

        try:
            plus_val = int(pulse_quantity)
            minus_val = int(minus_quantity)
        except ValueError:
            return JsonResponse({"success": False, "message": "Invalid quantity values."}, status=400)

        # Compute the net mismatch.
        # For example, if minus (missing qty) is greater than plus (extra qty), then net_mismatch is positive.
        net_mismatch = minus_val - plus_val
        print("Calculated net_mismatch:", net_mismatch)

        # Get the ReturnDeliveryItem
        item = get_object_or_404(ReturnDeliveryItem, pk=pk)
        try:
            print("Before item.return_qty:", item.return_qty)
            # Subtract the net mismatch from the current return_qty
            item.return_qty -= net_mismatch
            item.save()
            print("After item.return_qty:", item.return_qty)
            return JsonResponse({"success": True, "message": "Return Delivery Item updated."})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=400)


class InspectionListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Return Pickups in a DataTable format."""

    def get_queryset(self):
        """Returns a queryset of return deliveries based on order."""
        order_id = self.kwargs.get("order_id")

        return_orders = ReturnOrder.objects.filter(order__order_id=order_id)
        return_deliveries = ReturnDelivery.objects.filter(return_order__in=return_orders).exclude(direct_delivery=True)
        return_items = ReturnDeliveryItem.objects.filter(
            return_delivery__in=return_deliveries,
            return_status__in=[ReturnDeliveryItem.STAGE_7, ReturnDeliveryItem.STAGE_8],
        )

        return return_items

    def _get_inspection_date(self, return_delivery_obj):
        # Get today's date in ISO format
        today_date = datetime.datetime.utcnow().date().isoformat()

        # Get the check-in date from the return_delivery_obj, if available
        inspection_date = return_delivery_obj.inspection_date
        print("inspection_date: ======================++>>>", inspection_date)
        if inspection_date:
            inspection_date = inspection_date.isoformat()  # Strip time and timezone

        # Render the template with the provided context
        t = get_template("rental/rent_process/delivery_inspection_date.html")
        return t.render(
            {"return_delivery_obj": return_delivery_obj, "today_date": today_date, "inspection_date": inspection_date}
        )

    def filter_queryset(self, qs):
        """Return filtered queryset based on search input."""
        if self.search:
            return qs.filter(
                Q(return_delivery__return_order__order__order_id__icontains=self.search)
                | Q(return_delivery__return_unique_id__icontains=self.search)
                | Q(return_status__icontains=self.search)
                | Q(return_delivery__return_order__customer__name__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Format return delivery data for DataTables with grouped items."""
        qs = sorted(qs, key=lambda x: x.return_qty)

        return_map = {}
        for return_item in qs:
            return_delivery = return_item.return_delivery
            return_id = return_delivery.return_unique_id

            if return_id not in return_map:
                return_map[return_id] = {
                    "return_id": return_id,
                    "delivery_id": return_delivery.pk,
                    "total_qty": 0,
                    "check_in_date": (
                        return_delivery.check_in_date.strftime("%d %B, %Y") if return_delivery.check_in_date else "-"
                    ),
                    "inspection_date": self._get_inspection_date(return_delivery),
                    "products": "",
                }

            return_map[return_id]["total_qty"] += return_item.return_qty
            item_index = len(return_map[return_id]["products"].split("<tr>")) - 1
            item_row = self._get_item_row(return_item, item_index + 1)
            return_map[return_id]["products"] += item_row

        data = []
        for value in return_map.values():
            if value["products"]:
                value["products"] = self._wrap_item_table(value["products"], value["return_id"], value["delivery_id"])
            data.append(value)

        return data

    def _get_item_row(self, return_item, index):
        """Generate a table row for an individual return item with a dynamic Sr No."""
        if not return_item.product:
            return ""
        stock_adjustments = return_item.product.stock_adjustments.all()  # This returns a queryset
        stock_adjustments_pk = stock_adjustments.first().pk if stock_adjustments.exists() else ""
        stock_adjustments_stock = stock_adjustments.first().quantity if stock_adjustments.exists() else ""
        # Build the AJAX URL using reverse:
        complete_inspection_url = reverse("rental:rent_process:mark-inspection-completed-ajax", args=[return_item.pk])

        # Only show the mark-completed block if status is not already completed.
        if return_item.return_status != ReturnDeliveryItem.STAGE_8:
            mark_block = f"""
                <span class="info mark-completed">
                    <i class="ft-info"></i> Mark inspection as completed!!
                    <a href="#" class="marked" data-url="{complete_inspection_url}">
                        <i class="ft-check success" id="completed-inspection-product-stock"
                        data-item-stock-pk="{return_item.pk}"
                        data-item-quantity="{return_item.return_qty}"></i>
                    </a>
                    <a href="#" class="inspection-adjust-stock-cancel" data-stock-id="{stock_adjustments_pk}" data-pick-up-ticket-items-pk="{return_item.pk}" data-mismatched-quantity="0"><i class="ft-x danger"></i></a>
                </span>
            """
        else:
            mark_block = ""

        return f"""
            <tr>
                <td>{index}</td>
                <td>{return_item.product.equipment_id if return_item.product else '-'}</td>
                <td>{return_item.product.equipment_name}</td>
                <td>
                    <input type="text"
                        id="quantity-{return_item.product.equipment_id}"
                        data-return-delivery-unique_id="{return_item.return_delivery.return_unique_id}"
                        data-pick-up-ticket-items-pk="{return_item.pk}"
                        data-stock-id="{stock_adjustments_pk}"
                        data-value="{return_item.return_qty}"
                        data-current-stock="{stock_adjustments_stock}"
                        value="{return_item.return_qty}"
                        class="form-control inspection-qty wizard-required">
                    <small class="quantityMessage text-danger"></small>
                    {mark_block}
                </td>
            </tr>
        """

    def _wrap_item_table(self, rows, return_id, delivery_id):
        """Wrap item rows in a full table structure with a unique ID."""
        return f"""
            <table class="table table-striped table-bordered inspection-items-table"
                id="return-items-table-{return_id}" data-table-id="{delivery_id}">
                <thead>
                    <tr class="text-center">
                        <th colspan="5" class="align-top">Return Items Information</th>
                    </tr>
                    <tr>
                        <th>Sr No</th>
                        <th>Internal Id</th>
                        <th>Items</th>
                        <th>Quantity</th>
                    </tr>
                </thead>
                <tbody class="table-striped">
                    {rows}
                </tbody>
            </table>
        """

    def get_ordering(self, qs):
        """Handle ordering for DataTable columns."""
        column_map = {
            "0": "return_delivery__return_unique_id",
            "1": "return_qty",
            "2": "return_delivery__return_date",
        }
        order_column_index = self.request.GET.get("order[0][column]", "0")
        order_by = column_map.get(order_column_index, "return_delivery__return_unique_id")
        return qs.order_by(order_by)

    def get(self, request, *args, **kwargs):
        """Return JSON response for DataTables."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

    def get_context_data(self, request):
        try:
            context = super().get_context_data(request)
            return context
        except Exception as e:
            return {"error": str(e)}


class MarkInspectionCompletedAjaxView(View):
    def post(self, request, pk):
        # Get the ReturnDeliveryItem instance
        item = get_object_or_404(ReturnDeliveryItem, pk=pk)
        # Update its status to "Inspection Completed" (STAGE_8)
        item.return_status = ReturnDeliveryItem.STAGE_8
        item.save()
        return JsonResponse({"success": True, "message": "Inspection marked as completed."})


class UpdateInspectionDateView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            delivery_id = data.get("delivery_id")
            inspection_date = data.get("inspection_date")

            if not delivery_id or not inspection_date:
                return JsonResponse({"success": False, "error": "Invalid data received."})

            # Ensure the date format is correct
            try:
                inspection_date = datetime.datetime.strptime(inspection_date, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"success": False, "error": "Invalid date format."})

            # Fetch and update the delivery object
            return_deliverys = ReturnDelivery.objects.filter(return_unique_id=delivery_id)
            if not return_deliverys:
                return JsonResponse({"success": False, "error": "Delivery not found."})
            for return_delivery in return_deliverys:
                return_delivery.inspection_date = inspection_date
                return_delivery.save()

            print(f"Updated return_delivery {delivery_id} with new date: {inspection_date}")
            return JsonResponse({"success": True, "message": "Checkout date updated successfully."})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data."})
        except Exception as e:
            return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"})


class UpdateCheckInStatusView(View):
    def post(self, request, *args, **kwargs):
        try:
            order_identifier = self.kwargs.get("order_id")  # This is your order_id string, e.g., "O20250200001"

            # Filter by the order_id field, not the primary key.
            order_obj = Order.objects.filter(order_id=order_identifier).first()
            if not order_obj:
                return JsonResponse({"success": False, "error": "Order not found"})

            return_order_obj = ReturnOrder.objects.filter(order=order_obj).first()
            if not return_order_obj:
                return JsonResponse({"success": False, "error": "Return order not found"})

            return_order_objs = ReturnDelivery.objects.filter(return_order=return_order_obj)
            if not return_order_objs.exists():
                return JsonResponse({"success": False, "error": "Return deliveries not found"})

            # Update the return status of ReturnDeliveryItems in bulk
            updated_count = 0
            for return_delivery in return_order_objs:
                updated_count += ReturnDeliveryItem.objects.filter(
                    return_delivery=return_delivery, return_status=ReturnDeliveryItem.STAGE_6
                ).update(return_status=ReturnDeliveryItem.STAGE_7)

            if updated_count == 0:
                return JsonResponse({"success": False, "error": "No items to update"})

            return JsonResponse({"success": True, "message": "Status updated successfully"})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})


class CustomerAddressAjaxView(View):
    def get(self, request, *args, **kwargs):
        customer_id = request.GET.get("customer_id")
        data = {}
        if customer_id:
            try:
                customer = RentalCustomer.objects.get(pk=customer_id)
                data["address"] = (
                    customer.billing_address_1 if customer.billing_address_1 else customer.billing_address_2
                )
            except RentalCustomer.DoesNotExist:
                data["address"] = ""
        return JsonResponse(data)
class CustomerSearchView(View):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("q", "")  # Get search term
        customers = RentalCustomer.objects.only("id", "name").order_by("name")
        if term:
            customers = customers.filter(name__icontains=term)
        else:
            customers = customers[:7]  # Return first 7 when term is empty
        data = [{"id": c.pk, "text": c.name} for c in customers]
        return JsonResponse({"results": data})
class AccountManagerSearchView(View):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("q", "")
        managers = AccountManager.objects.all().order_by("name")
        if term:
            managers = managers.filter(name__icontains=term)
        else:
            managers = managers[:7]  # Return first 7 when no term is provided
        data = [{"id": m.pk, "text": m.name} for m in managers]
        return JsonResponse({"results": data})
    
class PickUpLocationSearchView(View):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("q", "")
        locations = RentalWarehouse.objects.all().order_by("location")
        if term:
            locations = locations.filter(location__icontains=term)
        else:
            locations = locations[:7]  
        data = [{"id": m.pk, "text": m.location} for m in locations]
        return JsonResponse({"results": data})
class RentalProductIDSearchView(View):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("q", "")
        products = RentalProduct.objects.all().order_by("equipment_id")
        if term:
            products = products.filter(
                Q(equipment_id__icontains=term) | Q(equipment_name__icontains=term)
            )
        else:
            products = products[:7]  # Return first 7 when no search term is provided

        data = [{
            "id": p.equipment_id,
            # Concatenate equipment_id and equipment_name, or change as needed
            "text": f"{p.equipment_id}"
        } for p in products]
        return JsonResponse({"results": data})

class RentalProductNameSearchView(View):
    def get(self, request, *args, **kwargs):
        term = request.GET.get("q", "")
        products = RentalProduct.objects.all().order_by("equipment_id")
        if term:
            products = products.filter(
                Q(equipment_id__icontains=term) | Q(equipment_name__icontains=term)
            )
        else:
            products = products[:7]  # Return first 7 when no search term is provided

        data = [{
            "id": p.equipment_id,
            # Concatenate equipment_id and equipment_name, or change as needed
            "text": f"{p.equipment_name}"
        } for p in products]
        return JsonResponse({"results": data})