import os

import pandas as pd
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.proposal.vendor.models import Vendor


def import_vendor_from_file(file: InMemoryUploadedFile) -> dict:
    """
    Import vendor data from an uploaded CSV or Excel file.

    :param file: The uploaded .csv, .xlsx, or .xls file.
    :return: A dict containing 'messages' if successful or 'error' if there's an issue.
    """
    context = {"messages": []}
    skip_vendor = []

    # Validate file size
    if file.size == 0:
        return {"error": "You are trying to upload an empty file; it won't be processed."}

    # Required columns
    required_columns = ["Internal ID", "Name"]

    # Determine file extension and read the file
    file_extension = os.path.splitext(file.name)[1].lower()
    try:
        if file_extension == ".csv":
            df = pd.read_csv(file)
        elif file_extension in {".xlsx", ".xls"}:
            excel_file = pd.ExcelFile(file)
            if len(excel_file.sheet_names) > 1:
                return {"error": "The file with multiple sheets won't be processed."}
            df = pd.read_excel(excel_file, sheet_name=0)
        else:
            return {"error": "Unsupported file format."}
    except (ImportError, pd.errors.EmptyDataError, ValidationError) as e:
        return {"error": f"Failed to process the file: {str(e)}."}

    # Check if DataFrame is empty
    if df.empty:
        return {"error": "You are trying to upload an empty file; it won't be processed."}

    df.fillna("", inplace=True)
    vendor_list = df.to_dict(orient="records")

    # Check for required columns
    actual_columns = sorted(vendor_list[0].keys())
    if sorted(required_columns) != actual_columns:
        return {"error": "The columns do not match the required format."}

    for record in vendor_list:
        try:
            internal_id = record["Internal ID"]
            name = record["Name"]

            if not internal_id:
                context["messages"].append(f"Missing 'Internal ID' in record: {record}")
                skip_vendor.append(record)
                continue

            vendor, created = Vendor.objects.update_or_create(
                internal_id=internal_id,
                defaults={"name": name},
            )

            if created:
                context["messages"].append(f"Created new Vendor: {name}")
            else:
                context["messages"].append(f"Updated existing Vendor: {name}")

        except Exception as e:
            context["messages"].append(f"Error processing record: {record}. Error: {str(e)}")
            skip_vendor.append(record)

    if skip_vendor:
        context["messages"].append(f"Skipped records: {len(skip_vendor)} due to errors.")

    return context
