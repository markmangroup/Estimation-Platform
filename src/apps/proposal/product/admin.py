from django.contrib import admin

from .models import AdditionalMaterials, Product

admin.site.register(Product)
admin.site.register(AdditionalMaterials)
