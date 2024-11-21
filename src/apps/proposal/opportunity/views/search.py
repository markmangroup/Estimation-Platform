import urllib.parse

from django.contrib import messages
from django.http import JsonResponse

from apps.constants import ERROR_RESPONSE, LOGGER, RESPONSE_CODE_0
from apps.mixin import ViewMixin
from apps.proposal.customer.models import Customer
from apps.proposal.labour_cost.models import LabourCost
from apps.proposal.product.models import Product
from apps.proposal.task.models import Task
from apps.proposal.vendor.models import Vendor

from ..models import AssignedProduct, Opportunity, TaskMapping


class ItemCodeSearchView(ViewMixin):
    """
    View for searching item codes and retrieving product details.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles GET requests for searching item codes.

        :param request: The HTTP request object containing search parameters.
        :return: JsonResponse containing a list of item codes matching the search term.
        """
        search_term = request.GET.get("q", "")
        item_codes = Product.objects.filter(internal_id__icontains=search_term)[:15]
        item_code_list = [{"id": item_code.id, "text": item_code.internal_id} for item_code in item_codes]
        item_code_list.insert(0, {"id": "0", "text": "--------------"})
        return JsonResponse({"results": item_code_list})

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles POST requests to retrieve product details by ID.

        :param request: The HTTP request object containing the product ID.
        :return: JsonResponse containing the product's description and standard cost.
        :raises Product.DoesNotExist: If no product is found with the given ID.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            id = data["value"][0]
            product_object = Product.objects.get(id=id)

            return JsonResponse(
                {
                    "code": 200,
                    "message": "success",
                    "description": product_object.description,
                    "std_cost": product_object.std_cost,
                }
            )

        except Product.DoesNotExist:
            LOGGER.error(f"Error: Product ID Dose Not Exists")
            return RESPONSE_CODE_0

        except Exception as e:
            LOGGER.error(f"Error: {e}")
            return RESPONSE_CODE_0


class ItemDescriptionSearchView(ViewMixin):
    """
    View for searching item descriptions.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles GET requests for searching item descriptions.

        :param request: The HTTP request object containing search parameters.
        :return: JsonResponse containing a list of item descriptions matching the search term.
        """
        search_term = request.GET.get("q", "")
        item_descriptions = Product.objects.filter(description__icontains=search_term)[:15]
        item_description_list = [
            {"id": item_description.id, "text": item_description.description} for item_description in item_descriptions
        ]
        item_description_list.insert(0, {"id": "Clear", "text": "--------------"})
        return JsonResponse({"results": item_description_list})

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles POST requests to retrieve product details by ID.

        :param request: The HTTP request object containing the product ID.
        :return: JsonResponse containing the product's item code and standard cost.
        :raises Product.DoesNotExist: If no product is found with the given ID.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)

            id = data["value"][0]
            product_object = Product.objects.get(id=id)

            return JsonResponse(
                {
                    "code": 200,
                    "message": "success",
                    "item_code": product_object.internal_id,
                    "std_cost": product_object.std_cost,
                }
            )

        except Product.DoesNotExist:
            LOGGER.error(f"Error: Product ID Dose Not Exists")
            return RESPONSE_CODE_0

        except Exception as e:
            LOGGER.error(f"Error: {e}")
            return RESPONSE_CODE_0


class VendorSearchView(ViewMixin):
    """
    View handles searching for vendors based on a search term,
    returning a limited list of matching vendors.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles GET requests for searching vendors.

        :param request: The HTTP request object containing the search parameters.
        :return: JsonResponse containing a list of vendors matching the search term.
        """
        search_term = request.GET.get("q", "")

        # Filter vendors based on the search term
        vendors = Vendor.objects.filter(name__icontains=search_term)[:15]  # Limit results to 15

        vendor_list = [{"id": vendor.id, "text": vendor.name} for vendor in vendors]
        return JsonResponse({"results": vendor_list})


class CustomerSearchView(ViewMixin):
    """
    View handles searching for customers by name and adding a customer to an opportunity.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles GET requests for searching customers.

        :param request: The HTTP request object containing search parameters.
        :return: JsonResponse containing a list of customers matching the search term.
        """
        search_term = request.GET.get("q", "")
        customers = Customer.objects.filter(name__icontains=search_term)[:15]
        customer_list = [{"id": customer.id, "text": customer.name} for customer in customers]
        return JsonResponse({"results": customer_list})

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles POST requests to add a customer to an opportunity.

        :param request: The HTTP request object containing the customer ID and document number.
        :return: JsonResponse indicating success or failure of the operation.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)

            customer_id = data.get("value")[0]
            document_number = data.get("document_number")[0]

            # Save customer into opportunity
            customer_obj = Customer.objects.get(id=customer_id)
            opportunity_obj = Opportunity.objects.get(document_number=document_number)
            opportunity_obj.customer = customer_obj
            opportunity_obj.save()

            messages.success(request, "Customer added successfully.")
            return JsonResponse({"code": 200, "status": "success", "message": "Customer added successfully."})

        except Exception as e:
            LOGGER.error(f"CustomerSearchView: {e}")
            messages.error(request, ERROR_RESPONSE["message"])
            return JsonResponse(ERROR_RESPONSE)


class TaskSearchView(ViewMixin):
    """
    View handles searching for tasks based on a search term and a specific document number,
    returning tasks that are not already mapped to the given opportunity.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles GET requests for searching tasks.

        :param request: The HTTP request object containing search parameters.
        :return: JsonResponse containing a list of tasks matching the search term
                that are not already mapped to the specified document number.
        """
        search_term = request.GET.get("q", "")
        document_number = request.GET.get("document_number", None)

        # Get mapped task IDs for the given document number
        mapped_task_ids = TaskMapping.objects.filter(
            opportunity__document_number=document_number, task_id__isnull=False
        ).values_list("task_id", flat=True)

        # Filter tasks based on search term and exclusion criteria
        tasks = (
            Task.objects.filter(name__icontains=search_term)
            .exclude(id__in=mapped_task_ids)
            .exclude(description__icontains="labor")[:15]  # Limit results to 15
        )

        task_list = [{"id": task.id, "text": task.name} for task in tasks]
        return JsonResponse({"results": task_list})


class LaborTaskSearchView(ViewMixin):
    """
    View handles searching for labor-related tasks based on a search term,
    returning a limited list of matching tasks.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles GET requests for searching labor tasks.

        :param request: The HTTP request object containing the search parameters.
        :return: JsonResponse containing a list of labor-related tasks matching the search term.
        """
        search_term = request.GET.get("q", "")

        # Filter tasks based on search term and include only those related to labor
        tasks = Task.objects.filter(name__icontains=search_term).filter(description__icontains="labor")[
            :15
        ]  # Limit results to 15
        task_list = [{"id": task.id, "text": task.name} for task in tasks]
        return JsonResponse({"results": task_list})


class LaborDescriptionView(ViewMixin):
    """
    View handles searching for labor cost descriptions based on a search term,
    returning a limited list of matching descriptions.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles GET requests for searching labor cost descriptions.

        :param request: The HTTP request object containing the search parameters.
        :return: JsonResponse containing a list of labor cost descriptions matching the search term.
        """
        search_term = request.GET.get("q", "")

        # Filter descriptions based on the search term
        descriptions = LabourCost.objects.filter(description__icontains=search_term)[:15]  # Limit results to 15

        description_list = [{"id": description.id, "text": description.description} for description in descriptions]
        description_list.insert(0, {"id": "Clear", "text": "--------------"})
        return JsonResponse({"results": description_list})

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles POST requests to retrieve details of a specific labor task.

        :param request: The HTTP request object containing the labor task ID.
        :return: JsonResponse containing details of the requested labor task.
        :raises LabourCost.DoesNotExist: If no labor task is found with the given ID.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            id = data["value"][0]

            labor_obj = LabourCost.objects.get(id=id)

            # Prepare the response data
            response_data = {
                "code": 200,
                "message": "success",
                "task_name": labor_obj.labour_task,
            }

            return JsonResponse(response_data)

        except LabourCost.DoesNotExist:
            LOGGER.error("Labor Cost not exists")
            return RESPONSE_CODE_0

        except Exception as e:
            LOGGER.error(f"LaborDescriptionView: {e}")
            return RESPONSE_CODE_0


class LaborTaskNameView(ViewMixin):
    """
    View handles searching for labor tasks by name and retrieving details
    for a specific labor task based on its ID.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles GET requests for searching labor tasks.

        :param request: The HTTP request object containing the search parameters.
        :return: JsonResponse containing a list of labor tasks matching the search term.
        """
        search_term = request.GET.get("q", "")

        # Filter labor tasks based on the search term
        labors = LabourCost.objects.filter(labour_task__icontains=search_term)[:15]  # Limit results to 15

        labor_list = [{"id": labor.id, "text": labor.labour_task} for labor in labors]
        labor_list.insert(0, {"id": "Clear", "text": "--------------"})
        return JsonResponse({"results": labor_list})

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles POST requests to retrieve details of a specific labor task.

        :param request: The HTTP request object containing the labor task ID.
        :return: JsonResponse containing details of the requested labor task.
        :raises LabourCost.DoesNotExist: If no labor task is found with the given ID.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            id = data["value"][0]

            labor_obj = LabourCost.objects.get(id=id)

            # Prepare the response data
            response_data = {
                "code": 200,
                "message": "success",
                "description": labor_obj.description,
            }

            return JsonResponse(response_data)

        except LabourCost.DoesNotExist:
            LOGGER.error("Labor Cost not exists")
            return RESPONSE_CODE_0

        except Exception as e:
            LOGGER.error(f"LaborTaskNameView: {e}")
            return RESPONSE_CODE_0


class TaskItemView(ViewMixin):
    """
    View handles searching for task item codes based on a search term
    and retrieving details for a specific assigned product.
    """

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles GET requests for searching task item codes.

        :param request: The HTTP request object containing the search parameters.
        :param task_id: The ID of the task for which to search item codes.
        :return: JsonResponse containing a list of item codes matching the search term.
        """
        search_term = request.GET.get("q", "")
        task_id = kwargs["task_id"]

        # Filter assigned products based on task ID and search term
        task_items = AssignedProduct.objects.filter(task_mapping__id=task_id, item_code__icontains=search_term).exclude(
            is_select=True
        )[
            :15
        ]  # Limit results to 15

        task_item_list = [{"id": t.id, "text": t.item_code} for t in task_items]
        return JsonResponse({"results": task_item_list})

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handles POST requests to retrieve details of a specific assigned product.

        :param request: The HTTP request object containing the assigned product ID.
        :return: JsonResponse containing details of the requested assigned product.
        :raises AssignedProduct.DoesNotExist: If no assigned product is found with the given ID.
        """
        try:
            body_unicode = request.body.decode("utf-8")
            data = urllib.parse.parse_qs(body_unicode)
            id = data["value"][0]

            assigned_prod = AssignedProduct.objects.get(id=id)

            return JsonResponse(
                {
                    "code": 200,
                    "message": "success",
                    "description": assigned_prod.description,
                    "quantity": assigned_prod.quantity,
                    "price": (
                        assigned_prod.standard_cost if assigned_prod.standard_cost else assigned_prod.vendor_quoted_cost
                    ),
                }
            )

        except AssignedProduct.DoesNotExist:
            LOGGER.error("Assigned product does not exist")
            return JsonResponse(ERROR_RESPONSE, status=404)
        except Exception as e:
            LOGGER.error(f"TaskItemView: {e}")
            return JsonResponse(ERROR_RESPONSE, status=400)
