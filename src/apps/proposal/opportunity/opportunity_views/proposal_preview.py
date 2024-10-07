import json
import urllib.parse

from django.http import JsonResponse

from apps.constants import ERROR_RESPONSE
from apps.rental.mixin import ViewMixin

from ..models import AssignedProduct, Invoice, TaskMapping


class AddItemsView(ViewMixin):
    """
    View for adding dynamically generated items to assigned products.
    """

    def add_items(self, data):
        """
        Add items to the assigned products based on the provided data.

        :param data: List of dictionaries containing item information.
        :return: A dictionary indicating the success or failure of the operation.
        """
        try:
            saved = False
            for item in data:
                assigned_prod = AssignedProduct.objects.get(id=int(item["itemCode"]))
                assigned_prod.is_select = True
                assigned_prod.save()
                saved = True

            if saved:
                return {"status": "success", "message": "Item added successfully"}
            else:
                return {"status": "warning", "message": "No item to add"}
        except AssignedProduct.DoesNotExist:
            print("Error: Assigned product not found")
            return ERROR_RESPONSE
        except Exception as e:
            print(f"ERROR: [AddItemsView][2035] {e}")
            return ERROR_RESPONSE

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to add items to assigned products.

        :param request: The HTTP request object containing JSON data.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JsonResponse indicating the result of the add operation.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = json.loads(body_unicode)
            response = self.add_items(data)
            return JsonResponse(response)
        except json.JSONDecodeError:
            print("Invalid JSON")
            return JsonResponse(ERROR_RESPONSE, status=400)


class AddDescriptionView(ViewMixin):
    """
    View for adding dynamically generated descriptions to task mappings.
    """

    def add_description(self, data):
        """
        Add descriptions to task mappings based on the provided data.

        :param data: Dictionary where keys are task IDs and values are lists of description dictionaries.
        :return: A dictionary indicating the success or failure of the operation.
        """
        try:
            saved = False

            for task_id, descriptions in data.items():
                task_mapping_obj = TaskMapping.objects.get(id=task_id)

                # Prepare new descriptions based on incoming data
                new_descriptions = []

                for description_dict in descriptions:
                    for key, value in description_dict.items():
                        if value:
                            new_descriptions.append({key: value})

                # Update the task mapping object with new descriptions if they differ
                if new_descriptions != task_mapping_obj.extra_description:
                    task_mapping_obj.extra_description = new_descriptions or []
                    task_mapping_obj.save()
                    saved = True

            if saved:
                return {"status": "success", "message": "Description updated successfully"}
            else:
                return {"status": "empty", "message": "No updates made."}

        except TaskMapping.DoesNotExist:
            print("Error: Task mapping not found")
            return ERROR_RESPONSE
        except Exception as e:
            print("Error [AddDescriptionView][add_description]", e)
            return ERROR_RESPONSE

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to add descriptions to task mappings.

        :param request: The HTTP request object containing JSON data.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JsonResponse indicating the result of the add operation.
        """
        try:
            data = json.loads(request.body)
            response = self.add_description(data)
            return JsonResponse(response)
        except Exception as e:
            print("Error [AddDescriptionView]", e)
            return JsonResponse(ERROR_RESPONSE, status=400)


class UpdateItemIncludeView(ViewMixin):
    """
    View for updating the inclusion status of items in task mappings.
    """

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to toggle the inclusion status of a task mapping.

        :param request: The HTTP request object containing JSON data.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JsonResponse indicating the success or failure of the update operation.
        """
        try:
            data = json.loads(request.body)
            task_mapping_id = data.get("id")

            # Fetch the TaskMapping object
            task_mapping_obj = TaskMapping.objects.get(id=task_mapping_id)

            # Toggle the include status
            task_mapping_obj.include = not task_mapping_obj.include
            task_mapping_obj.save()

            status_message = "Include item updated successfully"
            return JsonResponse({"status": "success", "message": status_message})

        except TaskMapping.DoesNotExist:
            print("Error: Task Mapping does not exist")
            return JsonResponse(ERROR_RESPONSE, status=404)
        except Exception as e:
            print(f"ERROR: [UpdateItemIncludeView][2071] {e}")
            return JsonResponse(ERROR_RESPONSE, status=500)


class UpdateTaskMappingView(ViewMixin):
    """
    View for updating fields of task mappings.
    """

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to update task mapping fields.

        :param request: The HTTP request object containing the update data.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JsonResponse indicating the success or failure of the update operation.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)

            # Extract parameters with fallback for missing keys
            task_mapping_id = data.get("id", [None])[0]
            update_type = data.get("type", [None])[0]
            new_value = data.get("value", [None])[0]

            # Validate input
            if not all([task_mapping_id, update_type, new_value]):
                return JsonResponse({"status": "error", "message": "Missing required parameters."}, status=400)

            # Fetch task mapping object
            task_mapping_obj = TaskMapping.objects.get(id=task_mapping_id)

            # Define a mapping of update types to object attributes and messages
            update_map = {
                "task_code": ("code", "Task code updated successfully"),
                "task_description": ("description", "Task description updated successfully"),
                "approve": ("approve", "Approve & Initial updated successfully"),
            }

            if update_type in update_map:
                attr, message = update_map[update_type]
                setattr(task_mapping_obj, attr, new_value)
                task_mapping_obj.save()
                return JsonResponse({"status": "success", "message": message}, status=200)

            print("Invalid Update Type")
            return JsonResponse(ERROR_RESPONSE, status=400)

        except TaskMapping.DoesNotExist:
            return JsonResponse(ERROR_RESPONSE, status=404)
        except Exception as e:
            print(f"Error: {e}")  # Logging error for debugging
            return JsonResponse(ERROR_RESPONSE, status=500)


class UpdateProposalItemsView(ViewMixin):
    """
    Update proposal items of a task.
    """

    SUCCESS_MESSAGES = {
        "prod_item_code": "Item Code Updated successfully",
        "prod_labor_task": "Item Updated successfully",
        "prod_local_cost": "Price Updated successfully",
        "prod_description": "Description Updated successfully",
        "prod_quantity": "Quantity Updated successfully",
        "prod_cost": "Price Updated successfully",
    }

    def update_data(self, data):
        """
        Update the attributes of an assigned product based on provided input data.

        :param data: A dictionary containing the input type, id of the product, and the new value.
        :return: A dictionary containing the status and message indicating the result of the update operation.
        """
        try:
            assigned_pro_obj = AssignedProduct.objects.get(id=data.get("id")[0])
            input_type = data.get("input_type")[0]
            value = data.get("value")[0]

            if input_type not in self.SUCCESS_MESSAGES:
                print("Error: Invalid input type")
                return ERROR_RESPONSE

            # Map input types to the corresponding attribute and parsing method
            input_mapping = {
                "prod_local_cost": ("local_cost", self.parse_cost),
                "prod_cost": ("standard_cost", self.parse_cost),
                "prod_quantity": ("quantity", self.parse_quantity),
            }

            if input_type in input_mapping:
                attribute, parser = input_mapping[input_type]
                setattr(assigned_pro_obj, attribute, parser(value))
            else:
                setattr(assigned_pro_obj, input_type.replace("prod_", ""), value)

            assigned_pro_obj.save()
            return {"status": "success", "message": self.SUCCESS_MESSAGES[input_type]}

        except AssignedProduct.DoesNotExist:
            print("Error: Assigned product does not exist")
            return ERROR_RESPONSE
        except (ValueError, TypeError) as e:
            print(f"Value Error: {e}")
            return ERROR_RESPONSE
        except Exception as e:
            print(f"Error [UpdateProposalItemsView][update_data]: {e}")
            return ERROR_RESPONSE

    def parse_cost(self, value):
        """
        Parse a cost value from a string to a float.

        :param value: The cost value as a string, potentially including a currency symbol.
        :return: The parsed cost as a float.
        """
        return float(value.replace("$", "").strip())

    def parse_quantity(self, value):
        """
        Parse a quantity value from a string to an integer.

        :param value: The quantity value as a string.
        :return: The parsed quantity as an integer.
        """
        return float(value.strip())

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to update proposal items.

        :param request: The HTTP request object containing form-encoded data.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JsonResponse indicating the success or failure of the update operation.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            response = self.update_data(data)
            return JsonResponse(response)
        except Exception as e:
            print(f"Error: [UpdateProposalItemsView][post]: {e}")
            return JsonResponse(ERROR_RESPONSE, status=400)


class UpdateInvoiceView(ViewMixin):
    """
    Update Invoice View.
    """

    SUCCESS_MESSAGES = {
        "invoice_number": "Invoice Number Updated successfully",
        "invoice_data": "Invoice Date Updated successfully",
        "deposit_amount": "Deposit Updated successfully",
        "billing_address": "Address Updated successfully",
        "other_tax": "Other Tax Updated successfully",
        "tax_rate": "Tax Rate Updated successfully",
        "sales_tax": "Sales Tax Updated successfully",
        "deposit_address": "Address Updated successfully",
        "buyer": "Buyer Updated successfully",
        "buyer_date": "Buyer Date Updated successfully",
        "buyer_name": "Buyer Name Updated successfully",
        "buyer_position": "Buyer Position Updated successfully",
        "seller": "Seller Updated successfully",
        "seller_date": "Seller Date Updated successfully",
        "seller_name": "Seller Name Updated successfully",
        "seller_position": "Seller Position Updated successfully",
    }

    def update_data(self, data):
        """
        Update the attributes of an invoice based on the provided input data.

        :param data: A dictionary containing the id of the invoice, the type of update, and the new value.
        :return: A dictionary containing the status and message indicating the result of the update operation.
        """
        try:
            invoice_obj = Invoice.objects.get(id=data["id"][0])
            update_type = data["type"][0]
            value = data["value"][0]

            if update_type in self.SUCCESS_MESSAGES:
                setattr(invoice_obj, update_type, value)
                invoice_obj.save()
                return {"status": "success", "message": self.SUCCESS_MESSAGES[update_type]}
            else:
                print("Error: Invalid update type")
                return ERROR_RESPONSE

        except Invoice.DoesNotExist:
            print("Error: Invoice Not Found")
            return ERROR_RESPONSE
        except Exception as e:
            print(f"Error [UpdateInvoiceView][update_data]: {e}")
            return ERROR_RESPONSE

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to update invoice attributes.

        :param request: The HTTP request object containing form-encoded data.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JsonResponse indicating the success or failure of the update operation.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            response = self.update_data(data)
            return JsonResponse(response)
        except Exception as e:
            print(f"Error [UpdateInvoiceView][post]: {e}")
            return JsonResponse(ERROR_RESPONSE, status=400)
