import os
from datetime import datetime, timedelta
from django.db import models
from django.utils.translation import gettext_lazy as _
from laurel.models import BaseModel
from apps.rental.customer.models import RentalCustomer
from apps.rental.account_manager.models import AccountManager
from apps.rental.product.models import RentalProduct
from django.utils.timezone import now
from django_countries.fields import CountryField
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas

from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv
from django.db import transaction

from apps.rental.account_manager.models import AccountManager
from apps.rental.customer.models import RentalCustomer
from apps.rental.product.models import RentalProduct
from laurel.models import BaseModel

SHIPPING_CARRIER_CHOICES = [
    ("Internal", _("Internal")),
    ("Hired", _("Hired")),
]


class Order(BaseModel):
    STAGE_1 = "Create Delivery"
    STAGE_2 = "Pick Up Ticket"
    STAGE_3 = "Check Out"
    STAGE_4 = "Delivered To Customer"
    STAGE_5 = "Create Return Delivery"
    STAGE_6 = "Return Pick Up Ticket"
    STAGE_7 = "Check In"
    STAGE_8 = "Inspection Completed"

    ORDER_STATUS_CHOICES = [
        (STAGE_1, _("Create Delivery")),
        (STAGE_2, _("Pick Up Ticket")),
        (STAGE_3, _("Check Out")),
        (STAGE_4, _("Delivered To Customer")),
        (STAGE_5, _("Create Return Delivery")),
        (STAGE_6, _("Return Pick Up Ticket")),
        (STAGE_7, _("Check In")),
        (STAGE_8, _("Inspection Completed")),
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
    link_netsuite = models.CharField(max_length=255, blank=True, null=True)
    region = CountryField(null=True, blank=True, max_length=255)
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
        total_orders = 1
        if self.repeat_type == "Weekly":
            total_days = (self.repeat_end_date - self.repeat_start_date).days
            if total_days < 7:
                total_orders = 1
            else:
                total_orders = total_days // 7 + 1
        elif self.repeat_type == "Monthly":
            if (
                self.repeat_end_date.year == self.repeat_start_date.year
                and self.repeat_end_date.month == self.repeat_start_date.month
            ):
                total_orders = 1
            else:
                total_orders = (
                    (self.repeat_end_date.year - self.repeat_start_date.year) * 12
                    + self.repeat_end_date.month
                    - self.repeat_start_date.month
                    + 1
                )

        elif self.repeat_type == "Yearly":
            total_orders = self.repeat_end_date.year - self.repeat_start_date.year + 1

        return total_orders

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = self._generate_order_id()
        super().save(*args, **kwargs)

    def _generate_order_id(self):
        if isinstance(self.rental_start_date, str):
            self.rental_start_date = datetime.strptime(self.rental_start_date, "%Y-%m-%d")
        year_month = self.rental_start_date.strftime("%Y%m") if self.rental_start_date else now().strftime("%Y%m")
        prefix = "O" if self.recurring_order else "O"

        last_order = Order.objects.filter(order_id__startswith=prefix + year_month).order_by("-order_id").first()

        if last_order:
            last_seq = int(last_order.order_id[-5:])
            new_seq = f"{last_seq + 1:05d}"
        else:
            new_seq = "00001"

        return f"{prefix}{year_month}{new_seq}"

    def get_current_stage_constant(self):
        stage_mapping = {
            self.STAGE_1: "STAGE_1",
            self.STAGE_2: "STAGE_2",
            self.STAGE_3: "STAGE_3",
            self.STAGE_4: "STAGE_4",
            self.STAGE_5: "STAGE_5",
            self.STAGE_6: "STAGE_6",
            self.STAGE_7: "STAGE_7",
            self.STAGE_8: "STAGE_8",
        }
        return stage_mapping.get(self.order_status, "Unknown Stage")


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="orders", blank=True, null=True)
    product = models.ForeignKey(
        RentalProduct, on_delete=models.CASCADE, related_name="order_products", blank=True, null=True
    )
    quantity = models.PositiveIntegerField(blank=True, null=True)
    per_unit_price = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return f"Order {self.order.order_id} - {self.product} - {self.quantity}"


class Delivery(BaseModel):
    STAGE_1 = "Create Delivery"
    STAGE_2 = "Pick Up Ticket"
    STAGE_3 = "Check Out"
    STAGE_4 = "Delivered To Customer"
    STAGE_5 = "Create Return Delivery"
    STAGE_6 = "Return Pick Up Ticket"
    STAGE_7 = "Check In"
    STAGE_8 = "Inspection Completed"

    DELIVERY_STATUS_CHOICES = [
        (STAGE_1, _("Create Delivery")),
        (STAGE_2, _("Pick Up Ticket")),
        (STAGE_3, _("Check Out")),
        (STAGE_4, _("Delivered To Customer")),
        (STAGE_5, _("Create Return Delivery")),
        (STAGE_6, _("Return Pick Up Ticket")),
        (STAGE_7, _("Check In")),
        (STAGE_8, _("Inspection Completed")),
    ]

    delivery_id = models.CharField(max_length=255, primary_key=True)
    unique_delivery_id = models.CharField(max_length=255, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="delivery_order", blank=True, null=True)
    product = models.ForeignKey(
        RentalProduct, on_delete=models.CASCADE, related_name="delivery_products", blank=True, null=True
    )
    delivery_qty = models.IntegerField()
    contract_start_date = models.DateField(blank=True, null=True)
    contract_end_date = models.DateField(blank=True, null=True)
    delivery_date = models.DateField(blank=True, null=True)
    pickup_date = models.DateField(blank=True, null=True)
    check_out_date = models.DateField(blank=True, null=True)
    check_in_date = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    removal_date = models.DateField(blank=True, null=True)
    inspection_date = models.DateField(blank=True, null=True)
    pickup_site = models.CharField(max_length=255)
    delivery_site = models.CharField(max_length=255)
    po_number = models.CharField(max_length=50, blank=True, null=True)
    shipping_carrier = models.CharField(max_length=20, choices=SHIPPING_CARRIER_CHOICES)
    direct_delivery = models.BooleanField(default=False)
    delivery_status = models.CharField(
        _("Delivery Status"), max_length=50, choices=DELIVERY_STATUS_CHOICES, default=STAGE_1
    )

    def __str__(self):
        return f"Delivery {self.unique_delivery_id} - object id {self.delivery_id}"

    def generate_delivery_id(self):
        last_delivery = Delivery.objects.all().order_by("delivery_id").last()

        if last_delivery and last_delivery.delivery_id:
            try:
                last_number = int(last_delivery.delivery_id[2:])
                new_number = last_number + 1
                new_delivery_id = f"DE{new_number}"

                while Delivery.objects.filter(delivery_id=new_delivery_id).exists():
                    new_number += 1
                    new_delivery_id = f"DE{new_number}"

                return new_delivery_id
            except ValueError:
                return "DE1"
        else:
            return "DE1"

    def save(self, *args, **kwargs):
        if not self.delivery_id:
            self.delivery_id = self.generate_delivery_id()
        super().save(*args, **kwargs)

class ReturnOrder(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="return_orders", blank=True, null=True)
    delivery = models.ForeignKey(
        Delivery, on_delete=models.CASCADE, related_name="delivery_return_orders", blank=True, null=True
    )
    return_order_unique_id = models.CharField(max_length=30, unique=True, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.return_order_unique_id and self.order:
            self.return_order_unique_id = self.order.order_id.replace("O", "OR", 1)
        
        super().save(*args, **kwargs)
    def __str__(self):
        return f"Return Order {self.order.order_id} - {self.return_order_unique_id}"

class ReturnDelivery(BaseModel):
    return_order = models.ForeignKey(ReturnOrder, on_delete=models.CASCADE, related_name="return_delivery_order", blank=True, null=True)
    return_unique_id = models.CharField(max_length=30, unique=True, blank=True, null=True)
    return_po_number = models.CharField(max_length=50)
    returned_pickup_date = models.DateField()
    contract_end_date = models.DateField(blank=True, null=True)
    check_in_date = models.DateTimeField(blank=True, null=True)
    removal_date = models.DateField(blank=True, null=True)
    inspection_date = models.DateField(blank=True, null=True)
    returned_delivery_date = models.DateField()
    returned_pickup_site = models.CharField(max_length=255)
    returned_delivery_site = models.CharField(max_length=255)
    shipping_carrier = models.CharField(max_length=20, choices=SHIPPING_CARRIER_CHOICES)
    deliver_to_customer = models.BooleanField(default=False)
    direct_delivery = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.return_unique_id:
            today = datetime.today()
            year = today.strftime("%Y")
            month = today.strftime("%m")
            day = today.strftime("%d")

            formatted_date = f"{year}{month}000{day}"
            last_return = (
                ReturnDelivery.objects.filter(return_unique_id__startswith=f"O{formatted_date}").order_by("-id").first()
            )
            return_count = 1

            if last_return:
                last_id = last_return.return_unique_id.split("-R")[-1]
                return_count = int(last_id) + 1

            self.return_unique_id = f"O{formatted_date}-R{return_count}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.return_unique_id


class ReturnDeliveryItem(models.Model):
    STAGE_1 = "Create Delivery"
    STAGE_2 = "Pick Up Ticket"
    STAGE_3 = "Check Out"
    STAGE_4 = "Delivered To Customer"
    STAGE_5 = "Create Return Delivery"
    STAGE_6 = "Return Pick Up Ticket"
    STAGE_7 = "Check In"
    STAGE_8 = "Inspection Completed"

    RETURN_STATUS_CHOICES = [
        (STAGE_1, _("Create Delivery")),
        (STAGE_2, _("Pick Up Ticket")),
        (STAGE_3, _("Check Out")),
        (STAGE_4, _("Delivered To Customer")),
        (STAGE_5, _("Create Return Delivery")),
        (STAGE_6, _("Return Pick Up Ticket")),
        (STAGE_7, _("Check In")),
        (STAGE_8, _("Inspection Completed")),
    ]
    return_delivery = models.ForeignKey(ReturnDelivery, on_delete=models.CASCADE, related_name="return_items")
    product = models.ForeignKey(RentalProduct, on_delete=models.CASCADE, related_name="return_delivery_products")
    return_qty = models.IntegerField()
    return_status = models.CharField(max_length=50, choices=RETURN_STATUS_CHOICES, default=STAGE_5)

    def __str__(self):
        return f"{self.product} - {self.return_qty}"


class RecurringOrder(BaseModel):
    recurring_order_id = models.CharField(max_length=255, primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="recurring_orders", blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.recurring_order_id

    def save(self, *args, **kwargs):
        if not self.recurring_order_id:
            self.recurring_order_id = self._generate_recurring_order_id()
        super().save(*args, **kwargs)

    def _generate_recurring_order_id(self):
        if isinstance(self.order.rental_start_date, str):
            self.order.rental_start_date = datetime.datetime.strptime(self.order.rental_start_date, "%Y-%m-%d").date()

        year_month = (
            self.order.rental_start_date.strftime("%Y%m") if self.order.rental_start_date else now().strftime("%Y%m")
        )

        prefix = "OR"

        last_order = RecurringOrder.objects.filter(recurring_order_id__startswith=prefix + year_month).order_by("-recurring_order_id").first()

        if last_order:
            last_seq = int(last_order.recurring_order_id[-5:])
            new_seq = f"{last_seq + 1:05d}"
        else:
            new_seq = "00001"

        return f"{prefix}{year_month}{new_seq}"






class OrderFormPermissionModel(models.Model):
    customer = models.BooleanField(default=True)
    account_manager = models.BooleanField(default=True)
    link_netsuite = models.BooleanField(default=False)
    region = models.BooleanField(default=False)
    pick_up_location = models.BooleanField(default=False)
    delivery_location = models.BooleanField(default=False)
    water_source = models.BooleanField(default=False)
    crop = models.BooleanField(default=False)
    rent_amount = models.BooleanField(default=False)
    rental_period = models.BooleanField(default=False)
    recurring_order = models.BooleanField(default=False)
    repeat_type = models.BooleanField(default=True)
    repeat_value = models.BooleanField(default=False)
    repeat_start_date = models.BooleanField(default=False)
    repeat_end_date = models.BooleanField(default=False)
    rental_period = models.BooleanField(default=False)
    customer_email = models.BooleanField(default=True)
    rent_per_month = models.BooleanField(default=False)
    equipment_id = models.BooleanField(default=False)
    equipment_name = models.BooleanField(default=False)
    quantity = models.BooleanField(default=False)
    per_unit_price = models.BooleanField(default=False)

    def __str__(self):
        return f"OrderData {self.id}"


class Document(BaseModel):

    STAGE_1 = "Create Delivery"
    STAGE_2 = "Pick Up Ticket"
    STAGE_3 = "Check Out"
    STAGE_4 = "Delivered To Customer"
    STAGE_5 = "Create Return Delivery"
    STAGE_6 = "Return Pick Up Ticket"
    STAGE_7 = "Check In"
    STAGE_8 = "Inspection Completed"

    ESTIMATION_STAGE_CHOICES = [
        (STAGE_1, _("Create Delivery")),
        (STAGE_2, _("Pick Up Ticket")),
        (STAGE_3, _("Check Out")),
        (STAGE_4, _("Delivered To Customer")),
        (STAGE_5, _("Create Return Delivery")),
        (STAGE_6, _("Return Pick Up Ticket")),
        (STAGE_7, _("Check In")),
        (STAGE_8, _("Inspection Completed")),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="documents", blank=True, null=True)
    document = models.FileField(_("Document"), upload_to="documents/")
    stage = models.CharField(_("Stage"), max_length=50, choices=ESTIMATION_STAGE_CHOICES, default=STAGE_1)
    comment = models.TextField(_("Comment"), blank=True, null=True)

    @property
    def file_path(self):
        connection_string = os.getenv("AZURE_CONNECTION_STRING")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = os.getenv("AZURE_CONTAINER")
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            account_key=os.getenv("AZURE_ACCOUNT_KEY"),
            container_name=container_name,
            blob_name=self.document.name,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )
        file_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{self.document.name}?{sas_token}"
        return file_url

    def __str__(self):
        return f"{self.stage} - {self.document.name}"

    class Meta:
        verbose_name = "Rental Document"
