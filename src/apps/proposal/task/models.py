from django.db import models

from laurel.models import BaseModel


# Create your models here.
class Task(BaseModel):
    internal_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Proposal Task"
