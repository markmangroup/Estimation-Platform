from django.urls import path

from . import views

app_name = "product"


urlpatterns = [
    path("products", views.ProductListView.as_view(), name="product-list"),
    path("products/ajax", views.ProductListAjaxView.as_view(), name="products-list-ajax"),
    path("import-products", views.ProductImportView.as_view(), name="import-products"),
    path("additional-material/ajax", views.AdditionalMaterialAjaxView.as_view(), name="additional-material-ajax"),
    path("import-additional-material", views.AdditionalMaterialImportView.as_view(), name="import-additional-material"),
]
