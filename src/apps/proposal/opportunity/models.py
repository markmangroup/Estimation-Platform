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


class TaskMapping(BaseModel):

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="task_mapping_opportunity")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_mapping_tasks", blank=True, null=True)

    # Manually added tasks
    code = models.CharField(_("Task Code"), max_length=255, blank=True, null=True)
    description = models.CharField(_("Task Description"), max_length=255, blank=True, null=True)

    labor_gp_percent = models.FloatField(_("Labor GP %"), max_length=255, default=25.0, blank=True, null=True)
    mat_gp_percent = models.FloatField(_("Mat GP %"), max_length=255, default=10.0, blank=True, null=True)
    s_and_h = models.FloatField(_("S & H"), max_length=255, default=10.0, blank=True, null=True)

    include = models.BooleanField(_("Include Items"), default=True)

    def __str__(self):
        if self.code:
            return f"{self.id} - {self.opportunity.document_number} - {self.code}"
        return f"{self.id} - {self.opportunity.document_number} - {self.task.name}"

    @property
    def labor_cost(self):
        """
        Return fixed labor cost. Modify this if you have a real calculation.
        """
        return 1000  # Example fixed value; replace with actual logic

    @property
    def labor_sell(self):
        """
        Calculate `Labor sell` based on `labor_cost` and `labor_gp_percent`.
        """
        if self.labor_cost is not None and self.labor_gp_percent is not None:
            try:
                labor_cost = float(self.labor_cost)
                labor_gp_percent = float(self.labor_gp_percent) / 100
                if (1 - labor_gp_percent) != 0:
                    return round(labor_cost / (1 - labor_gp_percent), 2)
            except (ValueError, ZeroDivisionError):
                return 0
        return 0

    @property
    def labor_gp(self):
        """
        Calculate `Labor GP $` as the difference between `labor_sell` and `labor_cost`.
        """
        try:
            labor_sell = float(self.labor_sell)
            labor_cost = float(self.labor_cost)
            return round(labor_sell - labor_cost, 2)
        except ValueError:
            return 0

    @property
    def mat_cost(self):
        """
        Return fixed MAT cost. Modify this if you have a real calculation.
        """
        return 12  # Example fixed value; replace with actual logic

    @property
    def mat_plus_mu(self):
        """
        Calculate `MAT + Mu` based on `mat_cost` and `mat_gp_percent`.
        """
        if self.mat_gp_percent is not None:
            try:
                mat_cost = float(self.mat_cost)
                mat_gp_percent = float(self.mat_gp_percent) / 100  # Convert percentage to decimal
                if (1 - mat_gp_percent) != 0:
                    return round(mat_cost / (1 - mat_gp_percent), 2)
            except (ValueError, ZeroDivisionError):
                return 0
        return 0

    @property
    def mat_gp(self):
        """
        Calculate `MAT GP $` as the difference between `mat_plus_mu` and `mat_cost`.
        """
        try:
            return round(self.mat_plus_mu - float(self.mat_cost), 2)
        except ValueError:
            return 0

    @property
    def sales_tax(self):
        """
        Calculate `Sales Tax` as 25% of `mat_plus_mu`.
        """
        try:
            return round(self.mat_plus_mu * 0.25, 2)
        except (ValueError, TypeError):
            return 0

    @property
    def mat_sell(self):
        """
        Calculate `MAT sell` as the sum of `mat_plus_mu` and `sales_tax`.
        """
        try:
            return round(self.mat_plus_mu + self.sales_tax, 2)
        except (ValueError, TypeError):
            return 0

    @property
    def mat_tax_labor(self):
        """
        Calculate `MAT, TAX, LABOR` as the sum of `mat_sell` and `labor_sell`.
        """
        try:
            return round(self.mat_sell + self.labor_sell, 2)
        except (ValueError, TypeError):
            return 0

    @property
    def comb_gp(self):
        """
        Calculate `COMB GP %` as the ratio of total GP to total cost.
        """
        try:
            total_gp = self.mat_gp + self.labor_gp
            total_cost = self.labor_sell + self.mat_plus_mu
            return round((total_gp / total_cost) * 100, 2) if total_cost != 0 else 0
        except (ValueError, ZeroDivisionError):
            return 0

    @property
    def acre(self):
        """
        Calculate `$/Acre` based on `mat_tax_labor` and `mat_gp_percent`.
        """
        if self.mat_gp_percent is not None:
            try:
                return self.mat_tax_labor / float(self.mat_gp_percent) if float(self.mat_gp_percent) != 0 else 0
            except (ValueError, ZeroDivisionError):
                return 0
        return 0

    class Meta:
        verbose_name = "Proposal Task Mapping"


class AssignedProduct(BaseModel):

    task_mapping = models.ForeignKey(TaskMapping, on_delete=models.CASCADE, related_name="assigned_products")
    is_assign = models.BooleanField(_("Is Assigned Product/Labour"), default=False)

    # Task-Product
    quantity = models.FloatField(_("Quantity"), blank=True, null=True)
    item_code = models.CharField(_("Item Code"), max_length=255, blank=True, null=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    standard_cost = models.FloatField(_("Standard Cost"), blank=True, null=True)
    vendor_quoted_cost = models.FloatField(_("Vendor Quoted Cost"), blank=True, null=True)
    vendor = models.CharField(_("Vendor"), max_length=255, blank=True, null=True)
    comment = models.CharField(_("Comment"), max_length=255, blank=True, null=True)

    # Task-Labor
    labor_task = models.CharField(_("Labor Task"), max_length=255, blank=True, null=True)
    local_cost = models.FloatField(_("Labor Local Cost"), blank=True, null=True)
    out_of_town_cost = models.FloatField(_("Out Of Town Cost"), blank=True, null=True)

    def __str__(self):
        return f"{self.id} - {self.task_mapping.id}"

    class Meta:
        verbose_name = "Proposal Assigned Product"


class ProposalCreation(BaseModel):

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="proposal_creation_opportunity")
    group_name = models.CharField(_("Group Name"), max_length=255)
    task_mapping = models.ForeignKey(TaskMapping, on_delete=models.CASCADE, related_name="proposal_tasks")

    def __str__(self):
        return f"{self.id} - {self.group_name} - {self.task_mapping.id}"

    class Meta:
        verbose_name = "Proposal Creation"
