from django.db import models

from core.models import BaseModel


# Create your models here.
class Task(BaseModel):
    internal_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name
