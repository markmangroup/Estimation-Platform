from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.proposal.customer.models import Customer
from apps.proposal.task.models import Task
from laurel.models import BaseModel


class Opportunity(BaseModel):
    """
    Opportunity Model.
    """

    STAGE_1 = "Select Task Code"
    STAGE_2 = "Upload CAD File"
    STAGE_3 = "Material List"
    STAGE_4 = "Task Mapping"
    STAGE_5 = "Generate Estimate"
    STAGE_6 = "Proposal Creation"
    STAGE_7 = "Proposal Preview"
    STAGE_8 = "Final Document"

    ESTIMATION_STAGE_CHOICES = [
        (STAGE_1, "Select Task Code"),
        (STAGE_2, "Upload CAD File"),
        (STAGE_3, "Material List"),
        (STAGE_4, "Task Mapping"),
        (STAGE_5, "Generate Estimate"),
        (STAGE_6, "Proposal Creation"),
        (STAGE_7, "Proposal Preview"),
        (STAGE_8, "Final Document"),
    ]

    internal_id = models.IntegerField(_("Internal Id"), unique=True, primary_key=True)
    sales_rep = models.CharField(_("Sales Rep"), max_length=255)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="customers",
        blank=True,
        null=True,
    )
    location = models.CharField(_("Location"), max_length=255)
    opportunity_class = models.CharField(_("Opportunity Class"), max_length=255)
    title = models.CharField(_("Title"), max_length=255)
    document_number = models.CharField(_("Document Number"), max_length=255)
    ranch_address = models.TextField(_("Ranch Address"), max_length=255, blank=True, null=True)
    opportunity_status = models.CharField(_("Opportunity Status"), max_length=255)
    projected_total = models.CharField(
        _("Projected Total"),
    )
    expected_margin = models.FloatField(
        _("Expected Margin"),
    )
    margin_amount = models.CharField(
        _("Margin Amount"),
    )
    win_probability = models.CharField(_("Win Probability"), blank=True, null=True)
    expected_close = models.DateField(
        _("Expected Close"),
    )
    opportunity_notes = models.TextField(_("Opportunity Notes"), blank=True, null=True)
    scope = models.TextField(_("Scope"), blank=True, null=True)
    designer = models.CharField(_("Designer"), max_length=255, blank=True, null=True)
    estimator = models.CharField(_("Estimator"), max_length=255, blank=True, null=True)
    pump_electrical_designer = models.CharField(_("Pump & Electrical Designer"), max_length=255, blank=True, null=True)
    design_estimation_note = models.TextField(_("Design/Estimation Note"), blank=True, null=True)
    estimation_stage = models.CharField(
        _("Estimation Stage"),
        max_length=50,
        choices=ESTIMATION_STAGE_CHOICES,
        default=STAGE_1,
    )

    def __str__(self):
        return f"{self.document_number} - {self.customer}"

    def get_current_stage_constant(self):
        stage_mapping = {
            self.STAGE_1: "STAGE_1",
            self.STAGE_2: "STAGE_2",
            self.STAGE_3: "STAGE_3",
            self.STAGE_4: "STAGE_4",
            self.STAGE_5: "STAGE_5",
            self.STAGE_6: "STAGE_6",
            self.STAGE_7: "STAGE_7",
            self.STAGE_8: "STAGE_8",
        }
        return stage_mapping.get(self.estimation_stage, "Unknown Stage")

    class Meta:
        verbose_name = "Proposal Opportunitie"


class SelectTaskCode(BaseModel):

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="opportunity")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="tasks")

    def __str__(self):
        return f"{self.opportunity.document_number} - {self.task.name}"

    class Meta:
        verbose_name = "Proposal TaskCode"


class Document(BaseModel):

    STAGE_1 = "Select Task Code"
    STAGE_2 = "Upload CAD File"
    STAGE_3 = "Material List"
    STAGE_4 = "Task Mapping"
    STAGE_5 = "Generate Estimate"
    STAGE_6 = "Proposal Creation"
    STAGE_7 = "Proposal Preview"
    STAGE_8 = "Final Document"

    ESTIMATION_STAGE_CHOICES = [
        (STAGE_1, "Select Task Code"),
        (STAGE_2, "Upload CAD File"),
        (STAGE_3, "Material List"),
        (STAGE_4, "Task Mapping"),
        (STAGE_5, "Generate Estimate"),
        (STAGE_6, "Proposal Creation"),
        (STAGE_7, "Proposal Preview"),
        (STAGE_8, "Final Document"),
    ]

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, blank=True, null=True)
    document = models.FileField(_("Document"), upload_to="documents/")
    stage = models.CharField(_("Stage"), max_length=50, choices=ESTIMATION_STAGE_CHOICES, default=STAGE_1)
    comment = models.TextField(_("Comment"), blank=True, null=True)

    def __str__(self):
        return f"{self.stage} - {self.document.name}"

    class Meta:
        verbose_name = "Proposal Document"


class MaterialList(BaseModel):

    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.CASCADE, blank=True, null=True, related_name="opportunity_materials"
    )
    quantity = models.IntegerField(
        _("Quantity"),
    )
    description = models.CharField(_("Description"), max_length=255)
    item_number = models.CharField(_("Item Number"), max_length=255)

    def __str__(self):
        return f"{self.item_number}"

    class Meta:
        verbose_name = "Proposal Material List"


class GlueAndAdditionalMaterial(BaseModel):

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="opportunity_glue_and_additional_material",
    )
    quantity = models.IntegerField(
        _("Quantity"),
    )
    description = models.CharField(_("Description"), max_length=255)
    item_number = models.CharField(_("Item Number"), max_length=255)
    category = models.CharField(_("Category"), max_length=255)

    def __str__(self):
        return f"{self.item_number}"

    class Meta:
        verbose_name = "Proposal Glue & Additional Material"


class PreliminaryMaterialList(BaseModel):

    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.CASCADE, blank=True, null=True, related_name="opportunity_preliminary_list"
    )
    irricad_imported_quantities = models.CharField(
        _("Irricad Imported Quantities"), max_length=255, blank=True, null=True
    )
    glue_and_additional_mat_quantities = models.CharField(
        _("Glue & Additional Mat'l Quantities"), max_length=255, blank=True, null=True
    )
    combined_quantities_from_both_import = models.CharField(
        _("Combined Quantities from both Import"), max_length=255, blank=True, null=True
    )
    description = models.CharField(_("Description"), max_length=255)
    item_number = models.CharField(_("Item Number"), max_length=255)
    category = models.CharField(_("Category"), max_length=255)
    bag_bundle_quantity = models.CharField(_("Bag/Bundle Quantity"), max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.item_number}"

    class Meta:
        verbose_name = "Proposal Preliminary Material"
