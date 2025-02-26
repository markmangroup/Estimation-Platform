from django import forms
from django.core.exceptions import ValidationError


class ImportCustomerCSVForm(forms.Form):
    """Form for uploading customer data from CSV, XLSX, or XLS files."""

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
        "Internal Id",
        "Customer Id",
        "Customer Name",
        "Sales Rep",
        "Billing Address 1",
        "Billing Address 2",
        "Billing City",
        "Billing State Province",
        "Billing Zip",
        "Billing Country",
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
