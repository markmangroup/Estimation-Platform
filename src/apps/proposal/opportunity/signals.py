import random

from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.proposal.opportunity.models import (
    Document,
    Invoice,
    Opportunity,
    SelectTaskCode,
    TaskMapping,
)


@receiver(post_save, sender=Opportunity)
def generate_invoice_details(sender, instance, created, **kwargs):
    """
    Generate and save an invoice objects for opportunity.

    :Arg sender: The model class that sent the signal (SelectTaskCode).
    :Arg instance: The actual instance of SelectTaskCode that was saved.
    :Arg created: Boolean indicating if a new record was created.
    :Arg **kwargs: Additional keyword arguments..
    """
    invoice_number = random.randint(1, 999999)
    invoice_number = f"INV-{invoice_number}"
    if created:
        Invoice.objects.create(opportunity=instance, invoice_number=invoice_number)

    # Check if invoice is already created but invoice number is not assigned
    try:
        invoice_object = Invoice.objects.get(opportunity=instance)
        print("Invoice ==>>", invoice_object)
    except Invoice.DoesNotExist:
        Invoice.objects.create(opportunity=instance, invoice_number=invoice_number)


@receiver(post_save, sender=SelectTaskCode)
def save_task_mapping_tasks(sender, instance, created, **kwargs):
    """
    Save multiple TaskMapping objects when a SelectTaskCode instance is created.

    :Arg sender: The model class that sent the signal (SelectTaskCode).
    :Arg instance: The actual instance of SelectTaskCode that was saved.
    :Arg created: Boolean indicating if a new record was created.
    :Arg **kwargs: Additional keyword arguments..
    """
    if created:
        TaskMapping.objects.create(
            opportunity=instance.opportunity,
            task=instance.task,
            code=instance.task.name,
            description=instance.task.description,
        )


@receiver(post_save, sender=Document)
def remove_document(sender, instance, created, **kwargs):
    """
    Remove documents.

    :Arg sender: The model class that sent the signal (Document).
    :Arg instance: The actual instance of SelectTaskCode that was saved.
    :Arg created: Boolean indicating if a new record was created.
    :Arg **kwargs: Additional keyword arguments..
    """
    if created:
        document_obj = Document.objects.filter(
            Q(document__isnull=True) | Q(document=""), Q(comment__isnull=True) | Q(comment="")
        )
        # print("document_obj", document_obj)
        document_obj.delete()
