from django.urls import path

from . import views

app_name = "product"


urlpatterns = [
    path("products", views.ProductListView.as_view(), name="product-list"),
    path("products/ajax", views.ProductListAjaxView.as_view(), name="products-list-ajax"),
    path("import-products", views.ProductImportView.as_view(), name="import-products"),
]
