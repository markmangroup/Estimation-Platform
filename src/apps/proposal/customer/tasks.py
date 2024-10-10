import os

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.constants import LOGGER

from .models import Customer


def import_customer_from_xlsx(file: InMemoryUploadedFile) -> dict:
    """
    Imports customer data from an Excel or CSV file.

    :prams file (File): The uploaded file containing product data.
    :return: A context dictionary with messages about created/updated products
            or errors if the columns do not match or records are skipped.
    """

    file_extension = os.path.splitext(file.name)[1].lower()
    context = {"messages": []}
    skip_customers = []

    # Define the expected columns
    expected_columns = [
        "Internal ID",
        "ID",
        "Name",
        "Sales Rep",
        "Billing Address 1",
        "Billing Address 2",
        "Billing City",
        "Billing State/Province",
        "Billing Zip",
        "Billing Country",
    ]

    # Load the data from the file
    try:
        if file_extension == ".csv":
            df = pd.read_csv(file)
        elif file_extension in [".xlsx", ".xls"]:
            df = pd.read_excel(file, sheet_name=0)
            if len(pd.ExcelFile(file).sheet_names) > 1:
                return {"error": "The file with multiple sheets won't be processed."}
        else:
            return {"error": "Unsupported file format."}
    except pd.errors.EmptyDataError:
        return {"error": "You are trying to upload an empty file."}

    # Check for empty DataFrame and validate columns
    if df.empty:
        return {"error": "You are trying to upload an empty file."}

    df.columns = df.columns.str.strip()  # Clean up any whitespace in column names
    if set(df.columns) != set(expected_columns):
        return {"error": "The columns do not match the expected format."}

    # Convert DataFrame to a list of dictionaries
    customer_list = df.fillna("").to_dict(orient="records")

    # Process each customer record
    for record in customer_list:
        try:
            customer_id = record["ID"]
            customer_data = {
                "internal_id": record["Internal ID"],
                "name": record["Name"],
                "sales_rep": record["Sales Rep"],
                "billing_address_1": record["Billing Address 1"],
                "billing_address_2": record.get("Billing Address 2", ""),
                "city": record["Billing City"],
                "state": record["Billing State/Province"],
                "zip": record["Billing Zip"],
                "country": record["Billing Country"],
            }

            customer, created = Customer.objects.update_or_create(
                customer_id=customer_id,
                defaults=customer_data,
            )

            message = f"{'Created' if created else 'Updated'} customer: {customer_data['name']}"
            context["messages"].append(message)

        except Exception as e:
            LOGGER.error(f"Error processing record {record['ID']}: {e}")
            skip_customers.append(record)

    # Log skipped customers if any
    if skip_customers:
        LOGGER.info(f"Skipped customers: {skip_customers}")

    return context
