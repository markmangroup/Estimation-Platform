from django.db import models
from django.utils.translation import gettext_lazy as _

from laurel.models import BaseModel


class LabourCost(BaseModel):
    labour_task = models.CharField(_("Labour Task"), max_length=255, unique=True)
    local_labour_rates = models.FloatField(_("Local Labour Rates"), blank=True, null=True)
    out_of_town_labour_rates = models.FloatField(_("Out Of Labour Rates"), blank=True, null=True)
    description = models.CharField(_("Description"), max_length=255, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    def __str__(self):
        return self.labour_task

    class Meta:
        verbose_name = "Proposal Labor Cost"
