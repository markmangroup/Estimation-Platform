import json
import urllib.parse
from typing import Any, Dict

from django.contrib import messages
from django.db.models import QuerySet
from django.http import JsonResponse

from apps.constants import ERROR_RESPONSE, LOGGER
from apps.mixin import TemplateViewMixin, ViewMixin
from django.shortcuts import get_object_or_404, render
from apps.proposal.labour_cost.models import LabourCost
from apps.proposal.product.models import Product
from apps.proposal.task.models import Task
from apps.proposal.vendor.models import Vendor

from ..models import AssignedProduct, Opportunity, PreliminaryMaterialList, TaskMapping


class AssignProdLabor(TemplateViewMixin):
    """
    Import data from CSV or Excel files.
    """

    template_name = "proposal/opportunity/stage/task_mapping/assign_prod_labor.html"

    def _get_products_data(self, task_mapping_id: int, document_number: str) -> QuerySet:
        """
        Retrieve available products for a specific task mapping and document number.

        :param task_mapping_id: ID of the task mapping to filter assigned products.
        :param document_number: Document number associated with the opportunity to filter products.
        :return: QuerySet of available products that are not assigned to the task mapping.
        """
        all_products = PreliminaryMaterialList.objects.filter(opportunity__document_number=document_number)

        assigned_item_codes = AssignedProduct.objects.filter(task_mapping__id=task_mapping_id).values_list(
            "item_code", flat=True
        )

        assigned_product_ids = list(map(str, assigned_item_codes)) if assigned_item_codes else []

        available_products = all_products.exclude(item_number__in=assigned_product_ids)

        return available_products

    def post(self, request, *args, **kwargs) -> JsonResponse:

        data = json.loads(request.POST.get("items", "[]"))
        document_number = self.kwargs["document_number"]
        task_id = self.kwargs.get("task_id")

        try:
            task_mapping_obj = TaskMapping.objects.get(id=task_id)
        except TaskMapping.DoesNotExist:
            LOGGER.error("Task Mapping does not exist")
            return JsonResponse(ERROR_RESPONSE, status=404)

        created_products = []
        errors = []

        for item in data:
            internal_id = item.get("internal_id")
            try:
                prod_obj = PreliminaryMaterialList.objects.get(
                    opportunity__document_number=document_number, item_number=internal_id
                )

                assigned_product = AssignedProduct(
                    task_mapping=task_mapping_obj,
                    quantity=prod_obj.combined_quantities_from_both_import,
                    item_code=prod_obj.item_number,
                    description=prod_obj.description,
                    standard_cost=2,
                    is_assign=True,
                )
                assigned_product.save()
                created_products.append(assigned_product.id)

            except PreliminaryMaterialList.DoesNotExist:
                errors.append({"internal_id": internal_id, "error": "Product not found"})
            except Exception as e:
                LOGGER.error(f"{str(e)}")
                errors.append({"internal_id": internal_id, "error": ERROR_RESPONSE["message"]})

        if errors:
            return JsonResponse({"status": "error", "errors": errors}, status=404)

        task_name = task_mapping_obj.code or task_mapping_obj.task.name
        messages.success(self.request, f'Product assigned for "{task_name}" successfully!')

        return JsonResponse({"status": "success", "created_products": created_products})

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        document_number = self.kwargs["document_number"]
        task_mapping_id = self.kwargs["task_id"]

        context["products"] = self._get_products_data(task_mapping_id, document_number)
        context["document_number"] = document_number
        context["task_id"] = task_mapping_id
        return context


class UpdateAssignProdView(ViewMixin):
    """
    View to update assigned product and task mapping data.
    """

    def update_fields(self, data: dict) -> dict:
        """
        Update fields in the database based on input.

        :param data: Dictionary containing the field data to update.
        :return: Response data indicating success or failure.
        """
        input_type = data.get("type", [""])[0]
        id = data.get("id", [""])[0]
        value = data.get("value", [""])[0].strip()

        if input_type == "task":
            task_mapping = TaskMapping.objects.get(id=id)
            task_obj = Task.objects.get(id=value)
            task_mapping.task = task_obj
            task_mapping.code = task_obj.name
            task_mapping.is_assign_task = False
            task_mapping.assign_to = ""
            task_mapping.save()
            return {"status": "success", "message": "Task updated successfully"}

        assigned_prod = AssignedProduct.objects.get(id=id)

        if input_type == "quantity":
            assigned_prod.quantity = value
            msg = "Quantity updated successfully"
        elif input_type == "standard_cost":
            assigned_prod.standard_cost = value
            msg = "Standard cost updated successfully"
        elif input_type == "vendor_quoted_cost":
            assigned_prod.vendor_quoted_cost = value
            msg = "Vendor quoted cost updated successfully"
        elif input_type == "comment":
            assigned_prod.comment = value
            msg = "Comment updated successfully"
        elif input_type == "vendor":
            assigned_prod.vendor = Vendor.objects.get(id=value).name
            msg = "Vendor updated successfully"
        elif input_type == "labor-task":
            task_mapping.task = Task.objects.get(id=value)
            task_mapping.save()
            return {"status": "success", "message": "Labor task updated successfully"}
        else:
            return {"status": "error", "message": "Invalid type"}

        assigned_prod.save()
        return {"status": "success", "message": msg}

    def bulk_update(self, data: dict) -> dict:
        """
        Perform bulk updates on assigned products based on input data.

        :param data: Dictionary containing bulk update data.
        :return: Response data indicating success or failure.
        """
        try:
            rows = {}

            for key, value in data.items():
                if key.startswith("rows["):
                    row_index = key.split("[")[1].split("]")[0]
                    field_name = key.split("[")[2].split("]")[0]

                    if row_index not in rows:
                        rows[row_index] = {}
                    rows[row_index][field_name] = value[0].strip()

            for index, row in rows.items():
                assigned_prod_obj = AssignedProduct.objects.get(id=row.get("assign_prod_id"))
                for field, value in row.items():
                    if field in ["quantity", "vendor_quoted_cost", "standard_cost"]:
                        setattr(assigned_prod_obj, field, value)
                        assigned_prod_obj.save()

            messages.success(self.request, "Updated Successfully")
            return {"status": "success", "type": "bulk_update", "message": "Product updated successfully"}

        except Exception as e:
            LOGGER.error(f"[UpdateAssignProdView][bulk_update] {e}")
            return ERROR_RESPONSE

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to update assigned products.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)

            if data.get("type")[0] == "bulk_update":
                response = self.bulk_update(data)
            else:
                response = self.update_fields(data)

            return JsonResponse(response)

        except json.JSONDecodeError:
            LOGGER.error("Invalid JSON")
            return JsonResponse(ERROR_RESPONSE, status=400)


class AddProdRowView(ViewMixin):
    """
    View to add product data rows based on input.
    """

    def format_data(self, input_data: dict) -> dict:
        """
        Format and save product data from the input.

        :param input_data: Dictionary containing the product data.
        :return: Response data indicating the result of the operation.
        """
        result = {}

        for key, value in input_data.items():
            parts = key.split("][")
            field_name = parts[1].split("]")[0]
            index = parts[0].split("[")[-1]
            task_id = input_data.get(f"rows[{index}][task_id]", [None])[0]

            if task_id not in result:
                result[task_id] = []

            task_data = {field_name: value[0]}
            existing_entry = next((entry for entry in result[task_id] if entry.get("index") == index), None)

            if existing_entry:
                existing_entry.update(task_data)
            else:
                task_data["index"] = index
                task_data["task_id"] = task_id
                result[task_id].append(task_data)

        overall_data_saved = False

        for task_id, products in result.items():
            task_mapping: TaskMapping = TaskMapping.objects.get(id=task_id)
            if task_mapping:
                for product in products:
                    if not product.get("item_code") and not product.get("task_name"):
                        continue

                    if product.get("item_code"):
                        response = self._save_product(task_mapping, product)
                        if response:
                            return response  # Return warning if any required field is missing
                        overall_data_saved = True

                    elif product.get("task_name"):
                        response = self._save_labor(task_mapping, product)
                        if response:
                            return response  # Return warning if any required field is missing
                        overall_data_saved = True

        return (
            {"status": "success", "message": "Product added successfully"}
            if overall_data_saved
            else {"status": "empty", "message": ""}
        )

    def _save_product(self, task_mapping: TaskMapping, product: dict):
        """
        Save a product entry.

        :param task_mapping: TaskMapping instance to associate the product with.
        :param product: Dictionary containing product data.
        :return: Warning message if a required field is missing, else None.
        """
        item_code = product.get("item_code")
        std_cost = product.get("standardCost")

        if not std_cost:
            return {"status": "warning", "message": "Please add standard cost"}

        vendor = Vendor.objects.filter(id=product.get("vendor")).first()

        try:
            product_obj = Product.objects.get(id=item_code)
            product_item_code = product_obj.internal_id
            description = product_obj.display_name
        except Exception:  # Handle custom item code data
            product_item_code = item_code
            try:
                product_obj = Product.objects.get(id=product.get("description"))
                description = product_obj.display_name
            except Exception:  # Handle custom description data
                description = product.get("description")

        AssignedProduct.objects.create(
            task_mapping=task_mapping,
            quantity=float(product.get("quantity", 0)),
            item_code=product_item_code,
            description=description,
            standard_cost=float(std_cost),
            vendor_quoted_cost=float(product.get("quotedCost", 0)),
            vendor=vendor,
            comment=product.get("comment", ""),
            sequence=product.get("sequence_number", ""),
        )
        return None

    def _save_labor(self, task_mapping: TaskMapping, product: dict):
        """
        Save a labor entry.

        :param task_mapping: TaskMapping instance to associate the labor with.
        :param product: Dictionary containing labor data.
        :return: Warning message if a required field is missing, else None.
        """
        quoted_cost = product.get("quotedCost")

        if not quoted_cost:
            return {"status": "warning", "message": "Please add quoted cost"}

        try:
            labor_task = LabourCost.objects.filter(id=product.get("task_name")).first()
            task_name_value = labor_task.labour_task
            task_desc_value = labor_task.description if labor_task else product.get("labor_description")
        except Exception:  # Handle custom item code data
            task_name_value = product.get("task_name")
            try:
                labor_task = LabourCost.objects.filter(id=product.get("task_name")).first()
                task_desc_value = labor_task.description
            except Exception:
                task_desc_value = product.get("labor_description")

        AssignedProduct.objects.create(
            task_mapping=task_mapping,
            quantity=float(product.get("quantity", 0)),
            description=task_desc_value,
            labor_task=task_name_value or "",
            standard_cost=product.get("standardCost", 0),
            vendor_quoted_cost=quoted_cost,
            comment=product.get("comment", ""),
            sequence=product.get("sequence_number", ""),
        )
        return None

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to add product data.

        :param request: The request object containing the product data.
        :return: JsonResponse with the status of the operation.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)

            if not data:
                return JsonResponse({"status": "empty", "message": "Please enter data"})

            response = self.format_data(data)
            if response["status"] == "success":
                messages.success(self.request, response["message"])
            elif response["status"] == "warning":
                messages.warning(self.request, response["message"])
            elif response["status"] == "error":
                messages.error(self.request, response["message"])

            return JsonResponse(response)

        except json.JSONDecodeError:
            LOGGER.error("Invalid JSON response")
            messages.error(self.request, ERROR_RESPONSE["message"])
            return JsonResponse(ERROR_RESPONSE, status=400)


class AssignTaskLaborView(ViewMixin):
    """
    View to link labor with task.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Retrieve available tasks for the specified opportunity."""
        document_number = kwargs.get("document_number")

        opportunity_obj = Opportunity.objects.filter(document_number=document_number).first()
        qs = TaskMapping.objects.filter(opportunity=opportunity_obj, is_assign_task=False).exclude(
            description__icontains="labor"
        )
        task_item_list = [{"id": t.id, "text": t.code} for t in qs]
        return JsonResponse({"results": task_item_list})

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Assign a labor task to a current task."""
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)

            current_task_id = data["id"][0]
            value = data["value"][0]

            current_task = TaskMapping.objects.get(id=current_task_id)
            assign_labor_task = TaskMapping.objects.get(id=value)

            current_task.assign_to = assign_labor_task.code
            current_task.save()
            assign_labor_task.is_assign_task = True
            assign_labor_task.assign_to = current_task.code
            assign_labor_task.save()

            messages.success(request, f"Labor Assigned to task {assign_labor_task.code}")
            return JsonResponse(
                {
                    "code": 200,
                    "message": "success",
                }
            )

        except TaskMapping.DoesNotExist:
            LOGGER.error("Task Mapping does not exist")
            return JsonResponse(ERROR_RESPONSE, status=404)
        except Exception as e:
            LOGGER.error(f"AssignTaskLaborView: {e}")
            return JsonResponse(ERROR_RESPONSE, status=400)


class DeleteAssignProdLabor(ViewMixin):
    """
    View to delete assigned product objects.
    """

    def post(self, request) -> JsonResponse:
        """
        Handle POST requests to delete an assigned product.

        :param request: The request object containing the ID of the assigned product to delete.
        :return: JsonResponse indicating the result of the deletion operation.
        """
        assigned_prod_id = request.POST.get("id")
        AssignedProduct.objects.filter(id=assigned_prod_id).delete()
        return JsonResponse({"message": "Deleted Successfully.", "code": 200, "status": "success"})


# NOTE: Old feature of `Add Task` for `Task Mapping Screen` 
# class AddTaskView(CreateViewMixin):
#     """
#     View to add a manual task to task mapping.
#     """

#     template_name = "proposal/opportunity/stage/task_mapping/add_tasks.html"
#     form_class = AddTaskForm

#     def form_valid(self, form):
#         """
#         Handle valid form submission to create a new TaskMapping.

#         :param form: The submitted form with valid data.
#         :return: JsonResponse indicating success.
#         """
#         document_number = self.kwargs["document_number"]

#         try:
#             opportunity = Opportunity.objects.get(document_number=document_number)
#         except Opportunity.DoesNotExist:
#             LOGGER.error("Opportunity does not exist")
#             return JsonResponse(ERROR_RESPONSE, status=404)

#         # Get form data
#         code = form.cleaned_data["code"]
#         description = form.cleaned_data["description"]

#         if code and description:
#             TaskMapping.objects.create(opportunity=opportunity, code=code, description=description)
#             messages.success(self.request, f'Task "{code} - {description}" added successfully!')
#             return JsonResponse({"status": "success", "code": "200"})

#         return JsonResponse({"status": "error", "message": "Code and description are required."}, status=400)

#     def form_invalid(self, form):
#         """
#         Handle invalid form submission.

#         :param form: The submitted form with errors.
#         :return: Render response with the form errors.
#         """
#         return self.render_to_response(self.get_context_data(form=form), status=400)

#     def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
#         """
#         Add additional context to the template.

#         :param kwargs: Additional keyword arguments.
#         :return: Updated context dictionary.
#         """
#         context = super().get_context_data(**kwargs)
#         context["document_number"] = self.kwargs["document_number"]
#         return context


class AddTaskView(ViewMixin):
    """
    View to add a manual task to task mapping.
    """

    template_name = "proposal/opportunity/stage/task_mapping/add_tasks.html"

    def __get(self, document_number: str) -> dict:  
        """
        Returns context data with available tasks.

        :param document_number: The document number associated with the opportunity.
        :return: A dictionary containing available tasks and the document number.
        """
        opportunity = get_object_or_404(Opportunity, document_number=document_number)

        selected_task_ids = (
            TaskMapping.objects.filter(opportunity=opportunity, task__isnull=False)
            .values_list("task_id", flat=True)
        )        
        available_tasks = Task.objects.exclude(id__in=selected_task_ids)

        return {
            "select_tasks": available_tasks,
            "document_number": document_number,
        }

    def get(self, request, *args, **kwargs):
        """
        Render the task selection template with available tasks.

        :param request: The HTTP request object.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments, including 'document_number'.
        :return: Rendered response containing available tasks.
        """
        document_number = self.kwargs.get("document_number")
        context = self.__get(document_number)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle task selection and creation.

        :param request: The HTTP request object containing form data.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JSON response indicating success or error status.
        """
        tasks = request.POST.getlist("task")
        description = request.POST.get("description")
        print(f'description {type(description)}: {description}')
        document_number = request.POST.get("document_number")

        if not tasks or not document_number:
            return JsonResponse({"error": "Tasks and document number are required."}, status=400)

        opportunity = get_object_or_404(Opportunity, document_number=document_number)        

        for task_name in tasks:
            task_instance = get_object_or_404(Task, name=task_name)
            if description:
                task_description = description
            else:
                task_description = task_instance.description

            TaskMapping.objects.create(
                opportunity=opportunity, task=task_instance,
                code=task_instance.name, description=task_description
            )

        messages.success(request, "Tasks added successfully!")
        return JsonResponse(
            {
                "status": "Created",
                "message": "Task added successfully",
            },
            status=201,
        )

    def render_to_response(self, context, **response_kwargs):
        """
        Render the response using the template specified.

        :param context: A dictionary containing the context data for rendering.
        :param response_kwargs: Additional keyword arguments for rendering.
        :return: Rendered response.
        """
        return render(self.request, self.template_name, context, **response_kwargs)


class TaskMappingData:

    @staticmethod
    def _get_total_tasks(document_number: str) -> int:
        """
        Returns the total number of tasks.

        :param document_number: The document number to filter task mappings.
        """
        task_mapping_obj = TaskMapping.objects.filter(opportunity__document_number=document_number)
        return len(task_mapping_obj)

    @staticmethod
    def _get_tasks(document_number: str) -> dict:
        """
        Retrieve tasks and their assigned products for a given document number.

        :param document_number: The document number to filter task mappings.
        :return: A dictionary with task details, including total quantities, prices, and profit percentages.
        """
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.exclude(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        try:
            assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids).order_by(
                "sequence"
            )

        except Exception as e:
            LOGGER.error(f"assigned_products Exception : {e}")
            assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                (
                    product.vendor_quoted_cost * product.quantity
                    if product.vendor_quoted_cost
                    else product.standard_cost * product.quantity
                )
                for product in task_assigned_products
            )
            total_unit_price = sum(
                product.vendor_quoted_cost if product.vendor_quoted_cost else product.standard_cost
                for product in task_assigned_products
            )

            total_percent = sum(product.gross_profit_percentage for product in task_assigned_products)

            tasks_with_products[task.id] = {
                "task": task,
                "assigned_products": task_assigned_products,
                "total_quantity": round(total_quantity, 2),
                "total_price": round(total_price, 2),
                "total_unit_price": round(total_unit_price, 2),
                "total_percent": round(total_percent, 2),
            }

        return tasks_with_products

    @staticmethod
    def _get_task_total(document_number: str) -> dict:
        """
        Calculate total quantities and prices for tasks associated with a document number.

        :param document_number: The document number to filter task mappings.
        :return: A dictionary with grand total quantity and price.
        """
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.exclude(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                (
                    (product.vendor_quoted_cost if product.vendor_quoted_cost is not None else product.standard_cost)
                    * product.quantity
                )
                for product in task_assigned_products
            )

            tasks_with_products[task.id] = {
                "total_quantity": total_quantity,
                "total_price": total_price,
            }

        # Calculate grand total price and quantity
        grand_total_price = sum(v["total_price"] for v in tasks_with_products.values())
        grand_total_quantity = sum(v["total_quantity"] for v in tasks_with_products.values())

        total_data = {
            "grand_total_price": round(grand_total_price, 2),
            "grand_total_quantity": round(grand_total_quantity, 2),
        }
        return total_data

    @staticmethod
    def _get_labour_tasks(document_number: str) -> dict:
        """
        Retrieve labor tasks and their assigned products for a given document number.

        :param document_number: The document number to filter task mappings.
        :return: A dictionary containing labor task details, including total quantities, prices, and profit percentages.
        """
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.filter(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        try:
            assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids).order_by(
                "sequence"
            )
        except Exception as e:
            LOGGER.error(f"error: {e}")
            assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                (
                    product.vendor_quoted_cost * product.quantity
                    if product.vendor_quoted_cost
                    else product.standard_cost * product.quantity
                )
                for product in task_assigned_products
            )
            total_unit_price = sum(
                product.vendor_quoted_cost if product.vendor_quoted_cost else product.standard_cost
                for product in task_assigned_products
            )

            total_percent = sum(product.gross_profit_percentage for product in task_assigned_products)

            tasks_with_products[task.id] = {
                "task": task,
                "assigned_products": task_assigned_products,
                "total_quantity": round(total_quantity, 2),
                "total_price": round(total_price, 2),
                "total_unit_price": round(total_unit_price, 2),
                "total_percent": round(total_percent, 2),
            }

        return tasks_with_products

    @staticmethod
    def _get_labor_task_total(document_number: str) -> dict:
        """
        Calculate total quantities and prices for labor tasks associated with a document number.

        :param document_number: The document number to filter task mappings.
        :return: A dictionary with grand total quantity and price for labor tasks.
        """
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.filter(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                (
                    product.vendor_quoted_cost * product.quantity
                    if product.vendor_quoted_cost * product.quantity
                    else product.standard_cost
                )
                for product in task_assigned_products
            )

            tasks_with_products[task.id] = {
                "total_quantity": total_quantity,
                "total_price": total_price,
            }

        # Calculate grand total price correctly
        grand_total_price = sum(v["total_price"] for v in tasks_with_products.values())
        grand_total_quantity = sum(v["total_quantity"] for v in tasks_with_products.values())

        total_data = {
            "grand_total_price": round(grand_total_price, 2),
            "grand_total_quantity": round(grand_total_quantity, 2),
        }
        return total_data


class UpdateSequenceView(ViewMixin):
    """Update sequence of rows."""

    def __update_sequence(self, body: bytes) -> None:
        """
        Updates the sequence field for each row in the provided data.
        :prams:body (bytes): The JSON-encoded request body containing sequence data.
        """
        data = json.loads(body)
        sequence_data = data.get("sequence", [])

        for item in sequence_data:
            row_id = item.get("id")
            new_sequence = item.get("sequence")

            if row_id:
                AssignedProduct.objects.filter(id=row_id).update(sequence=new_sequence)

    def post(self, request, *args, **kwargs):
        """POST request to update sequence"""
        try:
            self.__update_sequence(request.body)
            return JsonResponse({"status": "success", "message": "Sequence updated successfully"})

        except Exception:
            return JsonResponse({"status": "error", "message": ERROR_RESPONSE}, status=400)
