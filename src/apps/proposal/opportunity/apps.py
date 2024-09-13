from django.apps import AppConfig


class OpportunityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.proposal.opportunity"

    def ready(self):
        import apps.proposal.opportunity.signals
