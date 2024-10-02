from collections import defaultdict

from django.contrib import messages
from django.db.models import Count, Prefetch
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse

from apps.constants import ERROR_RESPONSE
from apps.rental.mixin import ViewMixin

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

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to render the proposal creation form.

        :param request: The HTTP request object.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments including 'document_number'.
        :return: Rendered HTML template with available task mappings.
        """
        document_number = self.kwargs["document_number"]

        # Fetch task mappings for the given document number
        task_mappings = TaskMapping.objects.filter(opportunity__document_number=document_number)

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

            messages.success(request, "Proposal created successfully!")
            return JsonResponse(
                {
                    "success_url": reverse("proposal_app:opportunity:opportunity-detail", args=(document_number,)),
                    "modal_to_close": "modelSelectTask",
                },
                status=201,
            )

        except Opportunity.DoesNotExist:
            return JsonResponse({"error": "Opportunity not found."}, status=404)
        except Exception as e:
            print(f"Error: {e}")  # Log error for debugging
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
        task_mapping_id = request.POST.get("id")
        TaskMapping.objects.filter(id=task_mapping_id).delete()
        messages.info(request, "Deleted Successfully")
        return JsonResponse({"message": "Deleted Successfully.", "code": 200, "status": "success"})


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
                print("Error: No proposals were found for the given IDs.")
                return JsonResponse(ERROR_RESPONSE, status=404)

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Group name updated successfully",
                },
                status=200,
            )
        except Exception as e:
            print(f"ERROR: [UpdateGroupName][2003] {e}")
            return JsonResponse(ERROR_RESPONSE, status=500)


class ProposalCreationData:

    @staticmethod
    def _get_proposal_creation(document_number):
        qs = ProposalCreation.objects.filter(opportunity__document_number=document_number).prefetch_related(
            Prefetch("task_mapping__assigned_products")
        )

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
            result[group_name]["proposals"].append(
                {
                    "proposal": proposal,
                }
            )

            # Add the ProposalCreation ID to the list
            result[group_name]["proposal_ids"].append(proposal.id)

            # Fetch all assigned products for the task
            assigned_products = proposal.task_mapping.assigned_products.all()  # Get all assigned products
            task_object = proposal.task_mapping

            # Initialize an empty list for filtered assigned products
            filtered_assigned_products = []

            for product in assigned_products:
                if product.is_select:  # Only include selected products
                    filtered_assigned_products.append(product)

                    # Calculate value based on available costs
                    quantity = product.quantity or 0
                    standard_cost = product.standard_cost or 0
                    local_cost = product.local_cost or 0

                    if quantity and standard_cost:
                        value = quantity * standard_cost
                    elif quantity and local_cost:
                        value = quantity * local_cost
                    else:
                        value = 0

                    result[group_name]["task_totals"][task_object] += value
                    result[group_name]["main_total"] += value

            # Store the filtered assigned products
            result[group_name]["assigned_products"][task_object] = filtered_assigned_products

        for group_data in result.values():
            group_data["assigned_products"] = dict(group_data["assigned_products"])
            group_data["task_totals"] = dict(group_data["task_totals"])

        return result

    @staticmethod
    def _get_proposal_totals(document_number):

        invoice = Invoice.objects.get(opportunity__document_number=document_number)

        proposal_creations = ProposalCreation.objects.filter(opportunity__document_number=document_number)

        # Get the related TaskMapping objects
        task_mappings = TaskMapping.objects.filter(id__in=proposal_creations.values_list("task_mapping_id", flat=True))

        # Include all task mappings
        filtered_task_mappings = task_mappings

        # Get task mapping IDs for the assigned products
        task_mapping_ids = filtered_task_mappings.values_list("id", flat=True)

        # Retrieve assigned products linked to these task mappings
        assigned_products = AssignedProduct.objects.filter(task_mapping_id__in=task_mapping_ids)

        tasks_with_products = {}
        for task in filtered_task_mappings:
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

        # Calculate grand total price correctly
        total_price_sum = sum(v["total_price"] for v in tasks_with_products.values())
        print(f"total_price_sum {type(total_price_sum)}: {total_price_sum}")
        total_local_cost_sum = sum(v["total_local_cost"] for v in tasks_with_products.values())
        print(f"total_local_cost_sum {type(total_local_cost_sum)}: {total_local_cost_sum}")
        grand_total_price = total_price_sum + total_local_cost_sum
        print("grand_total_price", grand_total_price)

        # final price with taxes
        final_total_price = grand_total_price + invoice.sales_tax + invoice.other_tax + (invoice.tax_rate / 100)

        total_data = {
            "grand_total_price": round(grand_total_price, 2),
            "final_total_price": round(final_total_price, 2),
        }

        return total_data
