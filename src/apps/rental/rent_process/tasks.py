import os
from datetime import datetime

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.constants import LOGGER
from apps.rental.account_manager.models import AccountManager
from apps.rental.customer.models import RentalCustomer
from apps.rental.rent_process.models import Delivery, Order


def convert_date(date_str):
    date_str = str(date_str).strip()
    if date_str in ["", "-", "N/A", "None"]:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def import_order_from_file(file: InMemoryUploadedFile) -> dict:
    """
    Imports product data from an uploaded Excel or CSV file.

    :param file: The uploaded file containing product data.
    :return: A context dictionary with messages about created/updated products
            or errors if the columns do not match or records are skipped.
    """
    expected_columns = {
        "Order ID",
        "Customer",
        "Order Amount",
        "Account Manager",
        "Start Date",
        "End Date",
        "Reccurence Type",
    }

    if file.size == 0:
        return {"error": "You are trying to upload an empty file."}

    try:
        file_extension = os.path.splitext(file.name)[1]
        if file_extension == ".csv":
            df = pd.read_csv(file)
        elif file_extension in {".xlsx", ".xls"}:
            excel_file = pd.ExcelFile(file)
            if len(excel_file.sheet_names) > 1:
                return {"error": "The file with multiple sheets won't be processed"}
            df = pd.read_excel(excel_file, sheet_name=0)
        else:
            return {"error": "Unsupported file format."}
    except (ImportError, pd.errors.EmptyDataError) as e:
        return {"error": f"Failed to process the file: {str(e)}."}
    if df.empty or set(df.columns) != expected_columns:
        return {"error": "The columns do not match or the file is empty."}

    df = df.fillna("")
    records = df.to_dict(orient="records")
    context = {"messages": []}
    skipped_records = []

    for record in records:
        order_id = record.get("Order ID")
        if not isinstance(order_id, (int, str)):
            skipped_records.append(record)
            context["messages"].append(f"Invalid 'Order ID' in record: {record}. Must be an integer.")
            continue

        try:
            order_id = int(order_id)
        except ValueError:
            skipped_records.append(record)
            context["messages"].append(f"Invalid 'Order ID' in record: {record}. Must be an integer.")
            continue

        rent_amount = record["Order Amount"].replace("$", "").replace(",", "").strip()
        try:
            rent_amount = float(rent_amount)
        except ValueError:
            skipped_records.append(record)
            context["messages"].append(f"Invalid 'Order Amount' in record: {record}. Must be a valid decimal number.")
            continue

        customer = RentalCustomer.objects.filter(customer_id=record["Customer"]).first()
        account_manager = AccountManager.objects.filter(email=record["Account Manager"]).first()

        if not customer or not account_manager:
            skipped_records.append(record)
            missing_entity = "Customer" if not customer else "Account Manager"
            context["messages"].append(f"{missing_entity} not found for Order ID: {order_id}. Skipping record.")
            continue

        order_data = {
            "order_id": order_id,
            "customer": customer,
            "account_manager": account_manager,
            "rent_amount": rent_amount,
            "repeat_start_date": convert_date(record["Start Date"]),
            "repeat_end_date": convert_date(record["End Date"]),
            "repeat_type": record["Reccurence Type"],
        }
        print(f"Processing Order Data: {order_data}")

        try:
            order, created = Order.objects.update_or_create(
                order_id=order_id,
                defaults=order_data,
            )
            action = "Created" if created else "Updated"
            context["messages"].append(f"{action} product with Order ID: {order_id}")
        except Exception as e:
            print(f"Error: {e}")
            skipped_records.append(record)
            context["messages"].append(f"Error processing record: {record}. Error: {str(e)}")

    if skipped_records:
        LOGGER.info(f"Skipped Records: {skipped_records}")

    context["skipped_records"] = skipped_records
    return context
