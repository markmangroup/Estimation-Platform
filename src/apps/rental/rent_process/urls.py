from django.urls import path

from apps.rental.rent_process import views

app_name = "rent_process"

urlpatterns = [
    path("order-list", views.OrderListView.as_view(), name="order-list"),
    path("import-order", views.RentalOrderImportView.as_view(), name="rental-import-order"),
    path("order/list/ajax", views.OrderListAjaxView.as_view(), name="order-list-ajax"),
    # path("recurring-order/ajax", views.RecurringOrderListAjaxView.as_view(), name="recurring-order-ajax"),
    # path("return-order/ajax", views.ReturnOrderListAjaxView.as_view(), name="return-order-ajax"),
    path(
        "order/<str:order_id>/detail",
        views.OrderDetailview.as_view(),
        name="order-detail",
    ),
    path(
        "delivery/<str:delivery_id>/detail",
        views.DeliveryDetailview.as_view(),
        name="delivery-detail",
    ),
    # path("reccuring-order/<str:recurring_order_id>/detail",views.RecurringOrderDetail.as_view(),name="reccuring-order-detail",),
]
