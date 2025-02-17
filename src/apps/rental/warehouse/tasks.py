import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from celery import shared_task
from django.core.files.uploadedfile import InMemoryUploadedFile

from apps.constants import LOGGER
from apps.rental.services.google_map import GoogleMap
from apps.rental.warehouse.models import RentalWarehouse

google_map_service = GoogleMap()


def import_warehouse_from_xlsx(file: InMemoryUploadedFile) -> dict:
    """
    Imports warehouse data from an Excel or CSV file.

    :prams file (File): The uploaded file containing product data.
    """
    file_extension = os.path.splitext(file.name)[1].lower()
    context = {"messages": []}
    skip_warehouse = []

    # Define the expected columns
    expected_columns = ["Warehouse Name", "Address"]

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
    warehouse_list = df.fillna("").to_dict(orient="records")

    # Process each customer record
    for record in warehouse_list:
        try:

            location = record["Warehouse Name"]
            address = record["Address"]

            if location:
                warehouse, created = RentalWarehouse.objects.update_or_create(
                    location=location,
                    defaults={"address": address},
                )

                message = f"{'Created' if created else 'Updated'} Warehouse: {location}"
                context["messages"].append(message)
            else:
                message = f"Email Not Found"
                context["messages"].append(message)

        except Exception as e:
            LOGGER.error(f"Error processing record {record['ID']}: {e}")
            skip_warehouse.append(record)

    # Log skipped customers if any
    if skip_warehouse:
        LOGGER.info(f"Skipped Warehouse: {skip_warehouse}")

    return context


@shared_task()
def update_warehouse_lat_and_log():
    """Update Warehouse Lat and Log As per Address."""
    # Get Warehouse Objects.
    warehouse = RentalWarehouse.objects.all()

    def update_location(warehouse):
        city = ""
        state = ""
        country = ""
        billing_location = google_map_service.get_geo_code_from_address(warehouse.address, city, state, country)
        if billing_location:
            warehouse.lat = billing_location.get("lat")
            warehouse.lng = billing_location.get("lng")
            warehouse.save()

    # Using ThreadPoolExecutor to process customers in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust max_workers as needed
        futures = {executor.submit(update_location, w): w for w in warehouse}

        for future in as_completed(futures):
            warehouse = futures[future]
            try:
                future.result()  # This will raise an exception if update_location fails
            except Exception as e:
                # Handle exceptions (e.g., log them)
                LOGGER.error(f"Error updating location for warehouse {warehouse.id}: {e}")

    return "Warehouse's location has been updated"
