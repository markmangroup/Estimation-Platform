import os
from datetime import datetime

import pandas as pd

from .models import Opportunity


def import_opportunity_from_xlsx(file):
    file_extension = os.path.splitext(file.name)[1]
    context = {"messages": []}
    skip_opportunity = []

    if file.size == 0:
        return {"error": "You are trying to upload an empty file therefore it won't be processed."}
    columns_list = [
        "Internal Id",
        "Sales Rep",
        "Customer",
        "Location",
        "Class",
        "Document Number",
        "Title",
        "Ranch Address",
        "Opportunity Status",
        "Projected Total",
        "Expected Margin",
        "Margin Amount",
        "Win Probability",
        "Expected Close",
        "Opportunity Notes",
        "Scope",
        "Designer",
        "Estimator",
        "Pump & Electrical Designer",
        "Design/Estimation Note",
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
        return {"error": "You are trying to upload an empty file therefore it won't be processed."}

    df = df.fillna("")
    opportunity_list = df.to_dict(orient="records")
    print(f"opportunity_list {len(opportunity_list)}:")
    keys = opportunity_list[0].keys()

    keys_list = sorted(keys)
    columns_list_sorted = sorted(columns_list)

    if keys_list == columns_list_sorted:
        for record in opportunity_list:
            try:
                internal_id = record["Internal Id"]
                sales_rep = record["Sales Rep"]
                record["Customer"]
                location = record["Location"]
                opportunity_class = record["Class"]
                document_number = record["Document Number"]
                title = record["Title"]
                ranch_address = record["Ranch Address"]
                opportunity_status = record["Opportunity Status"]
                projected_total = record["Projected Total"]
                expected_margin = record["Expected Margin"]
                margin_amount = record["Margin Amount"]
                win_probability = record["Win Probability"]
                expected_close = record.get("Expected Close")
                if isinstance(expected_close, str):
                    try:
                        expected_close = datetime.strptime(expected_close, "%Y-%m-%d").strftime("%Y-%m-%d")
                    except ValueError:
                        expected_close = ""
                opportunity_notes = record["Opportunity Notes"]
                scope = record["Scope"]
                designer = record["Designer"]
                estimator = record["Estimator"]
                pump_electrical_designer = record["Pump & Electrical Designer"]
                design_estimation_note = record["Design/Estimation Note"]

                # Check if all required fields are present
                if not internal_id:
                    context["messages"].append(f"Missing 'Labour Task' in record: {record}")
                    skip_opportunity.append(record)
                    continue

                opportunity, created = Opportunity.objects.update_or_create(
                    document_number=document_number,
                    defaults={
                        "internal_id": internal_id,
                        "sales_rep": sales_rep,
                        "location": location,
                        "opportunity_class": opportunity_class,
                        "title": title,
                        "ranch_address": ranch_address,
                        "opportunity_status": opportunity_status,
                        "projected_total": projected_total,
                        "expected_margin": expected_margin,
                        "margin_amount": margin_amount,
                        "win_probability": win_probability,
                        "expected_close": expected_close,
                        "opportunity_notes": opportunity_notes,
                        "scope": scope,
                        "designer": designer,
                        "estimator": estimator,
                        "pump_electrical_designer": pump_electrical_designer,
                        "design_estimation_note": design_estimation_note,
                    },
                )

                if created:
                    print(f"Created new Opportunity: {document_number}")
                    context["messages"].append(f"Created new Opportunity: {document_number}")
                else:
                    print(f"Updated existing Opportunity: {document_number}")
                    context["messages"].append(f"Updated existing Opportunity: {document_number}")

            except Exception as e:
                print("Error processing record:", e)
                skip_opportunity.append(record)
                return {"error": e}

            if skip_opportunity:
                print("Skipped records:", skip_opportunity)
        print(context)
        return context

    else:
        return {"error": "There is a mismatch in the columns."}
