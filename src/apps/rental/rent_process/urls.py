from django.urls import path

from apps.rental.rent_process import views

app_name = "rent_process"

urlpatterns = [
    path("order-list", views.OrderListView.as_view(), name="order-list"),
    path("import-order", views.RentalOrderImportView.as_view(), name="rental-import-order"),
    path(
        "order/create",
        views.OrderCreate.as_view(),
        name="order-create",
    ),
    path("order/list/ajax", views.OrderListAjaxView.as_view(), name="order-list-ajax"),
    path(
        "order/<str:order_id>/overview",
        views.OrderOverview.as_view(),
        name="order-overview",
    ),
    path(
        "order/<str:order_id>/process",
        views.OrderProcessview.as_view(),
        name="order-process",
    ),
    path("order/<str:order_id>/", views.overview_model, name="overview_model"),
    path(
        "order/delete",
        views.OrderDelete.as_view(),
        name="order-delete",
    ),
    path(
        "order/<str:delivery_id>/history",
        views.OrderHistory.as_view(),
        name="order-history",
    ),
    # Recuriing Order
    path("recurring-order/ajax", views.RecurringOrderListAjaxView.as_view(), name="recurring-order-ajax"),
    path(
        "reccuring-order/<str:recurring_order_id>/overview",
        views.RecurringOrderOverview.as_view(),
        name="reccuring-order-overview",
    ),
    path(
        "reccuring-order/delete",
        views.RecurringOrderDelete.as_view(),
        name="reccuring-order-delete",
    ),
    path(
        "reccuring-order/<str:pk>/edit",
        views.RecurringOrderEdit.as_view(),
        name="reccuring-order-edit",
    ),
    # Return Order
    path("return-order/ajax", views.ReturnOrderListAjaxView.as_view(), name="return-order-ajax"),
    path(
        "return-order/<str:pk>/edit",
        views.ReturnOrderEdit.as_view(),
        name="return-order-edit",
    ),
    # delivery
    path(
        "delivery/<str:delivery_id>/detail",
        views.DeliveryDetailview.as_view(),
        name="delivery-detail",
    ),
    path("create-delivery/<str:order_id>/", views.create_delivery_modal, name="create_delivery_modal"),
    path("create-delivery/", views.DeliveryCreateView.as_view(), name="create_delivery"),
    # Permissions
    path("create-update-permission/", views.OrderPermissionCreateUpdateView.as_view(), name="order-permission"),
    # Document
    path("upload-document", views.UploadDocument.as_view(), name="upload-document"),
    path(
        "document-list/<str:order_id>/ajax/<str:stage>/",
        views.DocumentListAjaxView.as_view(),
        name="ajax-document-list",
    ),
    path("update-stages", views.UpdateStages.as_view(), name="update-stages"),
    path(
        "order/<str:order_id>/ajax/checkout-ajax/",
        views.DeliveryCheckoutListAjaxView.as_view(),
        name="checkout-list-ajax",
    ),
    path(
        "change-delivery-checkout-status/",
        views.CheckDeliveryStatusView.as_view(),
        name="change_delivery_checkout_status",
    ),
    path("update-checkout-date/", views.UpdateCheckoutDateView.as_view(), name="update_checkout_date"),
    path("update-quantity/", views.UpdateQuantityView.as_view(), name="update_quantity"),
    path(
        "ajax/create_deliveries/<str:order_id>", views.DeliveryListAjaxView.as_view(), name="create_delivery_list_ajax"
    ),
    path("ajax/pickupticket/<str:order_id>", views.PickupTicketListAjaxView.as_view(), name="pickup_ticket_list_ajax"),
    path("update-pickup-date/", views.UpdatePickupDateView.as_view(), name="update_pickup_date"),
]
