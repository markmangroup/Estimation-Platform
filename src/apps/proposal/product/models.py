from django.db import models

from laurel.models import BaseModel


# Create your models here.
class Product(BaseModel):
    internal_id = models.IntegerField(unique=True)
    family = models.CharField(max_length=255)
    parent = models.CharField(max_length=255)
    description = models.TextField()
    primary_units_type = models.CharField(max_length=50)
    primary_stock_unit = models.CharField(max_length=50)
    std_cost = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    tax_schedule = models.CharField(max_length=255, blank=True, null=True)
    preferred_vendor = models.CharField(max_length=255)
    formula = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.internal_id} - {self.description}"

    class Meta:
        verbose_name = "Proposal Product"


class AdditionalMaterials(BaseModel):
    """Additional Material Model."""

    material_id = models.IntegerField(unique=True)
    material_name = models.CharField(max_length=255)
    material_type = models.CharField(max_length=255, null=True, blank=True)
    product_item_number = models.CharField(max_length=255)
    material_factor = models.FloatField(null=True, blank=True)
    additional_material_factor = models.FloatField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.material_id} - {self.material_name}"

    class Meta:
        verbose_name = "Proposal Additional Material"
