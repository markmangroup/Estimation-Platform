from django.apps import AppConfig


class CustomerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rental.customer"
    label = "rental_customer"  # Change label for rental customer model
