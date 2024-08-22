from django.urls import path

from . import views

app_name = "customer"

urlpatterns = [
    path("customer", views.CustomerList.as_view(), name="customer-list"),
    path("customer/ajax", views.CustomerListAjaxView.as_view(), name="customer-list-ajax"),
    path(
        "import-customer",
        views.CustomerCreateFromCSVFormView.as_view(),
        name="import-customer",
    ),
]
