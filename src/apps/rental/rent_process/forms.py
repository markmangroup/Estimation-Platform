from datetime import datetime
from django import forms
from django.core.exceptions import ValidationError
from apps.rental.rent_process.models import *
from apps.rental.account_manager.models import AccountManager
from apps.rental.customer.models import RentalCustomer
from apps.rental.product.models import RentalProduct
from apps.rental.rent_process.models import Order, OrderFormPermissionModel,OrderItem,RecurringOrder

class ImportOrderCSVForm(forms.Form):
    """Form for uploading warehouse data from CSV, XLSX, or XLS files."""

    csv_file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "accept": ".xlsx, .xls, .csv",
                "class": "custom-file-input",
                "id": "inputGroupFile01",
            }
        )
    )

    REQUIRED_COLUMNS = [
        "Order ID",
        "Delivery",
        "Status",
        "Customer",
        "Order Amount",
        "Account Manager",
        "Start Date",
        "End Date",
        "Reccurence Type",
        "Last Updated Date",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["csv_file"].help_text = (
            "File must be in .xlsx, .xls, or .csv format "
            "and contain the following columns in the specified order: "
            f"{', '.join(self.REQUIRED_COLUMNS)}."
        )

    def clean_csv_file(self):
        """
        Validate the uploaded CSV file.
        Checks for presence and valid extension.
        """
        csv_file = self.cleaned_data.get("csv_file")
        if not csv_file:
            raise ValidationError("This field is required.")

        valid_extensions = {".xlsx", ".xls", ".csv"}
        extension = f".{csv_file.name.split('.')[-1].lower()}"

        if extension not in valid_extensions:
            raise ValidationError("Only .csv, .xlsx, and .xls files are accepted.")

        return csv_file
    
class DeliveryForm(forms.ModelForm):
    po_number = forms.CharField(required=False)
    shipping_carrier = forms.ChoiceField(
        choices=[('Internal', 'Internal'), ('Hired', 'Hired')],
        required=False
    )
    class Meta:
        model = Delivery
        fields = ["pickup_date", "delivery_date", "shipping_carrier", "pickup_site", "delivery_site", "po_number"]
        widgets = {
            "pickup_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "delivery_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "shipping_carrier": forms.Select(attrs={"class": "form-control"}),
            "pickup_site": forms.TextInput(attrs={"class": "form-control"}),
            "delivery_site": forms.TextInput(attrs={"class": "form-control"}),
            "po_number": forms.TextInput(attrs={"class": "form-control"}),
        }
        
        

class RecurringOrderEditForm(forms.ModelForm):
    no_of_product = forms.IntegerField(
        label="Number of Products",
        widget=forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
        required=True,
    )
    repeat_date_range = forms.CharField(
        label="Repeat Date Range",
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = RecurringOrder
        fields = [
            "no_of_product",
            "repeat_date_range",
        ]
        widgets = {
            "order": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "no_of_product": "Number of Products",
            "repeat_date_range": "Repeat Date Range",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.order:
            order_instance = self.instance.order
            self.fields["order__customer"] = forms.CharField(
                initial=order_instance.customer.name, 
                widget=forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
                required=False
            )
            self.fields["order__rental_start_date"] = forms.DateField(
                initial=order_instance.rental_start_date, 
                widget=forms.DateInput(attrs={"class": "form-control", "readonly": "readonly", "type": "date"}),
                required=False
            )
            self.fields["order__pick_up_location"] = forms.CharField(
                initial=order_instance.pick_up_location, 
                widget=forms.TextInput(attrs={"class": "form-control", "readonly": "readonly"}),
                required=False
            )
            self.fields["order__rent_amount"] = forms.DecimalField(
                initial=order_instance.rent_amount, 
                widget=forms.NumberInput(attrs={"class": "form-control", "readonly": "readonly"}),
                required=False
            )
            self.fields["order__repeat_type"] = forms.ChoiceField(
                initial=order_instance.repeat_type, 
                choices=Order.REPEAT_TYPE_CHOICES, 
                widget=forms.Select(attrs={"class": "form-control"}),
                required=False
            )
        self.fields["no_of_product"].required = True

class OrderForm(forms.ModelForm):
    rental_start_date = forms.DateField(widget=forms.HiddenInput())
    rental_end_date = forms.DateField(widget=forms.HiddenInput())

    customer = forms.ChoiceField(
        choices=[("", "Select a value")] + [(c.id, c.name) for c in RentalCustomer.objects.only('id', 'name')],
        widget=forms.Select(attrs={"class": "form-control disable-first-option"})
    )
    account_manager = forms.ChoiceField(
        choices=[("", "Select a value")] + [(a.id, a.name) for a in AccountManager.objects.only('id', 'name')],
        widget=forms.Select(attrs={"class": "form-control disable-first-option"})
    )
    repeat_type = forms.ChoiceField(
        choices=[("", "Select a value")] + Order.REPEAT_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control disable-first-option"})
    )
    customer_email = forms.EmailField(
        label="Customer Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    rent_per_month = forms.CharField(
        label="Rent Per Month",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "id": "rentPerMonth", "rows": 4, "readonly": "readonly"}),
    )

    class Meta:
        model = Order
        fields = [
            "customer", "account_manager", "link_netsuite", "region",
            "pick_up_location", "delivery_location", "water_source", "crop",
            "rent_amount", "rental_start_date", "rental_end_date", "recurring_order",
            "repeat_type", "repeat_value", "repeat_start_date", "repeat_end_date"
        ]
        widgets = {
            "link_netsuite": forms.URLInput(attrs={"class": "form-control", "placeholder": "Link NetSuite"}),
            "region": forms.TextInput(attrs={"class": "form-control", "placeholder": "Region"}),
            "pick_up_location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Pick-Up Location"}),
            "delivery_location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Delivery Location"}),
            "water_source": forms.TextInput(attrs={"class": "form-control", "placeholder": "Water Source"}),
            "crop": forms.TextInput(attrs={"class": "form-control", "placeholder": "Crop"}),
            "rent_amount": forms.NumberInput(attrs={"class": "form-control", "id": "rentAmount", "placeholder": "Rent Amount"}),
            "rental_start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "rental_end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "recurring_order": forms.CheckboxInput(attrs={"class": "form-check-input", "id": "recurring-checkbox"}),
            "repeat_value": forms.NumberInput(attrs={"class": "form-control", "style": "width: 100px;"}),
            "repeat_start_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "id": "startDate", "style": "width: 150px;"}),
            "repeat_end_date": forms.DateInput(attrs={"class": "form-control", "type": "date", "id": "endDate", "style": "width: 150px;"}),
        }

    def clean_customer(self):
        customer_id = self.cleaned_data["customer"]
        if customer_id:
            return RentalCustomer.objects.get(id=int(customer_id))
        return None
    
    def clean_account_manager(self):
        account_manager = self.cleaned_data["account_manager"]
        if account_manager:
            return AccountManager.objects.get(id=int(account_manager))
        return None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the first instance of OrderFormPermissionModel (assuming single row)
        permissions = OrderFormPermissionModel.objects.first()

        if permissions:
            # Loop through form fields and set required dynamically
            for field_name in self.fields:
                if hasattr(permissions, field_name):
                    self.fields[field_name].required = getattr(permissions, field_name)

        if self.instance.pk:
            self.fields["rental_period"].initial = f"{self.instance.rental_start_date} - {self.instance.rental_end_date}"
            self.fields["repeat_type"].widget.attrs.update({"id": "repeatType"})
            self.fields["repeat_value"].widget.attrs.update({"id": "repeatValue"})


class OrderItemForm(forms.ModelForm):
    equipment_id = forms.ModelChoiceField(
        queryset=RentalProduct.objects.all(),
        widget=forms.Select(attrs={"class": "form-control disable-first-option", "onchange": "updateEquipmentName(this)"}),
        empty_label="Select Equipment ID",
        label="Equipment ID"
    )
    equipment_name = forms.ModelChoiceField(
        queryset=RentalProduct.objects.all(),
        widget=forms.Select(attrs={"class": "form-control disable-first-option", "onchange": "updateEquipmentID(this)"}),
        empty_label="Select Equipment Name",
        label="Equipment Name"
    )
    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "per_unit_price"]
        widgets = {
            "product": forms.HiddenInput(),
            "quantity": forms.NumberInput(attrs={"class": "form-control quantity", "oninput": "updateRentAmount()"}),
            "per_unit_price": forms.NumberInput(attrs={"class": "form-control price", "oninput": "updateRentAmount()"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get the first instance of OrderFormPermissionModel (assuming single row)
        permissions = OrderFormPermissionModel.objects.first()

        if permissions:
            # Loop through form fields and set required dynamically
            for field_name in self.fields:
                if hasattr(permissions, field_name):
                    self.fields[field_name].required = getattr(permissions, field_name)

        self.fields["equipment_id"].queryset = RentalProduct.objects.all()
        self.fields["equipment_name"].queryset = RentalProduct.objects.all()

        self.fields["equipment_id"].label_from_instance = lambda obj: f"{obj.equipment_id}"
        self.fields["equipment_name"].label_from_instance = lambda obj: f"{obj.equipment_name}"

        if "instance" in kwargs and kwargs["instance"]:
            product_instance = kwargs["instance"].product
            if product_instance:
                self.initial["equipment_id"] = product_instance
                self.initial["equipment_name"] = product_instance

    def clean(self):
        cleaned_data = super().clean()
        equipment_id = cleaned_data.get("equipment_id")

        if equipment_id:
            cleaned_data["product"] = equipment_id
        return cleaned_data

OrderItemFormSet = forms.inlineformset_factory(Order, OrderItem, form=OrderItemForm, extra=1)

class OrderFormPermissionForm(forms.ModelForm):
    class Meta:
        model = OrderFormPermissionModel
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.readonly_fields = {
            "customer",
            "account_manager",
            "repeat_type",
        }

        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
            
            if field_name in self.readonly_fields:
                field.widget.attrs['disabled'] = 'disabled'

    def clean(self):
        cleaned_data = super().clean()
        if self.instance:
            for field in self.readonly_fields:
                cleaned_data[field] = getattr(self.instance, field)
        return cleaned_data



class ReturnOrderEditForm(forms.ModelForm):
    rental_start_date = forms.DateField(
        label="Start Date",
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )
    rental_end_date = forms.DateField(
        label="End Date",
        widget=forms.DateInput(attrs={"type": "date"}), required=False
    )

    class Meta:
        model = ReturnOrder
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.order:
            self.fields["rental_start_date"].initial = self.instance.order.rental_start_date
            self.fields["rental_end_date"].initial = self.instance.order.rental_end_date


class UploadDocumentForm(forms.ModelForm):
    """
    Upload a documents file
    """

    class Meta:
        model = Document
        fields = ["document"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document"].required = False
