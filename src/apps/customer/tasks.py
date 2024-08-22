import os

import pandas as pd

from .models import Customer


def import_customer_from_xlsx(file):
    file_extension = os.path.splitext(file.name)[1]
    context = {"messages": []}
    skip_customers = []

    columns_list = [
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
                print("record[ID]: ", record["ID"])
                internal_id = record["Internal ID"]
                customer_id = record["ID"]
                name = record["Name"]
                sales_rep = record["Sales Rep"]
                billing_address_1 = record["Billing Address 1"]
                billing_address_2 = record.get("Billing Address 2", "")
                city = record["Billing City"]
                state = record["Billing State/Province"]
                zip_code = record["Billing Zip"]
                country = record["Billing Country"]

                customer, created = Customer.objects.update_or_create(
                    customer_id=customer_id,
                    defaults={
                        "internal_id": internal_id,
                        "name": name,
                        "sales_rep": sales_rep,
                        "billing_address_1": billing_address_1,
                        "billing_address_2": billing_address_2,
                        "city": city,
                        "state": state,
                        "zip": zip_code,
                        "country": country,
                    },
                )

                if created:
                    context["messages"].append(f"Created new customer: {name}")
                else:
                    context["messages"].append(f"Updated existing customer: {name}")

            except Exception as e:
                print("Error processing record:", e)
                skip_customers.append(record)
                continue

        if skip_customers:
            print("Skipped customers:", skip_customers)
        print(context)

    else:
        return {"error": "There is a mismatch in the columns."}
