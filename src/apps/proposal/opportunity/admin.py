from django.contrib import admin

from .models import (
    AssignedProduct,
    Document,
    GlueAndAdditionalMaterial,
    MaterialList,
    Opportunity,
    PreliminaryMaterialList,
    SelectTaskCode,
    TaskMapping,
)

# Register your models here.

admin.site.register(Opportunity)
admin.site.register(SelectTaskCode)
admin.site.register(Document)

admin.site.register(MaterialList)
admin.site.register(GlueAndAdditionalMaterial)
admin.site.register(PreliminaryMaterialList)
admin.site.register(TaskMapping)
admin.site.register(AssignedProduct)
