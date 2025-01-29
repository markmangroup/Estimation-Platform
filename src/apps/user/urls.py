from django.urls import path

from . import rental_user, views

app_name = "user"

urlpatterns = [
    path("", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("redirect/", views.CheckUserAccountTypeView.as_view(), name="redirect"),
    path("proposal/authorization", views.AuthorizationView.as_view(), name="authorization"),
    path("proposal/create", views.AddUserView.as_view(), name="create-user"),
    path("proposal/user/<int:pk>/edit", views.UpdateUserView.as_view(), name="edit-user"),
    path("proposal/user/delete/ajax", views.DeleteUserView.as_view(), name="ajax-user-delete"),
    path("proposal/user/list/ajax", views.UserAjaxListView.as_view(), name="ajax-user-list"),
    path("rental/user/create", rental_user.AddUserView.as_view(), name="rental-create-user"),
    path("rental/user/<int:pk>/edit", rental_user.UpdateUserView.as_view(), name="rental-edit-user"),
    path("rental/user/delete/ajax", rental_user.DeleteUserView.as_view(), name="ajax-rental-user-delete"),
    path("rental/user/list/ajax", rental_user.UserAjaxListView.as_view(), name="ajax-rental-user-list"),
]
