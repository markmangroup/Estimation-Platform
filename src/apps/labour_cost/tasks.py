import os

import pandas as pd

from .models import LabourCost


def import_labour_cost_from_xlsx(file):
    file_extension = os.path.splitext(file.name)[1]
    context = {"messages": []}
    skip_labour_cost = []

    columns_list = [
        "Labour Task",
        "Local Labour Rates",
        "Out Of Town Labour Rates",
        "Description",
        "Notes",
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
                labour_task = record["Labour Task"]
                local_labour_rates = record["Local Labour Rates"]
                out_of_town_labour_rates = record["Out Of Town Labour Rates"]
                description = record["Description"]
                notes = record["Notes"]

                # Check if all required fields are present
                if not labour_task:
                    context["messages"].append(f"Missing 'Labour Task' in record: {record}")
                    skip_labour_cost.append(record)
                    continue

                labour_cost, created = LabourCost.objects.update_or_create(
                    labour_task=labour_task,
                    defaults={
                        "local_labour_rates": local_labour_rates,
                        "out_of_town_labour_rates": out_of_town_labour_rates,
                        "description": description,
                        "notes": notes,
                    },
                )

                if created:
                    context["messages"].append(f"Created new labour cost: {labour_task}")
                else:
                    context["messages"].append(f"Updated existing labour cost: {labour_task}")

            except Exception as e:
                print("Error processing record:", e)
                skip_labour_cost.append(record)
                continue

            if skip_labour_cost:
                print("Skipped records:", skip_labour_cost)
        print(context)
        return context

    else:
        return {"error": "There is a mismatch in the columns."}
