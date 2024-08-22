"""laurel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include(("apps.proposal.urls", "proposal"), namespace="proposal")),
    path("", include(("apps.user.urls", "user"), namespace="user")),
    # path("", include(("apps.master_data.urls", 'user'), namespace="master_data")),
    path("", include(("apps.task.urls", "task"), namespace="task")),
    path("", include(("apps.product.urls", "product"), namespace="product")),
    path("", include(("apps.vendor.urls", "vendor"), namespace="vendor")),
    path("", include(("apps.customer.urls", "customer"), namespace="customer")),
    path("", include(("apps.labour_cost.urls", "labour_cost"), namespace="labour_cost")),
    path("", include(("apps.opportunity.urls", "opportunity"), namespace="opportunity")),
]

# API URLS
urlpatterns += [
    # API base url
    path("api/v1/", include("core.api_router")),
]
