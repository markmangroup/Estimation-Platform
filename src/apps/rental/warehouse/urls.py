from django.urls import path

from apps.rental.warehouse import views

app_name = "warehouse"

urlpatterns = [
    path("warehouse", views.WarehouseView.as_view(), name="warehouse"),
    path("warehouse/<int:pk>/detail", views.WarehouseDetailsView.as_view(), name="warehouse_detail"),
    path("warehouse/list/ajax", views.WarehouseListAjaxView.as_view(), name="warehouse-list-ajax"),
    path(
        "import-warehouse",
        views.WarehouseCreateFromCSVFormView.as_view(),
        name="import-warehouse",
    ),
]
