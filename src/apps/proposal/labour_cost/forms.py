import os

from django import forms
from django.core.exceptions import ValidationError


class ImportLabourCostCSVForm(forms.Form):
    """
    A form for uploading CSV/XLSX files with labour cost data.
    Validates file type and ensures required columns are present.
    """

    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={"accept": ".xlsx, .xls, .csv"}),
        help_text=(
            ".xlsx, .xls, and .csv files must contain the following columns in the same sequence: "
            "[Labour Task, Local Labour Rates, Out Of Town Labour Rates, Description, Notes]"
        ),
    )

    valid_extensions = {".xlsx", ".xls", ".csv"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs.update({"class": "custom-file-input", "id": "inputGroupFile02"})

    def clean_csv_file(self):
        """Validate the uploaded CSV file and check its extension."""
        csv_file = self.cleaned_data.get("csv_file")
        if not csv_file:
            raise ValidationError("This field is required.")

        _, extension = os.path.splitext(csv_file.name)
        if extension.lower() not in self.valid_extensions:
            raise ValidationError("Only .xlsx, .xls, and .csv files are accepted.")

        return csv_file
