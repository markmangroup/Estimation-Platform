import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from celery import shared_task
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.constants import LOGGER
from apps.rental.customer.models import RentalCustomer
from apps.rental.services.google_map import GoogleMap

google_map_service = GoogleMap()


def import_customer_from_xlsx(file: InMemoryUploadedFile) -> dict:
    """
    Imports customer data from an Excel or CSV file.

    :prams file (File): The uploaded file containing product data.
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

            customer, created = RentalCustomer.objects.update_or_create(
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


@shared_task()
def update_customer_lat_and_log():
    """Update Customer Lat and Log As per Address."""
    # Get Rental Customer Objects.
    rental_customers = RentalCustomer.objects.all()

    def update_location(customer):
        address = customer.billing_address_1 if customer.billing_address_1 else customer.billing_address_2
        billing_location = google_map_service.get_geo_code_from_address(
            address, customer.city, customer.state, customer.country
        )
        if billing_location:
            customer.lat = billing_location.get("lat")
            customer.lng = billing_location.get("lng")
            customer.save()

    # Using ThreadPoolExecutor to process customers in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed
        futures = {executor.submit(update_location, customer): customer for customer in rental_customers}

        for future in as_completed(futures):
            customer = futures[future]
            try:
                future.result()  # This will raise an exception if update_location fails
            except Exception as e:
                # Handle exceptions (e.g., log them)
                LOGGER.error(f"Error updating location for customer {customer.id}: {e}")

    return "Customer's location has been updated"
