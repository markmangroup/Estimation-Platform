import os

import pandas as pd

from apps.proposal.task.models import Task


def import_task_from_file(file):
    """
    Imports tasks from a CSV or Excel file, updating or creating Task records.

    Args:
        file (File): The file containing task data, in .csv, .xlsx, or .xls format.

    Returns:
        dict: A context dictionary containing messages about the import process or an error message if the file columns don't match the expected format.
    """
    file_extension = os.path.splitext(file.name)[1]
    context = {"messages": []}
    skip_labour_cost = []

    if file.size == 0:
        return {"error": "You are trying to upload an empty file therefore it won't be processed."}

    columns_list = ["Internal ID", "Name", "Task Code Description"]

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
    task_list = df.to_dict(orient="records")
    keys = task_list[0].keys()

    keys_list = sorted(keys)
    columns_list_sorted = sorted(columns_list)

    if keys_list == columns_list_sorted:

        for record in task_list:
            try:
                internal_id = record["Internal ID"]
                name = record["Name"]
                description = record["Task Code Description"]

                # Check if all required fields are present
                if not internal_id:
                    context["messages"].append(f"Missing 'Task' in record: {internal_id}")
                    skip_labour_cost.append(record)
                    continue

                labour_cost, created = Task.objects.update_or_create(
                    internal_id=internal_id,
                    defaults={"name": name, "description": description},
                )

                if created:
                    context["messages"].append(f"Created new task: {internal_id}")
                else:
                    context["messages"].append(f"Updated existing task: {internal_id}")

            except Exception as e:
                print("Error processing record:", e)
                skip_labour_cost.append(record)
                continue

            if skip_labour_cost:
                print("Skipped records:", skip_labour_cost)
        print(context)
        return context

    else:
        return {"error": "The columns do not match."}
