from django.db import models
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from laurel.models import BaseModel
from apps.proposal.opportunity.models import Opportunity
from apps.proposal.product.models import Product


class BidSchedule(BaseModel):
    """
    Master list of bid items from RFP.

    Represents one line item in the RFP's bid schedule.
    Each bid schedule item gets detailed estimation in BidItem.
    """

    # Relationship
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name="bid_schedule"
    )

    # RFP Info
    item_code = models.CharField(
        _("Item Code"),
        max_length=50,
        help_text="e.g., '100', '200', 'A-1'"
    )
    description = models.TextField(_("Description"))

    # Engineer's Estimate (from RFP)
    engineer_estimate = models.DecimalField(
        _("Engineer's Estimate"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Agency's estimated cost from RFP"
    )

    # Status & Color Coding
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('estimating', 'Estimating'),
        ('quoted', 'Quoted'),
        ('complete', 'Complete'),
        ('not_needed', 'Not Needed'),
    ]
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    COLOR_CHOICES = [
        ('green', '🟢 Green - Done'),
        ('red', '🔴 Red - Need Work'),
        ('yellow', '🟡 Yellow - Need Quote'),
        ('orange', '🟠 Orange - Waiting'),
        ('black', '⚫ Black - Not Needed'),
    ]
    color_code = models.CharField(
        _("Color Code"),
        max_length=20,
        choices=COLOR_CHOICES,
        default='red'
    )

    # Sequence
    sequence = models.IntegerField(
        _("Sequence"),
        default=0,
        help_text="Order in bid schedule"
    )

    # Notes
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text="Internal notes about this bid item"
    )

    class Meta:
        verbose_name = "Bid Schedule Item"
        verbose_name_plural = "Bid Schedule Items"
        ordering = ["sequence", "item_code"]
        unique_together = [["opportunity", "item_code"]]

    def __str__(self):
        return f"{self.item_code} - {self.description[:50]}"

    def get_total_cost(self):
        """Calculate total cost from related BidItem"""
        try:
            return self.bid_item.our_cost
        except:
            return Decimal('0.00')

    def get_sale_price(self):
        """Calculate sale price from related BidItem"""
        try:
            return self.bid_item.sale_price
        except:
            return Decimal('0.00')


class BidItem(BaseModel):
    """
    Detailed estimate for a bid schedule item.

    Contains materials, labor, equipment, subcontractors with costs.
    One-to-one with BidSchedule.
    """

    # One-to-one with BidSchedule
    bid_schedule = models.OneToOneField(
        BidSchedule,
        on_delete=models.CASCADE,
        related_name="bid_item"
    )

    # Totals (calculated from line items)
    materials_total = models.DecimalField(
        _("Materials Total"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    labor_total = models.DecimalField(
        _("Labor Total"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    equipment_total = models.DecimalField(
        _("Equipment Total"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    subcontractor_total = models.DecimalField(
        _("Subcontractor Total"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )

    # Calculated Fields
    our_cost = models.DecimalField(
        _("Our Cost"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Sum of materials + labor + equipment + subs"
    )
    margin_percent = models.DecimalField(
        _("Margin %"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('25.00'),
        help_text="Profit margin percentage"
    )
    margin_amount = models.DecimalField(
        _("Margin Amount"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    sale_price = models.DecimalField(
        _("Sale Price"),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Our cost + margin"
    )

    class Meta:
        verbose_name = "Bid Item Detail"
        verbose_name_plural = "Bid Item Details"

    def __str__(self):
        return f"Bid Item for {self.bid_schedule.item_code}"

    def calculate_totals(self):
        """Recalculate all totals from line items"""
        self.materials_total = sum(
            [m.total_cost for m in self.materials.all()],
            Decimal('0.00')
        )
        self.labor_total = sum(
            [l.total_cost for l in self.labor.all()],
            Decimal('0.00')
        )
        self.equipment_total = sum(
            [e.total_cost for e in self.equipment.all()],
            Decimal('0.00')
        )
        # Subcontractor total is manual entry

        self.our_cost = (
            self.materials_total +
            self.labor_total +
            self.equipment_total +
            self.subcontractor_total
        )

        self.margin_amount = self.our_cost * (self.margin_percent / Decimal('100'))
        self.sale_price = self.our_cost + self.margin_amount

        self.save()


class BidItemMaterial(BaseModel):
    """
    Material line item within a bid item.

    Links to Product catalog (from NetSuite import).
    """

    bid_item = models.ForeignKey(
        BidItem,
        on_delete=models.CASCADE,
        related_name="materials"
    )

    # Link to Product catalog
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Product from catalog"
    )

    # NetSuite reference (for export)
    netsuite_internal_id = models.IntegerField(
        _("NetSuite Internal ID"),
        null=True,
        blank=True,
        help_text="Internal ID from Items42.xls for NetSuite import"
    )

    # Material Details
    name = models.CharField(
        _("Name"),
        max_length=255,
        help_text="Product name/description"
    )
    quantity = models.DecimalField(
        _("Quantity"),
        max_digits=10,
        decimal_places=2
    )
    unit = models.CharField(
        _("Unit"),
        max_length=50,
        default="EA",
        help_text="e.g., EA, FT, GAL, LB"
    )
    unit_cost = models.DecimalField(
        _("Unit Cost"),
        max_digits=10,
        decimal_places=2,
        help_text="Cost per unit (from NetSuite)"
    )
    total_cost = models.DecimalField(
        _("Total Cost"),
        max_digits=12,
        decimal_places=2,
        help_text="Quantity × Unit Cost"
    )

    # Sequence
    sequence = models.IntegerField(
        _("Sequence"),
        default=0
    )

    # Notes
    notes = models.TextField(
        _("Notes"),
        blank=True
    )

    class Meta:
        verbose_name = "Bid Item Material"
        verbose_name_plural = "Bid Item Materials"
        ordering = ["sequence", "created_at"]

    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit}"

    def save(self, *args, **kwargs):
        # Auto-calculate total_cost
        self.total_cost = self.quantity * self.unit_cost

        # Get netsuite_internal_id from product if linked
        if self.product:
            self.netsuite_internal_id = self.product.internal_id
            self.unit_cost = self.product.std_cost

        super().save(*args, **kwargs)

        # Recalculate bid item totals
        self.bid_item.calculate_totals()


class BidItemLabor(BaseModel):
    """
    Labor line item within a bid item.
    """

    bid_item = models.ForeignKey(
        BidItem,
        on_delete=models.CASCADE,
        related_name="labor"
    )

    # Labor Details
    classification = models.CharField(
        _("Classification"),
        max_length=100,
        help_text="e.g., Laborer, Operator, Electrician"
    )
    hours = models.DecimalField(
        _("Hours"),
        max_digits=10,
        decimal_places=2
    )
    rate = models.DecimalField(
        _("Rate"),
        max_digits=10,
        decimal_places=2,
        help_text="Hourly rate (including burden)"
    )
    total_cost = models.DecimalField(
        _("Total Cost"),
        max_digits=12,
        decimal_places=2
    )

    # Sequence
    sequence = models.IntegerField(
        _("Sequence"),
        default=0
    )

    class Meta:
        verbose_name = "Bid Item Labor"
        verbose_name_plural = "Bid Item Labor"
        ordering = ["sequence", "created_at"]

    def __str__(self):
        return f"{self.classification} - {self.hours} hrs"

    def save(self, *args, **kwargs):
        # Auto-calculate total_cost
        self.total_cost = self.hours * self.rate
        super().save(*args, **kwargs)

        # Recalculate bid item totals
        self.bid_item.calculate_totals()


class BidItemEquipment(BaseModel):
    """
    Equipment line item within a bid item.
    """

    bid_item = models.ForeignKey(
        BidItem,
        on_delete=models.CASCADE,
        related_name="equipment"
    )

    # Equipment Details
    equipment_type = models.CharField(
        _("Equipment Type"),
        max_length=100,
        help_text="e.g., Excavator, Loader, Truck"
    )
    hours = models.DecimalField(
        _("Hours"),
        max_digits=10,
        decimal_places=2
    )
    rate = models.DecimalField(
        _("Rate"),
        max_digits=10,
        decimal_places=2,
        help_text="Hourly rental rate"
    )
    total_cost = models.DecimalField(
        _("Total Cost"),
        max_digits=12,
        decimal_places=2
    )

    # Fuel
    fuel_gallons = models.DecimalField(
        _("Fuel (Gallons)"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    fuel_cost_per_gallon = models.DecimalField(
        _("Fuel Cost/Gallon"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('4.50')
    )

    # Sequence
    sequence = models.IntegerField(
        _("Sequence"),
        default=0
    )

    class Meta:
        verbose_name = "Bid Item Equipment"
        verbose_name_plural = "Bid Item Equipment"
        ordering = ["sequence", "created_at"]

    def __str__(self):
        return f"{self.equipment_type} - {self.hours} hrs"

    def save(self, *args, **kwargs):
        # Auto-calculate total_cost (rental + fuel)
        rental_cost = self.hours * self.rate
        fuel_cost = self.fuel_gallons * self.fuel_cost_per_gallon
        self.total_cost = rental_cost + fuel_cost

        super().save(*args, **kwargs)

        # Recalculate bid item totals
        self.bid_item.calculate_totals()
