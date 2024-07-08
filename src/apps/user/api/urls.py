# -*- coding: utf-8 -*-

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views


# Routers provide an easy way of automatically determining the URL conf.
router = DefaultRouter()


urlpatterns = [path("", include(router.urls))]
