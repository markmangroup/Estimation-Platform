from django.db import models
from django.utils.translation import gettext_lazy as _

from laurel.models import BaseModel


class EstimationTemplate(BaseModel):
    """
    Reusable templates for common project types.

    Templates help users quickly create opportunities by pre-filling
    tasks, products, and labor estimates for common project scenarios.
    """

    # Basic Info
    name = models.CharField(_("Template Name"), max_length=255)
    description = models.TextField(_("Description"))
    industry = models.CharField(
        _("Industry"),
        max_length=100,
        help_text="e.g., Agriculture, Irrigation, Landscaping"
    )
    project_type = models.CharField(
        _("Project Type"),
        max_length=100,
        help_text="e.g., Drip Irrigation System, Sprinkler Installation"
    )

    # Estimates
    estimated_hours = models.IntegerField(
        _("Estimated Hours"),
        help_text="Typical labor hours for this project type"
    )
    estimated_cost_min = models.DecimalField(
        _("Estimated Cost (Min)"),
        max_digits=10,
        decimal_places=2,
        help_text="Minimum typical project cost"
    )
    estimated_cost_max = models.DecimalField(
        _("Estimated Cost (Max)"),
        max_digits=10,
        decimal_places=2,
        help_text="Maximum typical project cost"
    )

    # Template Data (JSON structure)
    template_data = models.JSONField(
        _("Template Data"),
        help_text="Stores selected tasks, products, labor costs, and quantities"
    )

    # Visibility & Usage
    is_public = models.BooleanField(
        _("Public Template"),
        default=True,
        help_text="Public templates are available to all users"
    )
    times_used = models.IntegerField(
        _("Times Used"),
        default=0,
        help_text="How many times this template has been used"
    )

    # Thumbnail/Preview
    thumbnail = models.ImageField(
        _("Thumbnail"),
        upload_to="template_thumbnails/",
        blank=True,
        null=True,
        help_text="Visual preview image for template browser"
    )

    class Meta:
        verbose_name = "Estimation Template"
        verbose_name_plural = "Estimation Templates"
        ordering = ["-times_used", "name"]

    def __str__(self):
        return f"{self.name} ({self.industry})"

    def increment_usage(self):
        """Increment times_used counter when template is applied"""
        self.times_used += 1
        self.save(update_fields=["times_used"])
