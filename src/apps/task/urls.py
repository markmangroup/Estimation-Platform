from django.urls import path

from . import views

app_name = "task"


urlpatterns = [
    path("task", views.TaskListView.as_view(), name="task-list"),
    path("task/ajax", views.TaskListAjaxView.as_view(), name="task-list-ajax"),
    path("import-task", views.TaskImportView.as_view(), name="import-task"),
]
