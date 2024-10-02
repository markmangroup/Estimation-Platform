import os

import pandas as pd
from django.db import IntegrityError

from apps.proposal.task.models import Task


def import_task_from_file(file):
    """
    Import tasks from a CSV or Excel file, creating or updating Task records.

    :param file: Task data file (.csv, .xlsx, or .xls).
    :return: Messages about the import process or error details.
    """
    context = {"messages": []}
    skip_labour_cost = []
    file_extension = os.path.splitext(file.name)[1]

    if file.size == 0:
        return {"error": "You are trying to upload an empty file."}

    expected_columns = ["Internal ID", "Name", "Task Code Description"]

    try:
        if file_extension == ".csv":
            df = pd.read_csv(file)
        elif file_extension in [".xlsx", ".xls"]:
            df = pd.read_excel(file, sheet_name=0)
            if len(pd.ExcelFile(file).sheet_names) > 1:
                return {"error": "The file contains multiple sheets and won't be processed."}
        else:
            return {"error": "Unsupported file format."}

        if df.empty:
            return {"error": "The file is empty."}

        df = df.fillna("")  # Fill NaNs with empty strings
        task_list = df.to_dict(orient="records")

        # Validate column names
        if sorted(df.columns) != sorted(expected_columns):
            return {"error": "The columns do not match the expected format."}

        for record in task_list:
            try:
                internal_id = record.get("Internal ID")
                name = record.get("Name")
                description = record.get("Task Code Description")

                if not internal_id:
                    context["messages"].append("Missing 'Internal ID' in record.")
                    skip_labour_cost.append(record)
                    continue

                labour_cost, created = Task.objects.update_or_create(
                    internal_id=internal_id,
                    defaults={"name": name, "description": description},
                )

                action = "Created" if created else "Updated"
                context["messages"].append(f"{action} task: {internal_id}")

            except IntegrityError:
                context["messages"].append(
                    f"Failed to save task with Internal ID {internal_id} due to integrity error."
                )
                skip_labour_cost.append(record)
            except Exception as e:
                context["messages"].append(f"Error processing record {internal_id}: {e}")
                skip_labour_cost.append(record)

        if skip_labour_cost:
            context["messages"].append(f"Skipped records: {skip_labour_cost}")

    except pd.errors.EmptyDataError:
        return {"error": "The file is empty."}
    except Exception as e:
        return {"error": f"An error occurred: {e}"}

    return context
