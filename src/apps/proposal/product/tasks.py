import os

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.constants import LOGGER
from apps.proposal.product.models import AdditionalMaterials, Product


def import_product_from_file(file: InMemoryUploadedFile) -> dict:
    """
    Imports product data from an uploaded Excel or CSV file.

    :prams file (File): The uploaded file containing product data.
    :return: A context dictionary with messages about created/updated products
            or errors if the columns do not match or records are skipped.
    """
    # Define the expected columns
    expected_columns = {
        "Internal ID",
        "Family",
        "Parent",
        "Description",
        "Primary Units Type",
        "Primary Stock Unit",
        "Std Cost",
        "Preferred Vendor",
        "Formula",
        "Type",
        "Name",
        "Display Name",
        "Tax Schedule",
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
        return {"error": "The columns do not match or the file is empty."}

    df = df.fillna("")
    records = df.to_dict(orient="records")
    context = {"messages": []}
    skipped_records = []

    # Validate 'Internal ID' and process records
    for record in records:
        internal_id = record.get("Internal ID")
        if not isinstance(internal_id, (int, str)):
            skipped_records.append(record)
            context["messages"].append(f"Invalid 'Internal ID' in record: {record}. Must be an integer.")
            continue

        try:
            internal_id = int(internal_id)
        except ValueError:
            skipped_records.append(record)
            context["messages"].append(f"Invalid 'Internal ID' in record: {record}. Must be an integer.")
            continue

        # Prepare data for updating or creating the product
        product_data = {
            "family": record["Family"],
            "parent": record["Parent"],
            "description": record["Description"],
            "primary_units_type": record["Primary Units Type"],
            "primary_stock_unit": record["Primary Stock Unit"],
            "std_cost": record["Std Cost"],
            "preferred_vendor": record["Preferred Vendor"],
            "type": record["Type"],
            "name": record["Name"],
            "display_name": record["Display Name"],
            "tax_schedule": record["Tax Schedule"],
            "formula": record["Formula"],
        }

        try:
            product, created = Product.objects.update_or_create(
                internal_id=internal_id,
                defaults=product_data,
            )
            action = "Created" if created else "Updated"
            context["messages"].append(f"{action} product with Internal ID: {internal_id}")
        except Exception as e:
            skipped_records.append(record)
            context["messages"].append(f"Error processing record: {record}. Error: {str(e)}")

    if skipped_records:
        LOGGER.info(f"Skipped Records: {skipped_records}")

    return context


def import_additional_material_from_file(file: InMemoryUploadedFile) -> dict:
    """
    Imports additional material data from an uploaded Excel or CSV file.

    :prams file (File): The uploaded file containing product data.
    :return: A context dictionary with messages about created/updated products
            or errors if the columns do not match or records are skipped.
    """
    # Define the expected columns
    expected_columns = {
        "Material ID",
        "Material Name",
        "Material Type",
        "Product Item Number",
        "Material Factor",
        "Additional Material Factor",
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
        return {"error": "The columns do not match or the file is empty."}

    df = df.fillna("")
    records = df.to_dict(orient="records")
    context = {"messages": []}
    skipped_material = []

    # Validate 'Internal ID' and process records
    for record in records:
        material_id = record["Material ID"]

        # Prepare data for updating or creating the product
        material_data = {
            "material_name": record["Material Name"],
            "material_type": record["Material Type"],
            "product_item_number": record["Product Item Number"],
            "material_factor": record["Material Factor"],
            "additional_material_factor": record["Additional Material Factor"],
        }

        try:
            if material_id:
                print("-=-=-====-==---")
                material, created = AdditionalMaterials.objects.update_or_create(
                    material_id=material_id,
                    defaults=material_data,
                )
                print("-=-=-====-==--- 2")
                action = "Created" if created else "Updated"
                context["messages"].append(f"{action} Material with Internal ID: {material_id}")
        except Exception as e:
            print("-=-=-=-=-=-=-=-=")
            skipped_material.append(record)
            context["messages"].append(f"Error processing record: {record}. Error: {str(e)}")

    if skipped_material:
        LOGGER.info(f"Skipped Records: {skipped_material}")

    return context
