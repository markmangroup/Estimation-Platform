from django.contrib import admin
from .models import EstimationTemplate


@admin.register(EstimationTemplate)
class EstimationTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "industry",
        "project_type",
        "estimated_hours",
        "estimated_cost_min",
        "estimated_cost_max",
        "times_used",
        "is_public",
        "created_at",
    ]
    list_filter = ["industry", "project_type", "is_public"]
    search_fields = ["name", "description", "industry", "project_type"]
    readonly_fields = ["times_used", "created_at", "updated_at"]

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "description", "industry", "project_type", "thumbnail")
        }),
        ("Estimates", {
            "fields": ("estimated_hours", "estimated_cost_min", "estimated_cost_max")
        }),
        ("Template Data", {
            "fields": ("template_data",),
            "classes": ("collapse",)
        }),
        ("Visibility & Usage", {
            "fields": ("is_public", "times_used")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
