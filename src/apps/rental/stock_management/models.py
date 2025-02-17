from django.db import models

from apps.rental.product.models import RentalProduct
from laurel.models import BaseModel


class StockAdjustment(BaseModel):
    REASON_CHOICES = [
        ("other", "Other"),
        ("inspection", "Inspection"),
        ("purchase", "Purchase"),
        ("wh_difference", "Warehouse Difference"),
    ]

    rental_product = models.ForeignKey(RentalProduct, on_delete=models.CASCADE, related_name="stock_adjustments")
    quantity = models.PositiveIntegerField()
    reason = models.CharField(max_length=50, choices=REASON_CHOICES, default="other")
    comment = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.rental_product.equipment_name}-{self.quantity})"
