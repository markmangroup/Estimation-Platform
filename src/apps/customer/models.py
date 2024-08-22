from django.db import models

from core.models import BaseModel


class Customer(BaseModel):
    internal_id = models.CharField(max_length=50, unique=True)
    customer_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    sales_rep = models.CharField(max_length=255)
    billing_address_1 = models.CharField(max_length=255)
    billing_address_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    zip = models.CharField(max_length=20)
    country = models.CharField(max_length=255)

    def __str__(self):
        return self.name
