import os

import pandas as pd

from apps.proposal.product.models import Product


def import_product_from_file(file):
    """
    Imports and updates product data from an uploaded Excel or CSV file.

    Args:
        file (File): The uploaded file containing product data.

    Returns:
        dict: A context dictionary with messages indicating created/updated products
            or errors if the columns do not match or records are skipped.

    Raises:
        ValidationError: If the uploaded file is missing required columns.
    """
    file_extension = os.path.splitext(file.name)[1]
    context = {"messages": []}
    skip_product = []

    if file.size == 0:
        return {"error": "You are trying to upload an empty file therefore it won't be processed."}

    columns_list = [
        "Internal ID",
        "Family",
        "Parent",
        "Description",
        "Primary Units Type",
        "Primary Stock Unit",
        "Std Cost",
        "Preferred Vendor",
    ]

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
        if set(df.columns) != set(columns_list):
            return {"error": "The columns do not match."}
        return {"error": "You are trying to upload an empty file therefore it won't be processed."}

    df = df.fillna("")
    customer_list = df.to_dict(orient="records")
    keys = customer_list[0].keys()

    keys_list = sorted(keys)
    columns_list_sorted = sorted(columns_list)

    if keys_list == columns_list_sorted:
        # Check if all values in 'Internal ID' are integers
        for record in customer_list:
            internal_id = record["Internal ID"]
            try:
                # Try converting 'Internal ID' to an integer
                int(internal_id)
            except ValueError:
                return {"error": "All 'Internal ID' values must be integers. Please correct the file and upload again."}

        # Convert 'Internal ID' to integers and process records
        for record in customer_list:
            try:
                record["Internal ID"] = int(record["Internal ID"])
            except ValueError:
                context["messages"].append(f"Invalid 'Internal ID' in record: {record}. Must be an integer.")
                skip_product.append(record)
                continue

        for record in customer_list:
            try:
                internal_id = record["Internal ID"]
                family = record["Family"]
                parent = record["Parent"]
                description = record["Description"]
                primary_units_type = record["Primary Units Type"]
                primary_stock_unit = record["Primary Stock Unit"]
                std_cost = record["Std Cost"]
                preferred_vendor = record["Preferred Vendor"]
                # Check if all required fields are present
                if not internal_id:
                    context["messages"].append(f"Missing 'Product' in record: {record}")
                    skip_product.append(record)
                    continue

                product, created = Product.objects.update_or_create(
                    internal_id=internal_id,
                    defaults={
                        "family": family,
                        "parent": parent,
                        "description": description,
                        "primary_units_type": primary_units_type,
                        "primary_stock_unit": primary_stock_unit,
                        "std_cost": std_cost,
                        "preferred_vendor": preferred_vendor,
                    },
                )

                if created:
                    context["messages"].append(f"Created new labour cost: {internal_id}")
                else:
                    context["messages"].append(f"Updated existing labour cost: {internal_id}")

            except Exception as e:
                print("Error processing record:", e)
                skip_product.append(record)
                continue

            if skip_product:
                print("Skipped records:", skip_product)
        print(context)
        return context

    else:
        return {"error": "The columns do not match."}
