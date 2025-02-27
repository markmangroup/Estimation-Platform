from datetime import datetime
import os

import pandas as pd
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.timezone import now
from apps.constants import LOGGER
from apps.rental.product.models import RentalProduct
from apps.rental.rent_process.models import Delivery, Order, OrderItem
from apps.rental.customer.models import RentalCustomer
from apps.rental.account_manager.models import AccountManager


def convert_date(date_str):
    date_str = str(date_str).strip()
    if date_str in ["", "-", "N/A", "None"]:
        return None
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception as e:
        return None


def import_order_from_file(file: InMemoryUploadedFile) -> dict:
    """
    Imports product data from an uploaded Excel or CSV file.

    :param file: The uploaded file containing product data.
    :return: A context dictionary with messages about created/updated products
            or errors if the columns do not match or records are skipped.
    """
    expected_columns = {
        "Customer",
        "Product",
        "Quentity",
        "Per Unit Price",
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
        product = record.get("Product")
        quentity = record.get("Quentity")
        per_unit_price = record.get("Per Unit Price")

        rent_amount = record["Order Amount"].replace("$", "").replace(",", "").strip()
        try:
            rent_amount = float(rent_amount)
        except ValueError:
            skipped_records.append(record)
            context["messages"].append(f"Invalid 'Order Amount' in record: {record}. Must be a valid decimal number.")
            continue

        customer = RentalCustomer.objects.filter(customer_id=record["Customer"]).first()
        account_manager = AccountManager.objects.filter(email=record["Account Manager"]).first()
        skip_product = RentalProduct.objects.filter(equipment_id=product).first()

        if not all([customer, account_manager, skip_product]):
            skipped_records.append(record)
            missing_entities = []
            
            if not customer:
                missing_entities.append("Customer")
            if not account_manager:
                missing_entities.append("Account Manager")
            if not skip_product:
                missing_entities.append("Rental Product")
            context["messages"].append(
                f"{', '.join(missing_entities)} not found for Order ID: {customer}. Skipping record."
            )
            continue

        order_data = {
            "customer": customer,
            "account_manager": account_manager,
            "rent_amount": rent_amount,
            "rental_start_date": convert_date(record["Start Date"]),
            "rental_end_date": convert_date(record["End Date"]),
            "repeat_type": record["Reccurence Type"],
        }

        try:
            order, created = Order.objects.update_or_create(
                customer=customer,
                defaults=order_data,
            )
            action = "Created" if created else "Updated"
            context["messages"].append(f"{action} product with Order ID: {order.order_id}")

            # Create OrderItem for each product in the record
            if product and quentity and per_unit_price:
                try:
                    rental_product = RentalProduct.objects.get(equipment_id=product)
                    order_item, _ = OrderItem.objects.update_or_create(  # Tuple unpacking
                        order=order,
                        product=rental_product,
                        defaults={
                            "quantity": int(quentity),
                            "per_unit_price": float(per_unit_price),
                        }
                    )
                    context["messages"].append(f"Created OrderItem for Order ID: {order.order_id} and Product: {product}")
                except RentalProduct.DoesNotExist:
                    skipped_records.append(record)
                    context["messages"].append(f"Product '{product}' not found for Order ID: {order.order_id}. Skipping OrderItem creation.")
        except Exception as e:
            skipped_records.append(record)
            context["messages"].append(f"Error processing record: {record}. Error: {str(e)}")

    if skipped_records:
        LOGGER.info(f"Skipped Records: {skipped_records}")

    context["skipped_records"] = skipped_records
    return context

def generate_delivery_id(order, delivery_type="DEL"):
    """
    Generate a unique delivery_id for a new delivery.
    
    Format:
    - Delivery: 'O20240200018-1'
    - Return Delivery: 'O20240200018-R1'
    """
    order_prefix = f"O{now().strftime('%Y%m')}{str(order.id).zfill(5)}"
    count = Delivery.objects.filter(order=order).count() + 1
    suffix = f"-R{count}" if delivery_type == "RET" else f"-{count}"
    
    return f"{order_prefix}{suffix}"
