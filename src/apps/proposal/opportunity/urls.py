from django.urls import path

from .views import (
    documents,
    generate_estimate,
    material_list,
    opportunity,
    proposal_creation,
    proposal_preview,
    search,
    select_task_code,
    task_mapping,
    upload_cad_file,
)

app_name = "opportunity"


urlpatterns = [
    # Opportunities URLS
    path("search", opportunity.SearchView.as_view(), name="search"),
    path("opportunity-list", opportunity.OpportunityList.as_view(), name="opportunity-list"),
    path(
        "opportunity-list/ajax",
        opportunity.OpportunityListAjaxView.as_view(),
        name="opportunity-list-ajax",
    ),
    path(
        "opportunity/<str:document_number>/detail",
        opportunity.OpportunityDetail.as_view(),
        name="opportunity-detail",
    ),
    path(
        "update-opportunity/ajax",
        opportunity.UpdateOpportunityView.as_view(),
        name="update-opportunity-ajax",
    ),
    path("update-stages", opportunity.UpdateStages.as_view(), name="update-stages"),
    path(
        "import-opportunity",
        opportunity.OpportunityCreateFromCSVFormView.as_view(),
        name="import-opportunity",
    ),
    path("filter/<str:column>/", opportunity.OpportunityFilterView.as_view(), name="opportunity-filter"),
    # Select Task Code URLS
    path("create/tasks", select_task_code.TaskManagementView.as_view(), name="create-task-code"),
    path(
        "select-task-model/<str:document_number>",
        select_task_code.TaskManagementView.as_view(),
        name="select-task-model",
    ),
    path(
        "selected-task-list/<str:document_number>/ajax",
        select_task_code.SelectedTaskListAjaxView.as_view(),
        name="ajax-selected-task-list",
    ),
    path(
        "update-selected-task/ajax",
        select_task_code.UpdateDescription.as_view(),
        name="update-selected-task-ajax",
    ),
    path(
        "delete-selected-task/ajax",
        select_task_code.DeleteSelectedTask.as_view(),
        name="ajax-delete-selected-task",
    ),
    # Document
    path(
        "document-list/<str:document_number>/ajax/<str:stage>/",
        documents.DocumentListAjaxView.as_view(),
        name="ajax-document-list",
    ),
    path("upload-document", documents.UploadDocument.as_view(), name="upload-document"),
    path(
        "opportunity-document-list/<str:document_number>/ajax",
        opportunity.OpportunityDocumentView.as_view(),
        name="opportunity-document-list",
    ),
    # Upload CAD file
    path("upload-cad-file", upload_cad_file.UploadCADFile.as_view(), name="upload-cad-file"),
    # Material List
    path(
        "material-list/<str:document_number>/ajax",
        material_list.MaterialListAjaxView.as_view(),
        name="material-list-ajax",
    ),
    path(
        "glue-and-additional-list/<str:document_number>/ajax",
        material_list.GlueAndAdditionalMaterialAjaxView.as_view(),
        name="glue-and-additional-list-list-ajax",
    ),
    path(
        "preliminary-material-list/<str:document_number>/ajax",
        material_list.PreliminaryMaterialListAjaxView.as_view(),
        name="preliminary-material-list-ajax",
    ),
    # Generate Estimation
    path(
        "task-product-data/<str:document_number>/ajax",
        generate_estimate.TaskProductDataView.as_view(),
        name="ajax-task-product-data",
    ),
    path(
        "<str:document_number>/estimate-table",
        generate_estimate.GenerateEstimateTable.as_view(),
        name="generate-estimate-table",
    ),
    path(
        "<int:task_id>/update-estimation-products/ajax",
        generate_estimate.UpdateEstimationProduct.as_view(),
        name="update-estimation-products-ajax",
    ),
    path(
        "<int:task_id>/update-estimation-labor/ajax",
        generate_estimate.UpdateEstimationLabor.as_view(),
        name="update-estimation-labor-ajax",
    ),
    path(
        "update-estimation-table/ajax",
        generate_estimate.UpdateEstimationTable.as_view(),
        name="update-estimation-table-ajax",
    ),
    # Task Mapping
    path(
        "assign-prod-labor/<str:document_number>/<int:task_id>",
        task_mapping.AssignProdLabor.as_view(),
        name="assign-prod-labor",
    ),
    path(
        "assign-prod/delete/ajax",
        task_mapping.DeleteAssignProdLabor.as_view(),
        name="assign-prod-delete-ajax",
    ),
    path(
        "assign-prod/update/ajax",
        task_mapping.UpdateAssignProdView.as_view(),
        name="assign-prod-update-ajax",
    ),
    path("add-task/<str:document_number>", task_mapping.AddTaskView.as_view(), name="add-task"),
    path("add-prod-row-ajax", task_mapping.AddProdRowView.as_view(), name="add-prod-row-ajax"),
    path(
        "assign-task-labor/<str:document_number>", task_mapping.AssignTaskLaborView.as_view(), name="assign-task-labor"
    ),
    path("update-sequence", task_mapping.UpdateSequenceView.as_view(), name="update-sequence"),
    # Proposal Creation
    path(
        "<str:document_number>/create-proposal/ajax",
        proposal_creation.CreateProposalView.as_view(),
        name="create-proposal-ajax",
    ),
    path(
        "task/delete/ajax",
        proposal_creation.DeleteTaskView.as_view(),
        name="task-delete-ajax",
    ),
    path(
        "group-name/update/ajax",
        proposal_creation.UpdateGroupName.as_view(),
        name="group-name-update-ajax",
    ),
    path('render-proposal-table/<str:document_number>/', proposal_creation.RenderProposalTableView.as_view(), name='render-proposal-table'),

    # Proposal Preview
    path(
        "add-items/ajax",
        proposal_preview.AddItemsView.as_view(),
        name="add-items-ajax",
    ),
    path(
        "add-description/ajax",
        proposal_preview.AddDescriptionView.as_view(),
        name="add-description-ajax",
    ),
    path(
        "include-items/ajax",
        proposal_preview.UpdateItemIncludeView.as_view(),
        name="include-items-ajax",
    ),
    path(
        "update-task-mapping/ajax",
        proposal_preview.UpdateTaskMappingView.as_view(),
        name="update-task-mapping-ajax",
    ),
    path(
        "update-proposal-item/ajax",
        proposal_preview.UpdateProposalItemsView.as_view(),
        name="update-proposal-item-ajax",
    ),
    path(
        "update-invoice/ajax",
        proposal_preview.UpdateInvoiceView.as_view(),
        name="update-invoice-ajax",
    ),
    # --KPI path
    path(
        "<str:document_number>/total-cost-breakdown-ajax",
        generate_estimate.TotalCostBreakdown.as_view(),
        name="total-cost-breakdown-ajax",
    ),
    path(
        "<str:document_number>/total-sale-breakdown-ajax",
        generate_estimate.TotalSaleBreakdown.as_view(),
        name="total-sale-breakdown-ajax",
    ),
    path(
        "<str:document_number>/total-gp-breakdown-ajax",
        generate_estimate.TotalGPBreakdown.as_view(),
        name="total-gp-breakdown-ajax",
    ),
    path(
        "<str:document_number>/total-gp-per-breakdown-ajax",
        generate_estimate.TotalGPPerBreakdown.as_view(),
        name="total-gp-per-breakdown-ajax",
    ),
    # --Search path
    path("item-code-search", search.ItemCodeSearchView.as_view(), name="item-code-search"),
    path("item-description-search", search.ItemDescriptionSearchView.as_view(), name="item-description-search"),
    path("vendor-search", search.VendorSearchView.as_view(), name="vendor-search"),
    path("customer-search", search.CustomerSearchView.as_view(), name="customer-search"),
    path("task-search", search.TaskSearchView.as_view(), name="task-search"),
    path("labor-task-search", search.LaborTaskSearchView.as_view(), name="labor-task-search"),
    path("labor-task-name-search", search.LaborTaskNameView.as_view(), name="labor-task-name-search"),
    path("labor-description-search", search.LaborDescriptionView.as_view(), name="labor-task-description-search"),
    path("task-item-search/<int:task_id>", search.TaskItemView.as_view(), name="task-item-search"),
]
