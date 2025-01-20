from django.core.management.base import BaseCommand

from apps.user.models import Permissions

# List of permissions to be created
PERMISSION = [
    ("create deliveries", "Create Deliveries"),
    ("pick up", "Pick Up"),
    ("check in", "Check In"),
    ("check out", "Check Out"),
    ("maintain master data", "Maintain Master Data"),
    ("create order", "Create Order"),
    ("complete order", "Complete Order"),
    ("stock adjustment", "Stock Adjustment"),
    ("inspection", "Inspection"),
    ("return pick up", "Return Pick Up"),
    ("create return order", "Create Return Order"),
]


class Command(BaseCommand):
    help = "Creates predefined permissions if they do not exist"

    def handle(self, *args, **kwargs):
        created_permissions = 0
        for code, name in PERMISSION:
            if not Permissions.objects.filter(name=name).exists():
                Permissions.objects.create(name=name)
                self.stdout.write(self.style.SUCCESS(f"Created permission: {name}"))
                created_permissions += 1
            else:
                self.stdout.write(self.style.WARNING(f"Permission already exists: {name}"))

        self.stdout.write(
            self.style.SUCCESS(f"Finished creating permissions. Total new permissions created: {created_permissions}")
        )
