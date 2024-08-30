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
    preferred_vendor = models.CharField(max_length=255)

    def __str__(self):
        return self.description

    class Meta:
        verbose_name = "Proposal Product"
