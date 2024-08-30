from django.urls import path

from . import views

app_name = "user"

urlpatterns = [
    path("", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("authorization", views.AuthorizationView.as_view(), name="authorization"),
    path("create", views.AddUserView.as_view(), name="create-user"),
    path("user/<int:pk>/edit", views.UpdateUserView.as_view(), name="edit-user"),
    path("user/delete/ajax", views.DeleteUserView.as_view(), name="ajax-user-delete"),
    path("user/list/ajax", views.UserAjaxListView.as_view(), name="ajax-user-list"),
    path("redirect/", views.CheckUserAccountTypeView.as_view(), name="redirect"),
]
