from django.urls import path

from apps.rental.product import views

app_name = "rental_product"

urlpatterns = [
    path("products", views.RentalProductListView.as_view(), name="rental-product-list"),
    path("products/ajax", views.RentalProductListAjaxView.as_view(), name="rental-products-list-ajax"),
    path("import-products", views.RentalProductImportView.as_view(), name="rental-import-products"),
]
