from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from laurel.models import BaseModel
from apps.proposal.task.models import Task
from apps.proposal.product.models import Product
from apps.proposal.labour_cost.models import LabourCost


class EstimationTemplate(BaseModel):
    """
    Reusable templates for common project types.

    Templates help users quickly create opportunities by pre-configuring
    tasks, products, and labor estimates for common project scenarios.

    Design: Uses relational structure instead of JSON blob to maintain
    referential integrity with Product/Task/LabourCost catalogs.
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

    # Estimates (ranges for filtering/discovery)
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

    # Configuration (parameterized templates)
    parameters = models.JSONField(
        _("Template Parameters"),
        default=dict,
        blank=True,
        help_text="User-adjustable parameters like acres, rows, pump HP that compute quantities"
    )

    # Default Settings
    default_margin_percent = models.DecimalField(
        _("Default Margin %"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("25.00")
    )
    default_tax_rate = models.DecimalField(
        _("Default Tax Rate %"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00")
    )

    # Multi-tenant support (added early per Codex feedback)
    organization = models.ForeignKey(
        "user.User",  # Will be Organization model once we build it
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Null = public template available to all"
    )

    # Visibility & Usage
    is_public = models.BooleanField(
        _("Public Template"),
        default=True,
        help_text="Public templates are available to all organizations"
    )
    times_used = models.IntegerField(
        _("Times Used"),
        default=0,
        help_text="How many times this template has been used (will be per-org later)"
    )

    # Versioning (per Codex feedback)
    schema_version = models.CharField(
        _("Schema Version"),
        max_length=10,
        default="1.0",
        help_text="Template schema version for migration safety"
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
        indexes = [
            models.Index(fields=["industry", "project_type"]),
            models.Index(fields=["is_public", "organization"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.industry})"

    def increment_usage(self):
        """Increment times_used counter when template is applied"""
        self.times_used += 1
        self.save(update_fields=["times_used"])


class TemplateTask(BaseModel):
    """
    Tasks included in a template.

    Links to real Task catalog but stores template-specific adjustments
    like default hours and sequence order.
    """
    template = models.ForeignKey(
        EstimationTemplate,
        on_delete=models.CASCADE,
        related_name="template_tasks"
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        help_text="Reference to actual task in catalog"
    )

    # Template-specific overrides
    default_hours = models.DecimalField(
        _("Default Hours"),
        max_digits=10,
        decimal_places=2,
        help_text="Typical hours for this task in this template"
    )
    sequence = models.IntegerField(
        _("Sequence"),
        default=0,
        help_text="Order tasks appear in template"
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text="Template-specific notes or instructions"
    )

    # Optional: Parameter-driven hours (e.g., "hours_per_acre * acres")
    hours_formula = models.CharField(
        _("Hours Formula"),
        max_length=255,
        blank=True,
        help_text="e.g., 'base_hours + (acres * 2)' for parameterized templates"
    )

    class Meta:
        verbose_name = "Template Task"
        verbose_name_plural = "Template Tasks"
        ordering = ["sequence", "created_at"]
        unique_together = [["template", "task", "sequence"]]

    def __str__(self):
        return f"{self.template.name} - {self.task.name}"


class TemplateProduct(BaseModel):
    """
    Products included in a template.

    Links to real Product catalog with template-specific quantities
    and adjustment factors.
    """
    template = models.ForeignKey(
        EstimationTemplate,
        on_delete=models.CASCADE,
        related_name="template_products"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        help_text="Reference to actual product in catalog"
    )

    # Which task this product belongs to (optional)
    template_task = models.ForeignKey(
        TemplateTask,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="products",
        help_text="Which task this product is associated with"
    )

    # Template-specific quantities
    default_quantity = models.DecimalField(
        _("Default Quantity"),
        max_digits=10,
        decimal_places=2,
        help_text="Typical quantity needed"
    )

    # Markup/margin adjustments (can differ from org defaults)
    markup_percent = models.DecimalField(
        _("Markup %"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave blank to use template default"
    )

    # Optional: Parameter-driven quantities
    quantity_formula = models.CharField(
        _("Quantity Formula"),
        max_length=255,
        blank=True,
        help_text="e.g., 'acres * 50' for parameterized templates"
    )

    sequence = models.IntegerField(
        _("Sequence"),
        default=0,
        help_text="Order products appear within task"
    )

    class Meta:
        verbose_name = "Template Product"
        verbose_name_plural = "Template Products"
        ordering = ["sequence", "created_at"]

    def __str__(self):
        return f"{self.template.name} - {self.product.description}"

    def get_effective_markup(self):
        """Get markup to use (template-specific or template default)"""
        return self.markup_percent or self.template.default_margin_percent


class TemplateLabour(BaseModel):
    """
    Labour costs included in a template.

    Links to real LabourCost catalog with template-specific hours.
    """
    template = models.ForeignKey(
        EstimationTemplate,
        on_delete=models.CASCADE,
        related_name="template_labour"
    )
    labour_cost = models.ForeignKey(
        LabourCost,
        on_delete=models.CASCADE,
        help_text="Reference to actual labour cost in catalog"
    )
    template_task = models.ForeignKey(
        TemplateTask,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="labour",
        help_text="Which task this labour is associated with"
    )

    # Template-specific hours
    default_hours = models.DecimalField(
        _("Default Hours"),
        max_digits=10,
        decimal_places=2,
        help_text="Typical hours for this labour type"
    )

    # Optional: Parameter-driven hours
    hours_formula = models.CharField(
        _("Hours Formula"),
        max_length=255,
        blank=True,
        help_text="e.g., 'acres * 1.5' for parameterized templates"
    )

    is_local = models.BooleanField(
        _("Local Rate"),
        default=True,
        help_text="Use local rate (True) or out-of-town rate (False)"
    )

    sequence = models.IntegerField(
        _("Sequence"),
        default=0
    )

    class Meta:
        verbose_name = "Template Labour"
        verbose_name_plural = "Template Labour"
        ordering = ["sequence", "created_at"]

    def __str__(self):
        return f"{self.template.name} - {self.labour_cost.labour_task}"
