from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from laurel.models import BaseModel


class Permissions(BaseModel):
    """
    Permissions model
    """

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class User(AbstractUser):

    username = models.CharField(_("Username"), max_length=255, blank=True, null=True)
    email = models.EmailField(_("Email"))
    mobile = models.CharField(_("Mobile Number"), max_length=255, blank=True, null=True)
    permissions = models.ManyToManyField(Permissions, related_name="user_permissions", blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
