from django.contrib import admin

from apps.rental.rent_process.models import (
    Delivery,
    Order,
    OrderItem,
    RecurringOrder,
    ReturnDelivery,
    ReturnOrder,
    OrderFormPermissionModel,
    Document,
    ReturnDeliveryItem,
)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1

class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "customer", "order_status", "rental_start_date", "rental_end_date","created_at")
    search_fields = ("order_id", "customer__name")
    list_filter = ("order_status", "repeat_type")
    inlines = [OrderItemInline]

admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
admin.site.register(Delivery)
admin.site.register(ReturnDelivery)
admin.site.register(RecurringOrder)
admin.site.register(ReturnOrder)
admin.site.register(OrderFormPermissionModel)
admin.site.register(Document)
admin.site.register(ReturnDeliveryItem)
