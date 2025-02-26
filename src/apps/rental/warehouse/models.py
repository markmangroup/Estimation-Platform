from django.db import models
from django.utils.translation import gettext_lazy as _

from laurel.models import BaseModel


class RentalWarehouse(BaseModel):
    """Rental Warehouse Model."""

    location = models.CharField(_("Location"), max_length=255) # Change Name location to Warehouse Name 
    address = models.TextField(_("Address"))
    lat = models.CharField(_("Latitude"), max_length=255, blank=True, null=True)
    lng = models.CharField(_("Longitude"), max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.location}"

    class Meta:
        verbose_name = "Rental Warehouse"
