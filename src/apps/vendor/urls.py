from django.urls import path

from . import views

app_name = "vendor"


urlpatterns = [
    path("vendor", views.VendorListView.as_view(), name="vendor-list"),
    path("vendor/list/ajax", views.VendorListAjaxView.as_view(), name="vendor-list-ajax"),
    path("import-vendor", views.VendorImportView.as_view(), name="import-vendor"),
]
