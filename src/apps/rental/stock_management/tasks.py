import os

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.rental.product.models import RentalProduct
from apps.rental.stock_management.models import StockAdjustment


def import_stock_adjustment_from_file(file: InMemoryUploadedFile) -> dict:
    """
    Imports stock adjustment data from an uploaded Excel or CSV file.

    :param file (File): The uploaded file containing stock adjustment data.
    :return: A context dictionary with messages about created/updated stock adjustments
            or errors if the columns do not match or records are skipped.
    """
    # Define the expected columns for stock adjustment
    expected_columns = {"Internal ID", "Location", "Quantity", "Reason", "Date", "Comment"}

    # Check for empty file
    if file.size == 0:
        return {"error": "You are trying to upload an empty file."}

    # Determine file type and load data
    try:
        file_extension = os.path.splitext(file.name)[1]
        if file_extension == ".csv":
            df = pd.read_csv(file)
        elif file_extension in {".xlsx", ".xls"}:
            excel_file = pd.ExcelFile(file)
            if len(excel_file.sheet_names) > 1:
                return {"error": "The file with multiple sheets won't be processed"}
            df = pd.read_excel(excel_file, sheet_name=0)
        else:
            return {"error": "Unsupported file format."}
    except (ImportError, pd.errors.EmptyDataError) as e:
        return {"error": f"Failed to process the file: {str(e)}."}

    # Check if DataFrame is empty or columns don't match
    print("expected_columns: ", expected_columns)
    print("df.columns: ", df.columns)
    df.columns = df.columns.str.strip()  # Strip whitespace from column names
    df.columns = df.columns.str.replace("\n", "")  # Remove newline characters if any

    if df.empty or set(df.columns) != expected_columns:
        return {"error": "The columns do not match or the file is empty."}

    df = df.fillna("")  # Fill NaN values with empty strings
    records = df.to_dict(orient="records")
    print("records: ", records)
    context = {"messages": []}
    skipped_records = []
    context["records"] = records

    # Validate and process each record
    for record in records:
        equipment_id = record.get("Internal ID")
        try:
            equipment_id = int(equipment_id)  # Validate if Equipment ID is an integer
        except ValueError:
            skipped_records.append(record)
            context["messages"].append(f"Invalid 'Internal ID' in record: {record}. Must be an integer.")
            continue

        # Try to get the rental product
        try:
            rental_product = RentalProduct.objects.get(equipment_id=equipment_id)
        except RentalProduct.DoesNotExist:
            skipped_records.append(record)
            context["messages"].append(f"Rental Product with Equipment ID {equipment_id} not found.")
            continue

        # Prepare data for stock adjustment
        stock_adjustment_data = {
            "rental_product": rental_product,
            "quantity": record["Quantity"],
            "reason": record["Reason"],
            "comment": record.get("Comment", ""),
            "location": record.get("Location", ""),
            "date": record["Date"],
        }
    context["skipped_records"] = skipped_records
    return context
