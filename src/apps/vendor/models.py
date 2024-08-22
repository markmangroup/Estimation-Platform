from django.db import models

from core.models import BaseModel

# Create your models here.


class Vendor(BaseModel):
    internal_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
