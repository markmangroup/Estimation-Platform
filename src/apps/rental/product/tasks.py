import os

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.constants import LOGGER
from apps.rental.product.models import RentalProduct


def import_product_from_file(file: InMemoryUploadedFile) -> dict:
    """
    Imports product data from an uploaded Excel or CSV file.

    :prams file (File): The uploaded file containing product data.
    :return: A context dictionary with messages about created/updated products
            or errors if the columns do not match or records are skipped.
    """
    # Define the expected columns
    expected_columns = {
        "Equipment ID",
        "Equipment Material Group",
        "Equipment Name",
        "SubType",
    }

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
    if df.empty or set(df.columns) != expected_columns:
        print("df: ", df)
        return {"error": "The columns do not match or the file is empty."}

    df = df.fillna("")
    records = df.to_dict(orient="records")
    context = {"messages": []}
    skipped_records = []

    # Validate 'Internal ID' and process records
    count = 0
    for record in records:
        count += 1
        equipment_id = record.get("Equipment ID")

        try:
            equipment_id = int(equipment_id)
        except ValueError:
            skipped_records.append(record)
            context["messages"].append(f"Invalid 'Equipment ID' in record: {record}. Must be an integer.")
            continue

        # Prepare data for updating or creating the product
        product_data = {
            "equipment_material_group": record["Equipment Material Group"],
            "equipment_name": record["Equipment Name"],
            "subtype": record["SubType"],
        }

        try:
            product, created = RentalProduct.objects.update_or_create(
                equipment_id=equipment_id,
                defaults=product_data,
            )
            action = "Created" if created else "Updated"
            context["messages"].append(f"{action} product with Equipment ID: {equipment_id}")
        except Exception as e:
            LOGGER.info(f"Error processing record: {record}. Error: {str(e)}")
            skipped_records.append(record)
            context["messages"].append(f"Error processing record: {record}. Error: {str(e)}")

    if skipped_records:
        LOGGER.info(f"Skipped Records: {skipped_records}")

    return context
