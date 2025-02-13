from django.contrib import admin

from apps.rental.rent_process.models import (
    Delivery,
    Order,
    OrderItem,
    RecurringOrder,
    ReturnDelivery,
    ReturnOrder,
)

admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Delivery)
admin.site.register(ReturnDelivery)
admin.site.register(RecurringOrder)
admin.site.register(ReturnOrder)