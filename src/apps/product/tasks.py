import os

import pandas as pd

from apps.product.models import Product


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

    if file_extension == ".csv":
        df = pd.read_csv(file)
    elif file_extension == ".xlsx" or file_extension == ".xls":
        df = pd.read_excel(file)

    df = df.fillna("")
    customer_list = df.to_dict(orient="records")
    keys = customer_list[0].keys()

    keys_list = sorted(keys)
    columns_list_sorted = sorted(columns_list)

    if keys_list == columns_list_sorted:

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
