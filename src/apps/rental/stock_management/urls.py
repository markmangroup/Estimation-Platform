from django.urls import path

from apps.rental.stock_management import views

app_name = "stock_management"

urlpatterns = [
    path("stock-management", views.StockManagementListView.as_view(), name="rental-stock-management-list"),
    path(
        "stock-management/ajax", views.StockManagementListAjaxView.as_view(), name="rental-stock-management-list-ajax"
    ),
    path("stock-edit/<int:pk>", views.StockManagementEditView.as_view(), name="rental-stock-management-edit"),
    path("import-mass-stock/", views.MassStockUploadView.as_view(), name="import-mass_stock"),
    path("save-mass-stock/", views.SaveMassStockAdjustmentsView.as_view(), name="save_mass_stock_adjustments"),
]
