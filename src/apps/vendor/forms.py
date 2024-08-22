from django import forms
from django.core.exceptions import ValidationError


class ImportVendorForm(forms.Form):
    """
    Form for uploading and validating a vendor CSV/Excel file.

    Fields:
        csv_file (FileField): Accepts .xlsx or .xls files for import.

    Methods:
        __init__(self, *args, **kwargs): Initializes form fields with custom attributes.
        clean_csv_file(self): Validates that the uploaded file is present and in an accepted format.
    """

    csv_file = forms.FileField(widget=forms.FileInput(attrs={"accept": ".xlsx, .xls, .csv"}))

    def __init__(self, *args, **kwargs):
        super(ImportVendorForm, self).__init__(*args, **kwargs)
        self.fields["csv_file"].help_text = (
            '.CSV file must contain following columns with same sequence: ["Internal Id", "Name"]'
        )
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "custom-file-input"
            visible.field.widget.attrs["id"] = "inputGroupFile01"

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get("csv_file", None)
        if not csv_file:
            raise ValidationError("This field is required.")
        valid_extensions = [".xlsx", ".xls", ".csv"]
        extension = csv_file.name.split(".")[-1].lower()
        if f".{extension}" not in valid_extensions:
            raise ValidationError("Only .csv, .xlsx and .xls files are accepted.")

        return csv_file
