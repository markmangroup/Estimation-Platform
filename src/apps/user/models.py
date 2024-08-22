from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    username = models.CharField(_("Username"), max_length=255, blank=True, null=True)
    email = models.EmailField(_("Email"), unique=True)
    mobile = models.CharField(_("Mobile Number"), max_length=255, blank=True, null=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
