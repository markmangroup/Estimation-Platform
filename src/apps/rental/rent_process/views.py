import json
from django.shortcuts import get_object_or_404, redirect
from apps.mixin import  CreateViewMixin, WarehouseDetailViewMixin, WarehouseViewMixin
from django.http import JsonResponse
from django.urls import reverse
import datetime

from django.forms import inlineformset_factory
from apps.mixin import WarehouseViewMixin,UpdateViewMixin
from django.http import HttpResponse, JsonResponse
from typing import Any, Dict
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.template.loader import get_template
from apps.mixin import FormViewMixin, WarehouseViewMixin,WarehouseDetailViewMixin,AdminMixin,View
from apps.rental.customer.models import RentalCustomer
from apps.rental.product.models import RentalProduct
from apps.rental.rent_process import forms,tasks
from django.shortcuts import get_object_or_404, redirect, render
from apps.mixin import CustomDataTableMixin
from apps.rental.rent_process.models import Order, OrderItem,Delivery
from django.template.loader import render_to_string
from django.db.models import Sum
from apps.rental.rent_process.models import Order,RecurringOrder,ReturnOrder,Delivery,OrderItem,OrderFormPermissionModel
from django.contrib import messages
from django.views.generic.edit import CreateView
from .forms import OrderForm, OrderFormPermissionForm, OrderItemForm,OrderItemFormSet


class OrderListView(WarehouseViewMixin):
    """View class for rendering the list of order."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['form'] = OrderForm
            context["order_item_formset"] = OrderItemFormSet(self.request.POST)
        else:
            context['form'] = OrderForm
            formset = OrderItemFormSet()    
            for form in formset.forms:
                form.fields["product"].queryset = RentalProduct.objects.all()  
            context["order_item_formset"] = formset
        context['permission'] = OrderFormPermissionModel.objects.all()
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
                "skipped_records":response['skipped_records'],
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
                Q(order_id__icontains=self.search) | 
                Q(customer__name__icontains=self.search) |
                Q(rent_amount__icontains=self.search) |
                Q(account_manager__name__icontains=self.search) |
                Q(repeat_start_date__icontains=self.search) | 
                Q(repeat_end_date__icontains=self.search) |
                Q(updated_at__icontains=self.search) 
            )
        return qs

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            delivery_ids = list(Delivery.objects.filter(order=o).values_list('delivery_id', flat=True))
            if o.repeat_type in ["Weekly","Monthly","Yearly","Recurring"]:
                recurring = "Recurring"
            else:
                recurring = "One Time"
            data.append(
                {
                    "order_id": self._get_order_id(o),
                    "delivery_id":self._get_delivery_id(delivery_ids) if delivery_ids else " - ",
                    "status":self._get_estimation_stage(delivery_ids) if delivery_ids else " - ",
                    "customer": o.customer.name,
                    "order_amount":o.rent_amount,
                    "account_manager": o.account_manager.name,
                    "start_date": o.rental_start_date.strftime("%d/%m/%Y") if o.rental_start_date else " - ",
                    "end_date": o.rental_end_date.strftime("%d/%m/%Y") if o.rental_end_date else " - ",
                    "recurring_type": recurring,
                    "last_updated_date":  o.updated_at.strftime("%d/%m/%Y"),
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
            "rental:rent_process:order-overview",
            kwargs={"order_id": obj.order_id},
        )
        return f'<a href="{detail_url}">{obj.order_id}</a>'
    
    def _get_delivery_id(self, delivery_ids):
        """
        Create links to the Opportunity detail pages for all delivery IDs in a table format.
        """
        table = '<table class="table bordered">'
        table += '<tbody>'
        for delivery_id in delivery_ids:
            edit_url = reverse(
                "rental:rent_process:delivery-detail",
                kwargs={"delivery_id": delivery_id},
            )
            table += f'<tr><td><a href="{edit_url}">{delivery_id}</a></td></tr>'
        table += '</tbody></table>'
        return table

    def _get_actions(self, obj):
        """
        Generate action buttons for the Opportunity with a link to the detail page.
        """
        t = get_template("rental/rent_process/rent_process_action.html")

        time_line_url = reverse(
            "rental:rent_process:order-overview",
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

        return t.render(
            {
                "delete_url": delete_url,
                "process_url": process_url,
                "time_line_url": time_line_url,
                "hx_target": hx_target,
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
            rent = self.calculation_of_rent_amount(quantity, price, start_date, end_date)
            rent_details.append({
                "item_id": item.id,
                "rent": rent
            })

        context["order"] = order
        context["deliverys"] = delivery
        context["recurring_order"] = recurring_order
        context["order_items"] = order_items
        context["rent_details"] = rent_details

        print(f"└─ ➡ ┌─ context: {context}")
        return context
    
    def calculation_of_rent_amount(self,quantity,price,start_date,end_date):
        rent_details = {}
        rent_amount = quantity * price
        rent_details['rent_amount'] = rent_amount
        while start_date <= end_date:
            month_name = start_date.strftime("%B")
            rent_details[month_name] = rent_amount
            if start_date.month == 12:
                start_date = datetime.date(start_date.year + 1, 1, 1)
            else:
                start_date = datetime.date(start_date.year, start_date.month + 1, 1)
        return rent_details



class DeliveryDetailview(FormViewMixin):
    pass

class OrderProcessview(WarehouseDetailViewMixin):
    model = Order
    render_template_name = "rental/orders/rental_order.html"

    def get_object(self, queryset=None):
        order_id = self.kwargs.get("order_id")
        return get_object_or_404(Order, order_id=order_id)


def create_delivery_modal(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    
    order_items = OrderItem.objects.filter(order=order)
    pending_order_items = []

    for item in order_items:
        delivered_qty = Delivery.objects.filter(order=order, product=item.product).aggregate(Sum('delivery_qty'))['delivery_qty__sum'] or 0
        remaining_qty = item.quantity - delivered_qty

        if remaining_qty > 0:
            pending_order_items.append({
                "order_item": item,
                "remaining_qty": remaining_qty
            })

    context = {
        "order": order,
        "order_items": pending_order_items
    }    
    html = render_to_string("rental/rent_process/delivery_table.html", context, request=request)
    return JsonResponse({"html": html})

class DeliveryCreateView(CreateViewMixin):
    form_class = forms.DeliveryForm

    def form_valid(self, form):
        order_number = self.request.POST.get('order')
        
        try:
            order = Order.objects.get(order_id=order_number)
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Order not found'}, status=404)

        pickup_date = form.cleaned_data['pickup_date']
        delivery_date = form.cleaned_data['delivery_date']
        shipping_carrier = form.cleaned_data['shipping_carrier']
        pickup_site = form.cleaned_data['pickup_site']
        delivery_site = form.cleaned_data['delivery_site']
        products_json = self.request.POST.get('products')
        po_number = form.cleaned_data['po_number']
        
        try:
            products = json.loads(products_json)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid product data format'}, status=400)
        
        for product in products:
            product_id = product.get('productId')
            quantity = product.get('quantity')
            try:
                product_id = int(product_id)
                quantity = int(quantity)
            except ValueError:  
                return JsonResponse({'success': False, 'error': 'Invalid product ID or quantity'}, status=400)

            try:
                order_item = OrderItem.objects.get(id=product_id, order=order)
            except OrderItem.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'OrderItem with ID {product_id} not found for Order {order_number}'}, status=404)

            delivery_id = tasks.generate_delivery_id(order)
            delivery = Delivery.objects.create(
                delivery_id=delivery_id,
                po_number= po_number if po_number else None,
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
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
class RecurringOrderListAjaxView(CustomDataTableMixin):
    """AJAX view for listing Warehouse in a data table format."""

    def _get_recurring_order_id(self, obj):
        """
        Create a link to the Opportunity detail page with the document number.
        """
        edit_url = reverse(
            "rental:rent_process:reccuring-order-overview",
            kwargs={"recurring_order_id": obj.recurring_order_id},
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
        delete_url = reverse(
            "rental:rent_process:reccuring-order-delete"
        )
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
                Q(recurring_order_id__icontains=self.search) |
                Q(order__order_id__icontains=self.search) |
                Q(order__customer__name__icontains=self.search) |
                Q(order__rent_amount__icontains=self.search) |
                Q(order__account_manager__name__icontains=self.search) |
                Q(order__repeat_start_date__icontains=self.search) |
                Q(order__repeat_end_date__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        """Create row data for datatables."""
        data = []
        for o in qs:
            number_of_orders = o.order.calculate_total_repeat_orders()
            data.append(
                {
                    "order_id": self._get_orignal_order_id(o.order.order_id),
                    "recurring_order_id": self._get_recurring_order_id(o),
                    "customer": o.order.customer.name,
                    "order_amount": o.order.rent_amount,
                    "account_manager": o.order.account_manager.name,
                    "recurring_type": o.order.repeat_type,
                    "repeat_start_date": o.order.repeat_start_date.strftime("%d/%m/%Y") if o.order.repeat_start_date else None,
                    "repeat_end_date": o.order.repeat_end_date.strftime("%d/%m/%Y") if o.order.repeat_end_date else None,
                    "number_of_orders": number_of_orders,
                    "actions": self._get_actions(o),
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        """Get a dictionary of data."""
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)

# class ReturnOrderListAjaxView(CustomDataTableMixin):
#     """AJAX view for listing Warehouse in a data table format."""

#     def _get_actions(self, obj):
#         """
#         Generate action buttons for the Opportunity with a link to the detail page.
#         """
#         t = get_template("rental/rent_process/rent_process_action.html")

#         time_line_url = reverse(
#             "rental:rent_process:order-overview",
#             kwargs={"order_id": obj.order.order_id}
#         )
#         edit_url = reverse(
#             "rental:rent_process:order-overview",
#             kwargs={"order_id": obj.order.order_id}
#         )
#         process_url = reverse(
#             "rental:rent_process:order-process",
#             kwargs={"order_id": obj.order.order_id}
#         )
#         return t.render(
#             {
#                 "time_line_url": time_line_url,
#                 "return_edit_url": edit_url,
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
#             "rental:rent_process:order-overview",
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
    context_object_name = 'recurring_order'

    def get_initial(self):
        initial_data = super().get_initial()
        order = self.object.order
        
        initial_data['customer'] = order.customer.name
        initial_data['pick_up_location'] = order.pick_up_location
        initial_data['rental_start_date'] = order.rental_start_date
        order_items = order.orders.all()

        initial_data['no_of_product'] = sum(item.quantity for item in order_items)
        initial_data['rent_amount'] = order.rent_amount
        initial_data['repeat_type'] = order.repeat_type
        
        if order.repeat_start_date and order.repeat_end_date:
            repeat_date_range = f"{order.repeat_start_date.strftime('%Y-%m-%d')} - {order.repeat_end_date.strftime('%Y-%m-%d')}"
            initial_data['repeat_date_range'] = repeat_date_range
        return initial_data

    def form_valid(self, form):
        self.object = form.save(commit=True)
        order = self.object.order
        if order:
            order.repeat_type = form.cleaned_data.get('order__repeat_type', order.repeat_type)
            repeat_date_range = form.cleaned_data.get('repeat_date_range', '')
            if repeat_date_range:
                try:
                    start_date_str, end_date_str = repeat_date_range.split(' - ')
                    order.repeat_start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    order.repeat_end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    messages.error(self.request, "Invalid date range format. Please use the format 'YYYY-MM-DD - YYYY-MM-DD'.")
                    return HttpResponse("error")
            order.save()
        messages.success(self.request, "Recurring Order updated successfully.")
        return HttpResponse("success")

    def form_invalid(self, form):   
        return render(self.request, 
                      self.template_name, 
                      {'form': form,'recurring_order': self.get_object()}, 
                      status=201
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


class OrderCreate(CreateView):
    model = Order
    form_class = OrderForm
    template_name = "rental/rent_process/create_order.html"
    success_url = reverse_lazy("rental:rent_process_order_list") 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        OrderItemFormSet = inlineformset_factory(Order, OrderItem, form=OrderItemForm, extra=1)
        
        if self.request.POST:
            context["order_item_formset"] = OrderItemFormSet(self.request.POST)
        else:
            formset = OrderItemFormSet()
            for form in formset.forms:
                form.fields["product"].queryset = RentalProduct.objects.all() 
            context["order_item_formset"] = formset

        context["form"].fields["customer"].queryset = RentalCustomer.objects.all() 
        context['permission'] = OrderFormPermissionModel.objects.first()
        return context

    def form_valid(self, form):
        order = form.save() 

        OrderItemFormSet = inlineformset_factory(Order, OrderItem, form=OrderItemForm, extra=1)
        order_item_formset = OrderItemFormSet(self.request.POST, instance=order) 

        if order_item_formset.is_valid():
            order_item_formset.save()
            messages.success(self.request, "Order Created Successfuly")
            return HttpResponse("success")
        else:
            print("OrderItem FormSet Errors:", order_item_formset.errors)
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors in the form.")
        return self.render_to_response(self.get_context_data(form=form))
    

class OrderPermissionCreateUpdateView(View):
    template_name = 'rental/rent_process/order_form_permission.html'
    success_url = reverse_lazy("rental:rent_process:order-list")

    def get(self, request, *args, **kwargs):
        user=self.request.user
        obj, created = OrderFormPermissionModel.objects.get_or_create(defaults={})
        form = OrderFormPermissionForm(instance=obj)
        return render(request, self.template_name, {"form": form,'user':user})

    def post(self, request, *args, **kwargs):
        user=self.request.user
        obj, created = OrderFormPermissionModel.objects.get_or_create(defaults={})
        form = OrderFormPermissionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(self.request, "Order permissions updated successfully.")
            return HttpResponse("success")
        return render(request, self.template_name, {"form": form,'user':user})
