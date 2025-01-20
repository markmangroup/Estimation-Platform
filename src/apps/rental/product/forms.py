from django import forms
from django.core.exceptions import ValidationError


class ImportProductForm(forms.Form):
    """
    Form for uploading product data files (.xlsx, .xls, .csv).
    """

    VALID_EXTENSIONS = {".xlsx", ".xls", ".csv"}
    REQUIRED_COLUMNS = [
        "Equipment ID",
        "Equipment Material Group",
        "Equipment Name",
        "SubType",
    ]

    csv_file = forms.FileField(widget=forms.FileInput(attrs={"accept": ", ".join(VALID_EXTENSIONS)}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["csv_file"].help_text = (
            f"{', '.join(self.VALID_EXTENSIONS)} files must contain the following columns in the same sequence: "
            f"{', '.join(self.REQUIRED_COLUMNS)}."
        )
        for visible in self.visible_fields():
            visible.field.widget.attrs.update({"class": "custom-file-input", "id": "inputGroupFile01"})

    def clean_csv_file(self):
        """Validates the uploaded file format."""
        csv_file = self.cleaned_data.get("csv_file")
        if not csv_file:
            raise ValidationError("This field is required.")

        extension = csv_file.name.rsplit(".", 1)[-1].lower()
        if f".{extension}" not in self.VALID_EXTENSIONS:
            raise ValidationError("Only .csv, .xlsx, and .xls files are accepted.")

        return csv_file
