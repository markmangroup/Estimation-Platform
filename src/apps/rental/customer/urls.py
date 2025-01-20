from django.urls import path

from apps.rental.customer import views

app_name = "rental_customer"

urlpatterns = [
    path("customer-list", views.CustomerListView.as_view(), name="customers"),
    path("customer/list/ajax", views.CustomerListAjaxView.as_view(), name="customer-list-ajax"),
    path("customer/<int:pk>/detail", views.CustomerDetailsView.as_view(), name="customer-detail"),
    path(
        "import-customer",
        views.CustomerCreateFromCSVFormView.as_view(),
        name="import-customer",
    ),
]
