from django import forms
from django.core.exceptions import ValidationError


class ImportAccountManagerCSVForm(forms.Form):
    """Form for uploading account manager data from CSV, XLSX, or XLS files."""

    csv_file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "accept": ".xlsx, .xls, .csv",
                "class": "custom-file-input",
                "id": "inputGroupFile01",
            }
        )
    )

    REQUIRED_COLUMNS = ["Name", "Email"]

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
