from django.urls import path

from . import views

app_name = "opportunity"


urlpatterns = [
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
        "generate_estimate_table",
        views.GenerateEstimateTable.as_view(),
        name="generate_estimate_table",
    ),
]
