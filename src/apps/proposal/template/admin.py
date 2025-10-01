from django.contrib import admin
from .models import EstimationTemplate, TemplateTask, TemplateProduct, TemplateLabour


class TemplateTaskInline(admin.TabularInline):
    model = TemplateTask
    extra = 1
    fields = ["task", "default_hours", "sequence", "hours_formula"]
    autocomplete_fields = ["task"]


class TemplateProductInline(admin.TabularInline):
    model = TemplateProduct
    extra = 1
    fields = ["product", "template_task", "default_quantity", "markup_percent", "sequence"]
    autocomplete_fields = ["product", "template_task"]


class TemplateLabourInline(admin.TabularInline):
    model = TemplateLabour
    extra = 1
    fields = ["labour_cost", "template_task", "default_hours", "is_local", "sequence"]
    autocomplete_fields = ["labour_cost", "template_task"]


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
        "schema_version",
        "created_at",
    ]
    list_filter = ["industry", "project_type", "is_public", "organization"]
    search_fields = ["name", "description", "industry", "project_type"]
    readonly_fields = ["times_used", "created_at", "updated_at"]
    inlines = [TemplateTaskInline, TemplateProductInline, TemplateLabourInline]

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "description", "industry", "project_type", "thumbnail")
        }),
        ("Estimates", {
            "fields": ("estimated_hours", "estimated_cost_min", "estimated_cost_max")
        }),
        ("Defaults", {
            "fields": ("default_margin_percent", "default_tax_rate", "parameters")
        }),
        ("Multi-Tenant", {
            "fields": ("organization", "is_public"),
            "classes": ("collapse",)
        }),
        ("Metadata", {
            "fields": ("schema_version", "times_used", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(TemplateTask)
class TemplateTaskAdmin(admin.ModelAdmin):
    list_display = ["template", "task", "default_hours", "sequence"]
    list_filter = ["template"]
    search_fields = ["template__name", "task__name"]
    autocomplete_fields = ["template", "task"]


@admin.register(TemplateProduct)
class TemplateProductAdmin(admin.ModelAdmin):
    list_display = ["template", "product", "default_quantity", "markup_percent", "sequence"]
    list_filter = ["template"]
    search_fields = ["template__name", "product__description"]
    autocomplete_fields = ["template", "product", "template_task"]


@admin.register(TemplateLabour)
class TemplateLabourAdmin(admin.ModelAdmin):
    list_display = ["template", "labour_cost", "default_hours", "is_local", "sequence"]
    list_filter = ["template", "is_local"]
    search_fields = ["template__name", "labour_cost__labour_task"]
    autocomplete_fields = ["template", "labour_cost", "template_task"]
