import os
import random
from datetime import datetime, timedelta

from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas
from django.db import models
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

from apps.proposal.customer.models import Customer
from apps.proposal.task.models import Task
from laurel.models import BaseModel

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)


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

    job = models.CharField(_("Job"), max_length=255, blank=True, null=True)
    job_name = models.CharField(_("Job Name"), max_length=255, blank=True, null=True)
    ranch_name = models.CharField(_("Ranch Name"), max_length=255, blank=True, null=True)
    project = models.CharField(_("Project"), max_length=255, blank=True, null=True)
    term_and_condition = models.JSONField(_("Term & Condition"), blank=True, null=True)

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
        verbose_name = "Proposal Opportunities"


class SelectTaskCode(BaseModel):

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="opportunity")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="tasks")
    task_description = models.CharField(_("Task Description"), max_length=255, null=True, blank=True)

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

    @property
    def file_path(self):
        connection_string = os.getenv("AZURE_CONNECTION_STRING")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_name = os.getenv("AZURE_CONTAINER")
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            account_key=os.getenv("AZURE_ACCOUNT_KEY"),
            container_name=container_name,
            blob_name=self.document.name,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1),
        )
        file_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{self.document.name}?{sas_token}"
        return file_url

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
    category = models.CharField(
        _("Category"), max_length=255, null=True, blank=True
    )  # Currently we are not using a category

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
    category = models.CharField(_("Category"), max_length=255)  # Currently we are not using a category
    bag_bundle_quantity = models.CharField(
        _("Bag/Bundle Quantity"), max_length=255, blank=True, null=True
    )  # Currently we are not using a bag bundle quantity

    def __str__(self):
        return f"{self.item_number}"

    class Meta:
        verbose_name = "Proposal Preliminary Material"


class TaskMapping(BaseModel):

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="task_mapping_opportunity")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_mapping_tasks", blank=True, null=True)

    # Assign labor
    is_assign_task = models.BooleanField(_("Is Assign Task"), default=False)
    assign_to = models.CharField(_("Assign to"), max_length=255, null=True, blank=True)

    # Manually added tasks
    code = models.CharField(_("Task Code"), max_length=255, blank=True, null=True)
    description = models.CharField(_("Task Description"), max_length=255, blank=True, null=True)

    labor_gp_percent = models.FloatField(_("Labor GP %"), max_length=255, default=25.0, blank=True, null=True)
    mat_gp_percent = models.FloatField(_("Mat GP %"), max_length=255, default=10.0, blank=True, null=True)
    s_and_h = models.FloatField(_("S & H"), max_length=255, default=10.0, blank=True, null=True)

    include = models.BooleanField(_("Include Items"), default=True)
    extra_description = models.JSONField(_("Extra Description"), blank=True, null=True)
    approve = models.CharField(_("Approve & Initial"), max_length=255, blank=True, null=True)

    def __str__(self):
        if self.code:
            return f"{self.id} - {self.opportunity.document_number} - {self.code}"
        return f"{self.id} - {self.opportunity.document_number} - {self.task.name}"

    @property
    def labor_cost(self):
        """
        Calculate the labor cost based on assigned products for tasks related to this TaskMapping instance.
        """
        if self.is_assign_task:
            task_mappings = TaskMapping.objects.filter(
                opportunity=self.opportunity, task__description__icontains="labor"
            )

            # Initialize total calculations
            total_quantity = 0
            total_price = 0.0
            total_percent = 0.0

            for task in task_mappings:
                if task.assign_to == self.code and task.assign_to:
                    assigned_products = AssignedProduct.objects.filter(task_mapping_id=task.id)
                    total_quantity += sum(product.quantity for product in assigned_products)
                    total_price += sum(
                        product.vendor_quoted_cost * product.quantity if product.vendor_quoted_cost else product.standard_cost * product.quantity
                        for product in assigned_products
                    )
                    total_percent += sum(product.gross_profit_percentage for product in assigned_products)

            return round(total_price, 2)

        elif not self.assign_to:
            task_mappings = TaskMapping.objects.filter(
                opportunity=self.opportunity, task__description__icontains="labor"
            )

            # Initialize total calculations
            total_quantity = 0
            total_price = 0.0
            total_percent = 0.0

            for task in task_mappings:
                if not task.assign_to:
                    assigned_products = AssignedProduct.objects.filter(task_mapping_id=task.id)
                    total_quantity += sum(product.quantity for product in assigned_products)
                    total_price += sum(
                        product.vendor_quoted_cost * product.quantity if product.vendor_quoted_cost else product.standard_cost * product.quantity
                        for product in assigned_products
                    )
                    total_percent += sum(product.gross_profit_percentage for product in assigned_products)
            return round(total_price, 2)

        return 0

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
        Calculate the mat cost based on assigned products for tasks related to this TaskMapping instance.
        """
        task_mappings = TaskMapping.objects.filter(opportunity=self.opportunity)
        filtered_task_mappings = task_mappings.exclude(task__description__icontains="labor")

        assigned_products = AssignedProduct.objects.filter(task_mapping_id=self.id)

        total_quantity = 0
        total_price = 0.0
        total_percent = 0.0

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity += sum(product.quantity for product in task_assigned_products)
            total_price += sum(
                product.vendor_quoted_cost if product.vendor_quoted_cost else product.standard_cost
                for product in task_assigned_products
            )
            total_percent += sum(product.gross_profit_percentage for product in task_assigned_products)

        return round(total_price, 2)

    @property
    def mat_plus_mu(self):
        """
        Calculate `MAT + Mu` based on `mat_cost` and `mat_gp_percent`.
        """
        if self.mat_gp_percent is not None:
            try:
                mat_cost = float(self.mat_cost)
                mat_gp_percent = float(self.mat_gp_percent) / 100
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
    is_select = models.BooleanField(_("Is Selected"), default=False)

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
    sequence = models.IntegerField(default=0)

    @property
    def sell(self):
        if self.vendor_quoted_cost:
            sell_sum = 0.25 + (self.vendor_quoted_cost * self.quantity)
        else:
            sell_sum = 0.25 + (self.standard_cost * self.quantity)
        return round(sell_sum, 2)

    @property
    def gross_profit(self):
        if self.vendor_quoted_cost:
            gross_profit_sum = self.sell - (self.vendor_quoted_cost * self.quantity)
        else:
            gross_profit_sum = self.sell - (self.standard_cost * self.quantity)
        return round(gross_profit_sum, 2)

    @property
    def gross_profit_percentage(self):
        gross_profit_percentage_sum = (self.gross_profit / self.sell) * 100
        return round(gross_profit_percentage_sum, 2)

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


class Invoice(BaseModel):

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="invoice_opportunity")
    invoice_number = models.CharField(_("Invoice Number"), max_length=255, null=True, blank=True)
    invoice_data = models.DateTimeField("Invoice Data", null=True, blank=True)
    total_amount = models.FloatField(_("Total Amount"), default=0.0)
    deposit_amount = models.FloatField(_("Deposit Amount"), default=0.0)
    deu_amount = models.FloatField(_("Deu Amount"), default=0.0)
    tax_rate = models.FloatField(_("Tax Rate"), default=0.0)
    sales_tax = models.FloatField(_("Sales Tax"), default=0.0)
    other_tax = models.FloatField(_("Other Tax"), default=0.0)
    deposit_address = models.TextField(_("Deposit Address"), null=True, blank=True)
    billing_address = models.TextField(_("Remit To"), null=True, blank=True)

    # --buyer details
    buyer = models.CharField(_("Buyer"), max_length=255, null=True, blank=True)
    buyer_date = models.DateTimeField(_("Buyer Date"), null=True, blank=True)
    buyer_name = models.CharField(_("Buyer Name"), max_length=255, null=True, blank=True)
    buyer_position = models.CharField(_("Buyer Position"), max_length=255, null=True, blank=True)

    # --seller details
    seller = models.CharField(_("Seller"), max_length=255, null=True, blank=True)
    seller_date = models.DateTimeField(_("Seller Date"), null=True, blank=True)
    seller_name = models.CharField(_("Seller Name"), max_length=255, null=True, blank=True)
    seller_position = models.CharField(_("Seller Position"), max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.id} - {self.opportunity.document_number} - {self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            invoice_number = random.randint(1, 999999)
            self.invoice_number = f"INV-{self.id}{invoice_number}"

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Proposal Invoice"
