"""
Final Document Stage Views
"""

from django.db.models import QuerySet

from apps.proposal.product.models import Product

from ..models import AssignedProduct, TaskMapping


class FinalDocument:
    """
    A class for handling final document generation and data retrieval,
    including material master data and cost variances.
    """

    @staticmethod
    def _get_new_material_master_data(document_number: str) -> QuerySet:
        """
        Retrieve new material master data for the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A queryset of assigned products that are not assigned.
        """
        task_mapping_ids = TaskMapping.objects.filter(opportunity__document_number=document_number).values_list(
            "id", flat=True
        )

        new_material_master_data = AssignedProduct.objects.filter(
            task_mapping__id__in=task_mapping_ids, is_assign=False
        )
        return new_material_master_data

    @staticmethod
    def _get_cost_variances_data(document_number: str) -> QuerySet:
        """
        Retrieve cost variances data for the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A queryset of assigned products with vendor quoted costs.
        """
        task_mapping_ids = TaskMapping.objects.filter(opportunity__document_number=document_number).values_list(
            "id", flat=True
        )

        cost_variances_data = AssignedProduct.objects.filter(
            task_mapping__id__in=task_mapping_ids, vendor_quoted_cost__isnull=False, vendor_quoted_cost__gt=0.0
        )
        return cost_variances_data

    @staticmethod
    def _get_netsuite_extract_data(document_number: str) -> list:
        """
        Retrieve a list of assigned products for the given document number.

        :param document_number: The unique identifier for the opportunity.
        :return: A list of assigned products associated with the opportunity.
        """
        task_mapping_objs = TaskMapping.objects.filter(opportunity__document_number=document_number)

        assigned_products = AssignedProduct.objects.filter(task_mapping__in=task_mapping_objs)
        assigned_products_data = []
        for assigned_product in assigned_products:
            code = assigned_product.item_code
            product = Product.objects.filter(
                display_name=code,
            ).first()
            assigned_products_data.append(
                {"assigned_product": assigned_product, "internal_id": product.internal_id if product else "-"}
            )
        return assigned_products_data
