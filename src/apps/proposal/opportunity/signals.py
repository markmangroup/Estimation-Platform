from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.proposal.opportunity.models import SelectTaskCode, TaskMapping


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
        print("instance ::", instance)
        TaskMapping.objects.create(opportunity=instance.opportunity, task=instance.task)
