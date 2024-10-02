from django import forms
from django.core.exceptions import ValidationError


class ImportTaskForm(forms.Form):
    """
    Form for importing task data from Excel or CSV files.
    """

    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={"accept": ".xlsx, .xls, .csv"}),
        help_text=(
            ".xlsx, .xls, and .csv files must contain the following columns in this sequence: "
            '["Internal Id", "Name", "Task Code Description"]'
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._set_widget_attributes()

    def _set_widget_attributes(self):
        """Set custom widget attributes for visible fields."""
        for visible in self.visible_fields():
            visible.field.widget.attrs.update({"class": "custom-file-input", "id": "inputGroupFile01"})

    def clean_csv_file(self):
        """
        Validate the uploaded CSV file.

        :raises ValidationError: If the file is missing or has an invalid extension.
        """
        csv_file = self.cleaned_data.get("csv_file")

        if not csv_file:
            raise ValidationError("This field is required.")

        valid_extensions = {".xlsx", ".xls", ".csv"}
        extension = csv_file.name.rsplit(".", 1)[-1].lower()

        if f".{extension}" not in valid_extensions:
            raise ValidationError("Only .csv, .xlsx, and .xls files are accepted.")

        return csv_file
