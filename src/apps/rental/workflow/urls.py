from django.urls import path

from apps.rental.workflow import views

app_name = "rental_workflow"

urlpatterns = [
    path("workflow", views.Workflow.as_view(), name="workflow"),
]
