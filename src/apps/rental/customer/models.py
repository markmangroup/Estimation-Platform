from django.db import models
from django.utils.translation import gettext_lazy as _

from laurel.models import BaseModel


class RentalCustomer(BaseModel):
    """Rental Customer Model."""

    internal_id = models.IntegerField(_("Internal ID"), unique=True)
    customer_id = models.CharField(_("ID"), max_length=255, unique=True)
    customer_email = models.EmailField(_("Rental Cutomer Email"))
    name = models.CharField(_("Customer Name"), max_length=255)
    sales_rep = models.CharField(_("Sales Rep."), max_length=255, blank=True, null=True)
    billing_address_1 = models.TextField(_("Billing Address 1"), blank=True, null=True)
    billing_address_2 = models.TextField(_("Billing Address 2"), blank=True, null=True)
    city = models.CharField(_("City"), max_length=255, blank=True, null=True)
    state = models.CharField(_("State (Billing state/province)"), max_length=255, blank=True, null=True)
    zip = models.CharField(_("Zip"), max_length=255, blank=True, null=True)
    country = models.CharField(_("Country"), max_length=255, blank=True, null=True)
    lat = models.CharField(_("Latitude"), max_length=255, blank=True, null=True)
    lng = models.CharField(_("Longitude"), max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.internal_id} - {self.customer_id} - {self.name} "

    class Meta:
        verbose_name = "Rental Customer"
