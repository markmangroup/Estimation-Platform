from django.db import models
from django.utils.translation import gettext_lazy as _

from laurel.models import BaseModel


class AccountManager(BaseModel):
    """Account Manager Model."""

    name = models.CharField(_("Account Manager Name"), max_length=255)
    email = models.EmailField(_("Account Manager Email"))
    manager_id = models.CharField(_("Manager ID"), max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.name} - {self.email}"

    class Meta:
        verbose_name = "Rental Account Manager"
