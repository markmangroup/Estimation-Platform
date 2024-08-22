from django.urls import path

from . import views

app_name = "labour_cost"


urlpatterns = [
    path("labour-cost/", views.LabourCostList.as_view(), name="labour-cost-list"),
    path(
        "labour-cost-list/ajax",
        views.LabourCostListAjaxView.as_view(),
        name="labour-cost-list-ajax",
    ),
    path(
        "import-labour-cost",
        views.LabourCostCreateFromCSVFormView.as_view(),
        name="import-labour-cost",
    ),
]
