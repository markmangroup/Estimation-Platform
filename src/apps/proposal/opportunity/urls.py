from django.urls import path

from . import views

app_name = "opportunity"


urlpatterns = [
    path("search", views.SearchView.as_view(), name="search"),
    path("opportunity-list", views.OpportunityList.as_view(), name="opportunity-list"),
    path(
        "opportunity-list/ajax",
        views.OpportunityListAjaxView.as_view(),
        name="opportunity-list-ajax",
    ),
    path(
        "opportunity/<str:document_number>/detail",
        views.OpportunityDetail.as_view(),
        name="opportunity-detail",
    ),
    path(
        "update-opportunity/ajax",
        views.UpdateOpportunityView.as_view(),
        name="update-opportunity-ajax",
    ),
    path("update-stages", views.UpdateStages.as_view(), name="update-stages"),
    path(
        "import-opportunity",
        views.OpportunityCreateFromCSVFormView.as_view(),
        name="import-opportunity",
    ),
    path("create/tasks", views.TaskManagementView.as_view(), name="create-task-code"),
    path(
        "select-task-model/<str:document_number>",
        views.TaskManagementView.as_view(),
        name="select-task-model",
    ),
    path(
        "selected-task-list/<str:document_number>/ajax",
        views.SelectedTaskListAjaxView.as_view(),
        name="ajax-selected-task-list",
    ),
    path(
        "document-list/<str:document_number>/ajax/<str:stage>/",
        views.DocumentListAjaxView.as_view(),
        name="ajax-document-list",
    ),
    path("upload-document", views.UploadDocument.as_view(), name="upload-document"),
    path(
        "opportunity-document-list/<str:document_number>/ajax",
        views.OpportunityDocumentView.as_view(),
        name="opportunity-document-list",
    ),
    path("opportunity-list/ajax", views.OpportunityListAjaxView.as_view(), name="opportunity-list-ajax"),
    path("import-opportunity", views.OpportunityCreateFromCSVFormView.as_view(), name="import-opportunity"),
    path("filter/<str:column>/", views.OpportunityFilterView.as_view(), name="opportunity-filter"),
    path("upload-cad-file", views.UploadCADFile.as_view(), name="upload-cad-file"),
    path(
        "material-list/<str:document_number>/ajax",
        views.MaterialListAjaxView.as_view(),
        name="material-list-ajax",
    ),
    path(
        "glue-and-additional-list/<str:document_number>/ajax",
        views.GlueAndAdditionalMaterialAjaxView.as_view(),
        name="glue-and-additional-list-list-ajax",
    ),
    path(
        "preliminary-material-list/<str:document_number>/ajax",
        views.PreliminaryMaterialListAjaxView.as_view(),
        name="preliminary-material-list-ajax",
    ),
    path(
        "<str:document_number>/estimate-table",
        views.GenerateEstimateTable.as_view(),
        name="generate-estimate-table",
    ),
    path(
        "assign-prod-labor/<str:document_number>/<int:task_id>",
        views.AssignProdLabor.as_view(),
        name="assign-prod-labor",
    ),
    path(
        "assign-prod/delete/ajax",
        views.DeleteAssignProdLabor.as_view(),
        name="assign-prod-delete-ajax",
    ),
    path(
        "assign-prod/update/ajax",
        views.UpdateAssignProdView.as_view(),
        name="assign-prod-update-ajax",
    ),
    path("add-task/<str:document_number>", views.AddTaskView.as_view(), name="add-task"),
    path("add-prod-row-ajax", views.AddProdRowView.as_view(), name="add-prod-row-ajax"),
    path(
        "<int:task_id>/update-estimation-products/ajax",
        views.UpdateEstimationProduct.as_view(),
        name="update-estimation-products-ajax",
    ),
    path(
        "<int:task_id>/update-estimation-labor/ajax",
        views.UpdateEstimationLabor.as_view(),
        name="update-estimation-labor-ajax",
    ),
    path("update-estimation-table/ajax", views.UpdateEstimationTable.as_view(), name="update-estimation-table-ajax"),
    path("<str:document_number>/create-proposal/ajax", views.CreateProposalView.as_view(), name="create-proposal-ajax"),
    path(
        "task/delete/ajax",
        views.DeleteTaskView.as_view(),
        name="task-delete-ajax",
    ),
    path(
        "group-name/update/ajax",
        views.UpdateGroupName.as_view(),
        name="group-name-update-ajax",
    ),
    path(
        "add-items/ajax",
        views.AddItemsView.as_view(),
        name="add-items-ajax",
    ),
    path(
        "add-description/ajax",
        views.AddDescriptionView.as_view(),
        name="add-description-ajax",
    ),
    path(
        "include-items/ajax",
        views.UpdateItemIncludeView.as_view(),
        name="include-items-ajax",
    ),
    path(
        "update-task-mapping/ajax",
        views.UpdateTaskMappingView.as_view(),
        name="update-task-mapping-ajax",
    ),
    path(
        "update-proposal-item/ajax",
        views.UpdateProposalItemsView.as_view(),
        name="update-proposal-item-ajax",
    ),
    path(
        "update-invoice/ajax",
        views.UpdateInvoiceView.as_view(),
        name="update-invoice-ajax",
    ),
    # --KPI path
    path(
        "<str:document_number>/total-cost-breakdown-ajax",
        views.TotalCostBreakdown.as_view(),
        name="total-cost-breakdown-ajax",
    ),
    path(
        "<str:document_number>/total-sale-breakdown-ajax",
        views.TotalSaleBreakdown.as_view(),
        name="total-sale-breakdown-ajax",
    ),
    path(
        "<str:document_number>/total-gp-breakdown-ajax",
        views.TotalGPBreakdown.as_view(),
        name="total-gp-breakdown-ajax",
    ),
    path(
        "<str:document_number>/total-gp-per-breakdown-ajax",
        views.TotalGPPerBreakdown.as_view(),
        name="total-gp-per-breakdown-ajax",
    ),
    # --Search path
    path("item-code-search", views.ItemCodeSearchView.as_view(), name="item-code-search"),
    path("item-description-search", views.ItemDescriptionSearchView.as_view(), name="item-description-search"),
    path("vendor-search", views.VendorSearchView.as_view(), name="vendor-search"),
    path("customer-search", views.CustomerSearchView.as_view(), name="customer-search"),
    path("task-search", views.TaskSearchView.as_view(), name="task-search"),
    path("labor-task-search", views.LaborTaskSearchView.as_view(), name="labor-task-search"),
    path("labor-task-name-search", views.LaborTaskNameView.as_view(), name="labor-task-name-search"),
    path("labor-description-search", views.LaborDescriptionView.as_view(), name="labor-task-description-search"),
    path("task-item-search/<int:task_id>", views.TaskItemView.as_view(), name="task-item-search"),
]
