from django import forms
from django.core.exceptions import ValidationError

from apps.proposal.opportunity.models import Document


class ImportOpportunityCSVForm(forms.Form):
    csv_file = forms.FileField(widget=forms.FileInput(attrs={"accept": ".xlsx, .xls, .csv"}))

    def __init__(self, *args, **kwargs):
        super(ImportOpportunityCSVForm, self).__init__(*args, **kwargs)
        self.fields["csv_file"].help_text = (
            """.xlsx ,.xls and .csv file must contain following columns with same sequence:
            ["Internal Id","Sales Rep","Customer","Location","Class","Document Number",
            "Title","Ranch Address","Opportunity Status","Projected Total","Expected Margin",
            "Margin Amount","Win Probability","Expected Close","Opportunity Notes","Scope","Designer",
            "Estimator","Pump & Electrical Designer","Design/Estimation Note"]
            """
        )
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "custom-file-input"
            visible.field.widget.attrs["id"] = "inputGroupFile02"

    def clean_csv_file(self):
        csv_file = self.cleaned_data.get("csv_file", None)
        if not csv_file:
            raise ValidationError("This field is required.")
        valid_extensions = [".xlsx", ".xls", ".csv"]
        extension = csv_file.name.split(".")[-1].lower()
        if f".{extension}" not in valid_extensions:
            raise ValidationError("Only .xlsx ,.xls and .csv files are accepted.")

        return csv_file


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


# NOTE: This form class form old feature of `Add Task` feature
# class AddTaskForm(forms.ModelForm):
#     """
#     Add Task from for manually adding tasks.
#     """

#     class Meta:
#         model = TaskMapping
#         fields = [
#             "code",
#             "description",
#         ]
