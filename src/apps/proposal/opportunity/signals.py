import random

from django.db.models import Q
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.constants import LOGGER
from apps.proposal.opportunity.models import (
    Document,
    Invoice,
    Opportunity,
    SelectTaskCode,
    TaskMapping,
)

SAVING_FLAG = False

@receiver(post_save, sender=Opportunity)
def generate_invoice_details(sender, instance, created, **kwargs):
    """
    Generate and save an invoice objects for opportunity.

    Args:
        sender: The model class that sent the signal (SelectTaskCode).
        instance: The actual instance of SelectTaskCode that was saved.
        created: Boolean indicating if a new record was created.
        **kwargs: Additional keyword arguments..
    """
    invoice_number = random.randint(1, 999999)
    invoice_number = f"INV-{invoice_number}"
    if created:
        Invoice.objects.create(opportunity=instance, invoice_number=invoice_number)

    try:  # Check if invoice is already created but invoice number is not assigned
        invoice_object = Invoice.objects.get(opportunity=instance)
        LOGGER.info(f"-- Invoice -- {invoice_object}")
    except Invoice.DoesNotExist:
        LOGGER.info(f"-- Invoice created for opportunity -- ")
        Invoice.objects.create(opportunity=instance, invoice_number=invoice_number)


@receiver(post_save, sender=SelectTaskCode)
def save_task_mapping_tasks(sender, instance, created, **kwargs):
    """
    Save multiple TaskMapping objects when a Task Mapping instance is created.

    Args:
        sender: The model class that sent the signal (Task Mapping).
        instance: The actual instance of Task Mapping that was saved.
        created: Boolean indicating if a new record was created.
        **kwargs: Additional keyword arguments..
    """
    if created:
        TaskMapping.objects.create(
            opportunity=instance.opportunity,
            task=instance.task,
            code=instance.task.name,
            description=instance.task.description,
        )
        LOGGER.info(f"-- Task added on task mapping --")
    else:
        try:
            task_mapping_object = TaskMapping.objects.filter(
                opportunity=instance.opportunity,
                task=instance.task,
            ).first()
            task_mapping_object.description = instance.task_description
            task_mapping_object.save()
        except Exception as e:
            LOGGER.error(f"-- An error occurred while sync data with select task code -- {e}")


@receiver(post_save, sender=Document)
def remove_document(sender, instance, created, **kwargs):
    """
    Remove documents.

    Args:
        sender: The model class that sent the signal (Document).
        instance: The actual instance of Document that was saved.
        created: Boolean indicating if a new record was created.
        **kwargs: Additional keyword arguments..
    """
    if created:
        try:
            document_obj = Document.objects.filter(
                Q(document__isnull=True) | Q(document=""), Q(comment__isnull=True) | Q(comment="")
            )
            document_obj.delete()
        except Exception as e:
            LOGGER.error(f"-- An error occurred while remove empty document from db -- {e}")

@receiver(post_save, sender=TaskMapping)
def sync_task_description_value(sender, instance, created, **kwargs):
    """
    Sync task description value while update

    Args:
        sender: The model class that sent the signal (TaskMapping).
        instance: The actual instance of Document that was saved.
        created: Boolean indicating if a new record was created.
        **kwargs: Additional keyword arguments..
    """
    global SAVING_FLAG

    if not created and not SAVING_FLAG:  # Check object is updated
        try:
            SAVING_FLAG = True
            select_task_code = SelectTaskCode.objects.filter(
                opportunity=instance.opportunity, task=instance.task
            ).first()

            select_task_code.task_description = instance.description
            select_task_code.save()
        except Exception as e:
            LOGGER.info(f"-- An error occurred while sync data with select task code -- {e}")
