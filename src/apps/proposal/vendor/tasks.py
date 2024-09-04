import os

import pandas as pd

from apps.proposal.vendor.models import Vendor


def import_vendor_from_file(file):
    """
    Imports vendor data from an uploaded Excel or CSV file.

    Args:
        file (UploadedFile): The uploaded .csv, .xlsx, or .xls file.

    Returns:
        dict: Contains 'messages' if successful or 'error' if the file format is incorrect.

    The function:
        - Reads and validates the file.
        - Ensures required columns ("Internal ID", "Name") are present.
        - Creates or updates Vendor records in the database.
        - Skips records with missing data or errors.
    """

    file_extension = os.path.splitext(file.name)[1]
    context = {"messages": []}
    skip_vendor = []

    if file.size == 0:
        return {"error": "You are trying to upload an empty file therefore it won't be processed."}

    columns_list = ["Internal ID", "Name"]

    try:
        if file_extension == ".csv":
            df = pd.read_csv(file)
        elif file_extension == ".xlsx" or file_extension == ".xls":
            excel_file = pd.ExcelFile(file)
            if len(excel_file.sheet_names) > 1:
                return {"error": "The file with multiple sheets won't be processed"}

            df = pd.read_excel(excel_file, sheet_name=0)
        else:
            return {"error": "Unsupported file format."}
    except ImportError as e:
        return {"error": f"Failed to process the file: {e}. Please ensure all dependencies are installed."}
    except pd.errors.EmptyDataError:
        return {"error": "You are trying to upload an empty file therefore it won't be processed."}

    if df.empty:
        return {"error": "You are trying to upload an empty file therefore it won't be processed."}

    df = df.fillna("")
    vendor_list = df.to_dict(orient="records")
    # print("vendor_list", vendor_list)
    keys = vendor_list[0].keys()

    keys_list = sorted(keys)
    columns_list_sorted = sorted(columns_list)

    if keys_list == columns_list_sorted:
        for record in vendor_list:
            print("record: ", record)
            try:
                internal_id = record["Internal ID"]
                name = record["Name"]

                if not internal_id:
                    context["messages"].append(f"Missing 'Vendor' in record: {record}")
                    skip_vendor.append(record)
                    continue

                vendor, created = Vendor.objects.update_or_create(
                    internal_id=internal_id,
                    defaults={
                        "name": name,
                    },
                )

                if created:
                    context["messages"].append(f"Created new Vendor: {name}")
                else:
                    context["messages"].append(f"Updated existing Vendor: {name}")

            except Exception as e:
                print("Error processing record:", e)
                skip_vendor.append(record)
                continue

            if skip_vendor:
                print("Skipped records:", skip_vendor)
        # print(context)
        return context

    else:
        return {"error": "The columns do not match."}
