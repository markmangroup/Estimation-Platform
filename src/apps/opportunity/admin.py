from django.contrib import admin

from .models import Document, Opportunity, SelectTaskCode

# Register your models here.

admin.site.register(Opportunity)
admin.site.register(SelectTaskCode)
admin.site.register(Document)
