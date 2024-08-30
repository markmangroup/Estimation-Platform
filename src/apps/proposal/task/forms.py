from django import forms
from django.core.exceptions import ValidationError


class ImportTaskForm(forms.Form):
    """
    Form for importing task data from an Excel file.

    Fields:
        csv_file (FileField): A file input field that accepts .xlsx and .xls files.

    Methods:
        clean_csv_file(): Validates the uploaded file, ensuring it has the correct format.
    """

    csv_file = forms.FileField(widget=forms.FileInput(attrs={"accept": ".xlsx, .xls, .csv"}))

    def __init__(self, *args, **kwargs):
        super(ImportTaskForm, self).__init__(*args, **kwargs)
        self.fields["csv_file"].help_text = (
            '.xlsx ,.xls and .csv file must contain following columns with same sequence: ["Internal Id", "Name", "Task Code Description"]'
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
