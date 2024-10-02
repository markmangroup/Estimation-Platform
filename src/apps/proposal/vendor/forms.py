import os

from django import forms
from django.core.exceptions import ValidationError


class ImportVendorForm(forms.Form):
    """
    Form for uploading and validating a vendor CSV/Excel file.
    """

    csv_file = forms.FileField(widget=forms.FileInput(attrs={"accept": ".xlsx, .xls, .csv"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["csv_file"].help_text = (
            "The file must contain the following columns in this order: " '["Internal Id", "Name"]'
        )
        # Set custom attributes for visible fields
        for field in self.visible_fields():
            field.field.widget.attrs.update({"class": "custom-file-input", "id": "inputGroupFile01"})

    def clean_csv_file(self):
        """Validates the uploaded CSV file."""
        csv_file = self.cleaned_data.get("csv_file")
        if not csv_file:
            raise ValidationError("This field is required.")

        valid_extensions = {".xlsx", ".xls", ".csv"}
        extension = os.path.splitext(csv_file.name)[-1].lower()

        if extension not in valid_extensions:
            raise ValidationError("Only .csv, .xlsx, and .xls files are accepted.")

        return csv_file
