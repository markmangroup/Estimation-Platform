from django.db import models
from django.utils.translation import gettext_lazy as _
from laurel.models import BaseModel
from apps.rental.customer.models import RentalCustomer
from apps.rental.account_manager.models import AccountManager
from apps.rental.product.models import RentalProduct

SHIPPING_CARRIER_CHOICES = [
    ("Internal", _("Internal")),
    ("Hired", _("Hired")),
]

class Order(BaseModel):
    STAGE_1 = "Pick Up"
    STAGE_2 = "Check Out"
    STAGE_3 = "Delivered"
    STAGE_4 = "Check In"
    STAGE_5 = "Create Return Delivery"
    STAGE_6 = "Create Delivery"

    ORDER_STATUS_CHOICES = [
        (STAGE_1, _("Pick Up")),
        (STAGE_2, _("Check Out")),
        (STAGE_3, _("Delivered")),
        (STAGE_4, _("Check In")),
        (STAGE_5, _("Create Return Delivery")),
        (STAGE_6, _("Create Delivery")),
    ]

    REPEAT_TYPE_CHOICES = [
        ("Weekly", _("Weekly")),
        ("Monthly", _("Monthly")),
        ("Yearly", _("Yearly")),
    ]

    RECURRING_TYPE_CHOICES = [
        ("Internal", _("Internal")),
        ("Hide", _("Hide")),
    ]

    order_id = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(
        RentalCustomer, on_delete=models.CASCADE, related_name="customers_order", blank=True, null=True
    )
    account_manager = models.ForeignKey(
        AccountManager, on_delete=models.CASCADE, related_name="account_manager_order", blank=True, null=True
    )
    link_netsuite = models.URLField(max_length=500, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    pick_up_location = models.CharField(max_length=255, blank=True, null=True)
    delivery_location = models.CharField(max_length=255, blank=True, null=True)
    water_source = models.CharField(max_length=255, blank=True, null=True)
    crop = models.CharField(max_length=255, blank=True, null=True)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rental_start_date = models.DateField(blank=True, null=True)
    rental_end_date = models.DateField(blank=True, null=True)
    recurring_order = models.BooleanField(default=False)
    repeat_type = models.CharField(max_length=255, choices=REPEAT_TYPE_CHOICES)
    repeat_value = models.PositiveIntegerField(blank=True, null=True)
    repeat_start_date = models.DateField(blank=True, null=True)
    repeat_end_date = models.DateField(blank=True, null=True)
    recurring_type = models.CharField(max_length=255, choices=RECURRING_TYPE_CHOICES, default="Daily")
    order_status = models.CharField(_("Order Status"), max_length=50, choices=ORDER_STATUS_CHOICES, default=STAGE_1)

    def __str__(self):
        return f"Order {self.order_id}"

    def calculate_total_repeat_orders(self):
        total_orders = 0
        if self.repeat_type == "Weekly":
            total_orders = (self.repeat_end_date - self.repeat_start_date).days // 7
        elif self.repeat_type == "Monthly":
            total_orders = (self.repeat_end_date.year - self.repeat_start_date.year) * 12 + self.repeat_end_date.month - self.repeat_start_date.month
        elif self.repeat_type == "Yearly":
            total_orders = self.repeat_end_date.year - self.repeat_start_date.year

        return total_orders


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="orders", blank=True, null=True
    )
    product = models.ForeignKey(
        RentalProduct, on_delete=models.CASCADE, related_name="order_products", blank=True, null=True
    )
    quantity = models.PositiveIntegerField(blank=True, null=True)
    per_unit_price = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.order.order_id} - {self.product} - {self.quantity}"


class Delivery(BaseModel):
    STAGE_1 = "Pick Up"
    STAGE_2 = "Check Out"
    STAGE_3 = "Delivered"
    STAGE_4 = "Check In"
    STAGE_5 = "Create Return Delivery"
    STAGE_6 = "Create Delivery"

    DELIVERY_STATUS_CHOICES = [
        (STAGE_1, _("Pick Up")),
        (STAGE_2, _("Check Out")),
        (STAGE_3, _("Delivered")),
        (STAGE_4, _("Check In")),
        (STAGE_5, _("Create Return Delivery")),
        (STAGE_6, _("Create Delivery")),
    ]

    delivery_id = models.CharField(max_length=255, primary_key=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="delivery_order", blank=True, null=True
    )
    product = models.ForeignKey(
        RentalProduct, on_delete=models.CASCADE, related_name="delivery_products", blank=True, null=True
    )
    delivery_qty = models.IntegerField()
    contract_start_date = models.DateField()
    contract_end_date = models.DateField()
    delivery_date = models.DateField()
    pickup_date = models.DateField()
    check_out_date = models.DateField()
    check_in_date = models.DateField()
    removal_date = models.DateField()
    inspection_date = models.DateField()
    pickup_site = models.CharField(max_length=255)
    delivery_site = models.CharField(max_length=255)
    po_number = models.CharField(max_length=50)
    shipping_carrier = models.CharField(max_length=20, choices=SHIPPING_CARRIER_CHOICES)
    delivery_status = models.CharField(_("Delivery Status"), max_length=50, choices=DELIVERY_STATUS_CHOICES, default=STAGE_1)

    def __str__(self):
        return self.delivery_id


class ReturnDelivery(BaseModel):
    delivery = models.ForeignKey(
        Delivery, on_delete=models.CASCADE, related_name="return_delivery", blank=True, null=True
    )
    return_order = models.CharField(max_length=50)
    return_qty = models.IntegerField()
    return_po_number = models.CharField(max_length=50)
    returned_pickup_date = models.DateField()
    returned_delivery_date = models.DateField()
    returned_pickup_site = models.CharField(max_length=255)
    returned_delivery_site = models.CharField(max_length=255)
    shipping_carrier = models.CharField(max_length=20, choices=SHIPPING_CARRIER_CHOICES)
    deliver_to_customer = models.BooleanField(default=False)

    def __str__(self):
        return self.return_order


class RecurringOrder(BaseModel):
    recurring_order_id = models.CharField(max_length=255, primary_key=True)
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="recurring_orders", blank=True, null=True
    )

    def __str__(self):
        return self.recurring_order_id


class ReturnOrder(BaseModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="return_orders", blank=True, null=True
    )
    delivery = models.ForeignKey(
        Delivery, on_delete=models.CASCADE, related_name="delivery_return_orders", blank=True, null=True
    )

    def __str__(self):
        return f"Return Order {self.order.order_id} - {self.delivery.delivery_id}"
