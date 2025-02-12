from collections import defaultdict

from django.db.models import Count, Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from apps.constants import ERROR_RESPONSE, LOGGER
from apps.mixin import ViewMixin

from ..models import (
    AssignedProduct,
    Invoice,
    Opportunity,
    ProposalCreation,
    TaskMapping,
)


class CreateProposalView(ViewMixin):
    """
    Create proposal view for managing proposals associated with opportunities.
    """

    template_name = "proposal/opportunity/stage/proposal_creation/create_proposal_form.html"

    def get(self, request, *args, **kwargs) -> HttpResponse:
        """
        Handle GET requests to render the proposal creation form.

        :param request: The HTTP request object.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments including 'document_number'.
        :return: Rendered HTML template with available task mappings.
        """
        document_number = self.kwargs["document_number"]

        # Fetch task mappings for the given document number
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number).exclude(
            Q(description="Labor") & Q(assign_to__isnull=False)
        )

        # Get the IDs of task mappings that are already in the ProposalCreation for the current opportunity
        existing_task_mapping_ids = ProposalCreation.objects.filter(
            opportunity__document_number=document_number
        ).values_list("task_mapping__id", flat=True)

        # Filter out task mappings that are already in ProposalCreation
        available_task_mappings = task_mappings.exclude(id__in=existing_task_mapping_ids)

        context = {"task_mapping_obj": available_task_mappings, "document_number": document_number}

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to create proposals based on selected tasks.

        :param request: The HTTP request object containing form data.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments including 'document_number'.
        :return: JsonResponse indicating success or failure.
        """
        document_number = self.kwargs["document_number"]
        tasks = request.POST.getlist("task")
        grp_name = request.POST.getlist("grp_name")

        if not (tasks and grp_name):
            return JsonResponse({"error": "Tasks and Group name are required."}, status=400)

        try:
            opportunity = Opportunity.objects.get(document_number=document_number)
            task_instances = TaskMapping.objects.filter(id__in=tasks)

            if task_instances.count() != len(tasks):
                return JsonResponse({"error": "One or more Task IDs are invalid."}, status=404)

            proposals = [
                ProposalCreation(opportunity=opportunity, group_name=grp_name[0], task_mapping=task)
                for task in task_instances
            ]
            ProposalCreation.objects.bulk_create(proposals)

            data = ProposalTable.generate_table(opportunity)
            data2 = TaskMappingTable.generate_table(opportunity)
            # Render the updated HTML for the task mapping table
            html = render(request, "proposal/opportunity/stage/proposal_creation/based_on_task.html", data)
            html2 = render(request, "proposal/opportunity/stage/task_mapping/task_table.html", data2)

            return JsonResponse(
                {
                    "modal_to_close": "modelSelectTask",
                    "message": "Proposal created successfully!",
                    "html": html.content.decode("utf-8"),
                    "html2": html2.content.decode("utf-8"),
                    "code": 201,
                },
                status=201,
            )

        except Opportunity.DoesNotExist:
            return JsonResponse({"error": "Opportunity not found."}, status=404)
        except Exception as e:
            LOGGER.error(f"Error: {e}")  # Log error for debugging
            return JsonResponse(ERROR_RESPONSE, status=500)


class DeleteTaskView(ViewMixin):
    """
    View for deleting task mapping objects.
    """

    def post(self, request) -> JsonResponse:
        """
        Handle POST requests to delete a task mapping by its ID.

        :param request: The HTTP request object containing the task mapping ID.
        :return: JsonResponse indicating the success of the deletion.
        """
        id = request.POST.get("id", None)
        task_type = request.POST.get("type", None)
        document_number = request.POST.get("document_number", None)

        opportunity = Opportunity.objects.get(document_number=document_number)

        if task_type == "proposal":
            ProposalCreation.objects.filter(id=id).delete()

        else:
            TaskMapping.objects.filter(id=id).delete()
            data = TaskMappingTable.generate_table(opportunity=opportunity)
            # Render the updated HTML for the task mapping table
            html = render(request, "proposal/opportunity/stage/task_mapping/tasks.html", data)

        _data = ProposalTable.generate_table(opportunity=opportunity)
        _html = render(request, "proposal/opportunity/stage/proposal_creation/proposal_task_main.html", _data)

        # messages.info(request, "Deleted Successfully")
        return JsonResponse(
            {
                "message": "Deleted Successfully.",
                "code": 200,
                "status": "success",
                "html": "" if task_type == "proposal" else html.content.decode("utf-8"),
                "_html": _html.content.decode("utf-8"),
            }
        )


class UpdateGroupName(ViewMixin):
    """
    View for updating the group name of proposal creations.
    """

    def post(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle POST requests to update the group name for specified proposal IDs.

        :param request: The HTTP request object containing the IDs, new group name, and document number.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        :return: JsonResponse indicating the success or failure of the update.
        """
        ids = request.POST.getlist("ids")
        group_name = request.POST.get("group_name")
        document_number = request.POST.get("document")

        if not ids or not group_name or not document_number:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "IDs, group name, and document number are required.",
                },
                status=400,
            )

        id_string = ids[0]
        id_list = [int(id.strip()) for id in id_string.split(",")]

        try:
            # Filter and update the proposal creation objects
            proposal_creation_obj = ProposalCreation.objects.filter(
                opportunity__document_number=document_number, id__in=id_list
            )
            updated_count = proposal_creation_obj.update(group_name=group_name)

            if updated_count == 0:
                LOGGER.error("No proposals were found for the given IDs.")
                return JsonResponse(ERROR_RESPONSE, status=404)

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Group name updated successfully",
                },
                status=200,
            )
        except Exception as e:
            LOGGER.error(f"ERROR: [UpdateGroupName] {e}")
            return JsonResponse(ERROR_RESPONSE, status=500)


class ProposalCreationData:

    @staticmethod
    def _get_proposal_creation(document_number: str) -> dict:
        """
        Retrieves proposals by document number and organizes them by group.

        :param document_number: The document number to filter proposals.
        :return: A dictionary with grouped proposals, task totals, and assigned products.
        """
        qs = ProposalCreation.objects.filter(opportunity__document_number=document_number).prefetch_related(
            Prefetch("task_mapping__assigned_products")
        )

        # Group proposals by their group name and count them
        grouped_proposals = qs.values("group_name").annotate(count=Count("id"))
        result = {
            group["group_name"]: {
                "proposals": [],
                "assigned_products": defaultdict(list),
                "task_totals": defaultdict(float),
                "main_total": 0.0,
                "proposal_ids": [],
            }
            for group in grouped_proposals
        }

        for proposal in qs:
            group_name = proposal.group_name
            result[group_name]["proposals"].append({"proposal": proposal})
            result[group_name]["proposal_ids"].append(proposal.id)

            # Fetch assigned products for the task
            assigned_products = proposal.task_mapping.assigned_products.all()
            task_object = proposal.task_mapping

            filtered_assigned_products = []

            for product in assigned_products:
                if product.is_select:  # Only include selected products
                    filtered_assigned_products.append(product)

                value = ProposalCreationData._calculate_product_value(task_object)

                result[group_name]["task_totals"][task_object] = value
                result[group_name]["main_total"] += value

            # Store the filtered assigned products
            result[group_name]["assigned_products"][task_object] = filtered_assigned_products

        # Convert defaultdicts to regular dicts for final output
        for group_data in result.values():
            group_data["assigned_products"] = dict(group_data["assigned_products"])
            group_data["task_totals"] = dict(group_data["task_totals"])

        return result

    @staticmethod
    def _calculate_product_value(product: TaskMapping) -> float:
        """
        Calculate the value of a product based on its costs.

        :param product: The product to calculate the value for.
        :return: The calculated value.
        """
        # quantity = product.quantity or 0
        # standard_cost = product.standard_cost or 0
        # local_cost = product.local_cost or 0

        # if quantity and standard_cost:
        #     return quantity * standard_cost
        # elif quantity and local_cost:
        #     return quantity * local_cost
        # else:
        #     return 0.0
        return product.mat_tax_labor

    @staticmethod
    def _get_proposal_totals(document_number: str) -> dict:
        """
        Calculates total quantities, prices, and costs for proposals linked to a document number.

        :param document_number: The document number used to filter proposals and invoices.
        :return: A dictionary with the grand total price and final total price (including taxes).
        """
        invoice = Invoice.objects.get(opportunity__document_number=document_number)
        proposal_creations = ProposalCreation.objects.filter(opportunity__document_number=document_number)

        task_mappings = TaskMapping.objects.filter(id__in=proposal_creations.values_list("task_mapping_id", flat=True))

        task_mapping_ids = task_mappings.values_list("id", flat=True)
        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}

        for task in task_mappings:
            task_assigned_products = assigned_products.filter(task_mapping_id=task.id)

            total_quantity = sum(product.quantity for product in task_assigned_products)

            total_price = sum(
                (product.standard_cost or product.vendor_quoted_cost or 0) * product.quantity
                for product in task_assigned_products
            )

            total_local_cost = sum(
                product.local_cost * product.quantity
                for product in task_assigned_products
                if product.local_cost is not None
            )

            tasks_with_products[task.id] = {
                "total_quantity": total_quantity,
                "total_price": total_price,
                "total_local_cost": total_local_cost,
            }

        total_price_sum = sum(v["total_price"] for v in tasks_with_products.values())
        total_local_cost_sum = sum(v["total_local_cost"] for v in tasks_with_products.values())
        grand_total_price = total_price_sum + total_local_cost_sum

        final_total_price = grand_total_price + invoice.sales_tax + invoice.other_tax + (invoice.tax_rate / 100)

        total_data = {
            "grand_total_price": round(grand_total_price, 2),
            "final_total_price": round(final_total_price, 2),
        }

        return total_data


# NOTE: Add data form handle circular import error
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


class TaskMappingTable:

    @staticmethod
    def generate_table(opportunity):
        total_tasks = TaskMappingData._get_total_tasks(opportunity.document_number)
        task_mapping_list = TaskMappingData._get_tasks(opportunity.document_number)
        task_mapping_labor_list = TaskMappingData._get_labour_tasks(opportunity.document_number)
        grand_total = TaskMappingData._get_task_total(opportunity.document_number)
        labor_task_total = TaskMappingData._get_labor_task_total(opportunity.document_number)

        data = {
            "total_tasks": total_tasks,
            "task_mapping_list": task_mapping_list,
            "task_mapping_labor_list": task_mapping_labor_list,
            "grand_total": grand_total,
            "labor_task_total": labor_task_total,
            "opportunity": opportunity,
        }
        return data


class ProposalTable:

    @staticmethod
    def generate_table(opportunity):
        """Generate proposal table"""
        grouped_proposals = ProposalCreationData._get_proposal_creation(opportunity.document_number)
        proposal_total = ProposalCreationData._get_proposal_totals(opportunity.document_number)

        data = {"grouped_proposals": grouped_proposals, "proposal_total": proposal_total, "opportunity": opportunity}

        return data
