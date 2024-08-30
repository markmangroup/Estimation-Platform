from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField


class User(AbstractUser):

    PROPOSAL = "Proposal"
    RENTAL = "Rental"

    APPLICATION_TYPE = ((PROPOSAL, "Proposal"), (RENTAL, "Rental"))
    username = models.CharField(_("Username"), max_length=255, blank=True, null=True)
    email = models.EmailField(_("Email"), unique=True)
    mobile = models.CharField(_("Mobile Number"), max_length=255, blank=True, null=True)
    application_type = MultiSelectField(
        choices=APPLICATION_TYPE,
        max_length=20,
        max_choices=2,
        null=True,
        blank=True,
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
