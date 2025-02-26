import os

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.constants import LOGGER
from apps.rental.account_manager.models import AccountManager


def import_account_manager_from_xlsx(file: InMemoryUploadedFile) -> dict:
    """
    Imports account manager data from an Excel or CSV file.

    :prams file (File): The uploaded file containing product data.
    """
    file_extension = os.path.splitext(file.name)[1].lower()
    context = {"messages": []}
    skip_account_manager = []

    # Define the expected columns
    expected_columns = ["Manager id","Account Manager Name", "Email"]

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
    account_manager_list = df.fillna("").to_dict(orient="records")

    # Process each customer record
    for record in account_manager_list:
        try:

            manager_id = record["Manager id"]
            name = record["Account Manager Name"]
            email = record["Email"]

            if email:
                account_manager, created = AccountManager.objects.update_or_create(
                    manager_id=manager_id,
                    email=email,
                    defaults={"name": name},
                )

                message = f"{'Created' if created else 'Updated'} Account Manager: {name}"
                context["messages"].append(message)
            else:
                message = f"Email Not Found"
                context["messages"].append(message)

        except Exception as e:
            LOGGER.error(f"Error processing record {record['ID']}: {e}")
            skip_account_manager.append(record)

    # Log skipped customers if any
    if skip_account_manager:
        LOGGER.info(f"Skipped Account Manager: {skip_account_manager}")

    return context
