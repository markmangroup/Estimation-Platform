import os

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.constants import LOGGER

from .models import LabourCost


def import_labour_cost_from_xlsx(file: InMemoryUploadedFile) -> dict:
    """
    Imports labor cost data from an Excel or CSV file.

    :prams file (File): The uploaded file containing product data.
    :return: A context dictionary with messages about created/updated products
            or errors if the columns do not match or records are skipped.
    """

    file_extension = os.path.splitext(file.name)[1]
    context = {"messages": []}
    skip_labour_cost = []

    if file.size == 0:
        return {"error": "You are trying to upload an empty file; it won't be processed."}

    expected_columns = [
        "Labour Task",
        "Local Labour Rates",
        "Out Of Town Labour Rates",
        "Description",
        "Notes",
    ]

    try:
        if file_extension in [".csv", ".xlsx", ".xls"]:
            if file_extension == ".csv":
                df = pd.read_csv(file)
            else:
                excel_file = pd.ExcelFile(file)
                if len(excel_file.sheet_names) > 1:
                    return {"error": "The file with multiple sheets won't be processed."}
                df = pd.read_excel(excel_file, sheet_name=0)

            if df.empty:
                return {"error": "You are trying to upload an empty file; it won't be processed."}

        else:
            return {"error": "Unsupported file format."}
    except pd.errors.EmptyDataError:
        return {"error": "You are trying to upload an empty file; it won't be processed."}

    df = df.fillna("")
    records = df.to_dict(orient="records")

    if sorted(records[0].keys()) != sorted(expected_columns):
        return {"error": "There is a mismatch in the columns."}

    for record in records:
        labour_task = record.get("Labour Task")
        if not labour_task:
            context["messages"].append(f"Missing 'Labour Task' in record: {record}")
            skip_labour_cost.append(record)
            continue

        try:
            labour_cost, created = LabourCost.objects.update_or_create(
                labour_task=labour_task,
                defaults={
                    "local_labour_rates": record["Local Labour Rates"],
                    "out_of_town_labour_rates": record["Out Of Town Labour Rates"],
                    "description": record["Description"],
                    "notes": record["Notes"],
                },
            )
            action = "Created" if created else "Updated"
            context["messages"].append(f"{action} labour cost: {labour_task}")

        except Exception as e:
            LOGGER.error(f"Error processing record: {e}")
            skip_labour_cost.append(record)

    if skip_labour_cost:
        LOGGER.error(f"Skipped records:: {skip_labour_cost}")

    return context
