from django import forms

from apps.rental.stock_management.models import StockAdjustment


class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        fields = ["quantity", "reason", "comment", "location", "date"]

    reason = forms.ChoiceField(choices=StockAdjustment.REASON_CHOICES)
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), required=False)

    def clean_rental_product(self):
        rental_product = self.cleaned_data.get("rental_product")
        print("rental_product: ", rental_product)
        if not rental_product:
            raise forms.ValidationError("Rental product is required.")
        return rental_product


class ImportStockAdjustmentForm(forms.Form):
    """
    Form for uploading stock adjustment data files (.xlsx, .xls, .csv).
    """

    VALID_EXTENSIONS = {".xlsx", ".xls", ".csv"}
    REQUIRED_COLUMNS = ["Internal ID", "Location", "Quantity", "Reason", "Date", "Comment"]

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
            raise forms.ValidationError("This field is required.")

        extension = csv_file.name.rsplit(".", 1)[-1].lower()
        if f".{extension}" not in self.VALID_EXTENSIONS:
            raise forms.ValidationError("Only .csv, .xlsx, and .xls files are accepted.")

        return csv_file
