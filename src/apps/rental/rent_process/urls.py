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
    path('ajax/customer-address/', views.CustomerAddressAjaxView.as_view(), name='customer-address-ajax'),
    path("order/update/<int:pk>",views.OrderUpdateView.as_view(),name="order-update",),
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
    # path("update-delivery-stock/",views.DeliveryStockUpdateView.as_view(),name="update_delivery_stock"),
    # Stage 4 Delivered To Customer
    path(
        "order/<str:order_id>/ajax/delivered-to-customer-list-ajax/",
        views.DeliveredToCustomerListAjaxView.as_view(),
        name="delivered-to-customer-list-ajax",
    ),
    path(
        "delivered-to-customer-update-date/",
        views.UpdateDeliveredToCustomerDateView.as_view(),
        name="delivered_to_customer_update_date",
    ),
    path(
        "change-delivery-delivered-to-customer-status/",
        views.UpdateDeliveredToCustomerStatusView.as_view(),
        name="change_delivery_delivered_to_customer_status",
    ),
    path(
        "create-return-delivery/<str:order_id>/",
        views.ReturnDeliveryModalView.as_view(),
        name="create_return_delivery_modal",
    ),
    path("return-delivery/", views.CreateReturnDeliveryView.as_view(), name="create_return_delivery"),
    path("order/<str:order_id>/ajax/return-delivery-list-ajax/",views.CreateReturnDeliveryListAjaxView.as_view(),name="return_delivery_list_ajax"),
    path("update-return-delivery-site/", views.UpdateReturnDeliverySiteView.as_view(), name="update_return_delivery_site"),
    path("update-return-delivery-qty/", views.UpdateReturnDeliveryQtyView.as_view(), name="update_return_delivery_qty"),
    path("return-delivery/edit/<str:pk>/", views.ReturnDeliveryUpdateView.as_view(), name="return-delivery-edit"),


    #Stage 6 Return Pickup 
    path("order/<str:order_id>/ajax/return-pickup-list-ajax/",views.ReturnPickupListAjaxView.as_view(),name="return-pickup-list-ajax"),
    path("update-return-pickup-date/", views.UpdateReturnPickupDateView.as_view(), name="update_return_pickup_date"),
    path("change-delivery-return-pickup-status/",views.ReturnPickupStatusView.as_view(),name="change_return_pickup_status"),

    #Stage 7 Check In  
    path("order/<str:order_id>/ajax/check-in-list-ajax/",views.CheckInListAjaxView.as_view(),name="check-in-list-ajax"),
    path("update-check-in-date/", views.UpdateCheckInDateView.as_view(), name="update_check_in_date"),
    path("return-delivery-item/update/<int:pk>/",views.ReturnDeliveryItemMismatchUpdateView.as_view(),name="return-delivery-item-update"),
    path("update-check-in-status/<str:order_id>/", views.UpdateCheckInStatusView.as_view(), name="update_check_in_status"),

    #Stage 7 Inspection
    path("order/<str:order_id>/ajax/inspection-list-ajax/",views.InspectionListAjaxView.as_view(),name="inspection-list-ajax"),
    path("update-inspection-date/", views.UpdateInspectionDateView.as_view(), name="update_inspection_date"),
    path("return-delivery-item/update/<int:pk>/",views.ReturnDeliveryItemMismatchUpdateView.as_view(),name="return-delivery-item-update"),
    path("mark-inspection-completed-ajax/<int:pk>/",views.MarkInspectionCompletedAjaxView.as_view(),name="mark-inspection-completed-ajax"),
    path("search/customers/", views.CustomerSearchView.as_view(), name="search_customers"),
    path("search/account-managers/", views.AccountManagerSearchView.as_view(), name="search_account_managers"),
    path("search/pick-up-location/", views.PickUpLocationSearchView.as_view(), name="search_pick_up_location"),
    path("search/rental-product/id/", views.RentalProductIDSearchView.as_view(), name="search_rental_product_id"),
    path("search/rental-product/name/", views.RentalProductNameSearchView.as_view(), name="search_rental_product_name"),


    
]
