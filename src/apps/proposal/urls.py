"""
Proposal App Configuration
"""

from django.urls import include, path

urlpatterns = [
    path("", include(("apps.proposal.task.urls", "task"), namespace="task")),
    path("", include(("apps.proposal.product.urls", "product"), namespace="product")),
    path("", include(("apps.proposal.vendor.urls", "vendor"), namespace="vendor")),
    path("", include(("apps.proposal.customer.urls", "customer"), namespace="customer")),
    path("", include(("apps.proposal.labour_cost.urls", "labour_cost"), namespace="labour_cost")),
    path("", include(("apps.proposal.opportunity.urls", "opportunity"), namespace="opportunity")),
]
