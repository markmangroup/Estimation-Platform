import json
import urllib.parse

from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import CreateView, TemplateView

from apps.constants import ERROR_RESPONSE
from apps.proposal.labour_cost.models import LabourCost
from apps.proposal.product.models import Product
from apps.proposal.task.models import Task
from apps.proposal.vendor.models import Vendor
from apps.rental.mixin import LoginRequiredMixin, ViewMixin

from ..forms import AddTaskForm
from ..models import AssignedProduct, Opportunity, PreliminaryMaterialList, TaskMapping


class AssignProdLabor(LoginRequiredMixin, TemplateView):
    """
    Import data from CSV or Excel files.
    """

    template_name = "proposal/opportunity/stage/task_mapping/assign_prod_labor.html"

    def _get_products_data(self, task_mapping_id, document_number):
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

        assigned_product_ids = list(map(int, assigned_item_codes)) if assigned_item_codes else []

        available_products = all_products.exclude(item_number__in=assigned_product_ids)
        return available_products

    def post(self, request, *args, **kwargs):
        data = json.loads(request.POST.get("items", "[]"))
        document_number = self.kwargs["document_number"]
        task_id = self.kwargs.get("task_id")

        try:
            task_mapping_obj = TaskMapping.objects.get(id=task_id)
        except TaskMapping.DoesNotExist:
            print("Error: Task Mapping does not exist")
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
                print(f"Error: {str(e)}")
                errors.append({"internal_id": internal_id, "error": ERROR_RESPONSE["message"]})

        if errors:
            return JsonResponse({"status": "error", "errors": errors}, status=404)

        task_name = task_mapping_obj.code or task_mapping_obj.task.name
        messages.success(self.request, f'Product assigned for "{task_name}" successfully!')

        return JsonResponse({"status": "success", "created_products": created_products})

    def get_context_data(self, **kwargs):
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

    def update_fields(self, data):
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
            task_mapping.task = Task.objects.get(id=value)
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

    def bulk_update(self, data):
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
                    print(f"filed {field}, value: {value}")
                    if field in ["quantity", "vendor_quoted_cost", "standard_cost"]:
                        setattr(assigned_prod_obj, field, value)
                        assigned_prod_obj.save()

            messages.success(self.request, "Updated Successfully")
            return {"status": "success", "type": "bulk_update", "message": "Product updated successfully"}

        except Exception as e:
            print(f"Error: [UpdateAssignProdView][bulk_update] {e}")
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
            print("Error: Invalid JSON")
            return JsonResponse(ERROR_RESPONSE, status=400)


class AddProdRowView(ViewMixin):
    """
    View to add product data rows based on input.
    """

    def format_data(self, input_data):
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
            task_mapping = TaskMapping.objects.get(id=task_id)

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

    def _save_product(self, task_mapping, product):
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
            description = product_obj.description
        except Exception:  # Handle custom item code data
            product_item_code = item_code
            try:
                product_obj = Product.objects.get(id=product.get("description"))
                description = product_obj.description
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
        )
        return None

    def _save_labor(self, task_mapping, product):
        """
        Save a labor entry.

        :param task_mapping: TaskMapping instance to associate the labor with.
        :param product: Dictionary containing labor data.
        :return: Warning message if a required field is missing, else None.
        """
        quoted_cost = product.get("quotedCost")
        print("quoted_cost", quoted_cost)

        if not quoted_cost:
            return {"status": "warning", "message": "Please add quoted cost"}

        labor_task = LabourCost.objects.filter(id=product.get("task_name")).first()
        task_name_value = labor_task.labour_task if labor_task else product.get("task_name")
        task_description = LabourCost.objects.filter(id=product.get("labor_description")).first()
        task_desc_value = task_description.description if task_description else product.get("labor_description")

        AssignedProduct.objects.create(
            task_mapping=task_mapping,
            quantity=float(product.get("quantity", 0)),
            description=task_desc_value,
            labor_task=task_name_value or "",
            standard_cost=product.get("standardCost", 0),
            vendor_quoted_cost=quoted_cost,
            comment=product.get("comment", ""),
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
            print("Error: Invalid JSON response")
            messages.error(self.request, ERROR_RESPONSE["message"])
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


class AddTaskView(LoginRequiredMixin, CreateView):
    """
    View to add a manual task to task mapping.
    """

    template_name = "proposal/opportunity/stage/task_mapping/add_tasks.html"
    form_class = AddTaskForm

    def form_valid(self, form):
        """
        Handle valid form submission to create a new TaskMapping.

        :param form: The submitted form with valid data.
        :return: JsonResponse indicating success.
        """
        document_number = self.kwargs["document_number"]

        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
        except Opportunity.DoesNotExist:
            print("Opportunity does not exist")
            return JsonResponse(ERROR_RESPONSE, status=404)

        # Get form data
        code = form.cleaned_data["code"]
        description = form.cleaned_data["description"]

        if code and description:
            TaskMapping.objects.create(opportunity=opportunity, code=code, description=description)
            messages.success(self.request, f'Task "{code} - {description}" added successfully!')
            return JsonResponse({"status": "success", "code": "200"})

        return JsonResponse({"status": "error", "message": "Code and description are required."}, status=400)

    def form_invalid(self, form):
        """
        Handle invalid form submission.

        :param form: The submitted form with errors.
        :return: Render response with the form errors.
        """
        return self.render_to_response(self.get_context_data(form=form), status=400)

    def get_context_data(self, **kwargs):
        """
        Add additional context to the template.

        :param kwargs: Additional keyword arguments.
        :return: Updated context dictionary.
        """
        context = super().get_context_data(**kwargs)
        context["document_number"] = self.kwargs["document_number"]
        return context


class TaskMappingData:

    @staticmethod
    def _get_tasks(document_number):
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.exclude(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                product.standard_cost if product.standard_cost else product.vendor_quoted_cost
                for product in task_assigned_products
            )

            total_percent = sum(product.gross_profit_percentage for product in task_assigned_products)

            tasks_with_products[task.id] = {
                "task": task,
                "assigned_products": task_assigned_products,
                "total_quantity": round(total_quantity, 2),
                "total_price": round(total_price, 2),
                "total_percent": round(total_percent, 2),
            }

        return tasks_with_products

    @staticmethod
    def _get_task_total(document_number):
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.exclude(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                product.standard_cost if product.standard_cost else product.vendor_quoted_cost
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

    @staticmethod
    def _get_labour_tasks(document_number):
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.filter(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                product.standard_cost if product.standard_cost else product.vendor_quoted_cost
                for product in task_assigned_products
            )

            total_percent = sum(product.gross_profit_percentage for product in task_assigned_products)

            tasks_with_products[task.id] = {
                "task": task,
                "assigned_products": task_assigned_products,
                "total_quantity": round(total_quantity, 2),
                "total_price": round(total_price, 2),
                "total_percent": round(total_percent, 2),
            }

        return tasks_with_products

    @staticmethod
    def _get_labor_task_total(document_number):
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)
        filtered_task_mappings = task_mappings.filter(task__description__icontains="labor")
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in filtered_task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)
            total_price = sum(
                product.standard_cost if product.standard_cost else product.vendor_quoted_cost
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
