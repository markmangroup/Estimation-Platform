from django.db.models import Q
from django.http import JsonResponse

from apps.rental.mixin import CustomDataTableMixin

from ..models import GlueAndAdditionalMaterial, MaterialList, PreliminaryMaterialList


class MaterialListAjaxView(CustomDataTableMixin):
    """AJAX view to list materials in a DataTable format."""

    model = MaterialList

    def get_queryset(self):
        document_number = self.kwargs.get("document_number")
        qs = MaterialList.objects.filter(opportunity__document_number=document_number)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(quantity__icontains=self.search)
                | Q(description__icontains=self.search)
                | Q(item_number__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "quantity": o.quantity,
                    "description": o.description,
                    "item_number": o.item_number,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class GlueAndAdditionalMaterialAjaxView(CustomDataTableMixin):
    """AJAX view to list glue and additional material in a DataTable format."""

    model = GlueAndAdditionalMaterial

    def get_queryset(self):
        document_number = self.kwargs.get("document_number")
        qs = GlueAndAdditionalMaterial.objects.filter(opportunity__document_number=document_number)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(quantity__icontains=self.search)
                | Q(description__icontains=self.search)
                | Q(item_number__icontains=self.search)
                | Q(category__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "quantity": o.quantity,
                    "description": o.description,
                    "item_number": o.item_number,
                    "category": o.category,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)


class PreliminaryMaterialListAjaxView(CustomDataTableMixin):
    """AJAX view to list preliminary material in a DataTable format."""

    model = PreliminaryMaterialList

    def get_queryset(self):
        document_number = self.kwargs.get("document_number")
        qs = PreliminaryMaterialList.objects.filter(opportunity__document_number=document_number)
        return qs

    def filter_queryset(self, qs):
        """Return the list of items for this view."""
        if self.search:
            return qs.filter(
                Q(irricad_imported_quantities__icontains=self.search)
                | Q(glue_and_additional_mat_quantities__icontains=self.search)
                | Q(combined_quantities_from_both_import__icontains=self.search)
                | Q(description__icontains=self.search)
                | Q(item_number__icontains=self.search)
                | Q(category__icontains=self.search)
                | Q(bag_bundle_quantity__icontains=self.search)
            )
        return qs

    def prepare_results(self, qs):
        # Create row data for datatables
        data = []
        for o in qs:
            data.append(
                {
                    "irricad_imported_quantities": o.irricad_imported_quantities,
                    "glue_and_additional_mat_quantities": o.glue_and_additional_mat_quantities,
                    "combined_quantities_from_both_import": o.combined_quantities_from_both_import,
                    "description": o.description,
                    "item_number": o.item_number,
                    "category": o.category,
                    "bag_bundle_quantity": o.bag_bundle_quantity,
                }
            )
        return data

    def get(self, request, *args, **kwargs):
        context_data = self.get_context_data(request)
        return JsonResponse(context_data)
