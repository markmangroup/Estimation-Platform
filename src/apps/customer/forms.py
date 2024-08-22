from django import forms
from django.core.exceptions import ValidationError


class ImportCustomerCSVForm(forms.Form):
    csv_file = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "accept": ".xlsx, .xls .csv",
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super(ImportCustomerCSVForm, self).__init__(*args, **kwargs)
        self.fields["csv_file"].help_text = (
            """.CSV file must contain following columns with same sequence:
            ["Internal Id", "Id", "Name", "Sales Rep", "Billing Address 1","Billing Address 2",
            "Billing City","Billing State Province","Billing Zip","Billing Country"]
            """
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
            raise ValidationError("Only .csv .xlsx and .xls files are accepted.")

        return csv_file
