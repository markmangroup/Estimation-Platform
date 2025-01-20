from django.db import models

from laurel.models import BaseModel


class RentalProduct(BaseModel):
    equipment_id = models.AutoField(primary_key=True)
    equipment_material_group = models.CharField(max_length=255)
    equipment_name = models.CharField(max_length=255)
    subtype = models.CharField(max_length=255)

    def __str__(self):
        return self.equipment_name
