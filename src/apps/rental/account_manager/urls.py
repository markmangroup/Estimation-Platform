from django.urls import path

from apps.rental.account_manager import views

app_name = "account_manager"

urlpatterns = [
    path("account-manager", views.AccountManagerView.as_view(), name="account-manager"),
    path("account-manager/list/ajax", views.AccountManagerListAjaxView.as_view(), name="account-manager-list-ajax"),
    path(
        "import-account-manager",
        views.AccountManagerCreateFromCSVFormView.as_view(),
        name="import-account-manager",
    ),
]
