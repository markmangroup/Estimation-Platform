from django.urls import path

from apps.rental.rent_process import views

app_name = "rent_process"

urlpatterns = [
    path("order-list", views.OrderListView.as_view(), name="order-list"),
    path("import-order", views.RentalOrderImportView.as_view(), name="rental-import-order"),
    path("order/create",views.OrderCreate.as_view(),name="order-create",),
    path("order/list/ajax", views.OrderListAjaxView.as_view(), name="order-list-ajax"),
    path("recurring-order/ajax", views.RecurringOrderListAjaxView.as_view(), name="recurring-order-ajax"),
    # path("return-order/ajax", views.ReturnOrderListAjaxView.as_view(), name="return-order-ajax"),
    path("order/<str:order_id>/overview",views.OrderOverview.as_view(),name="order-overview",),
    path("delivery/<str:delivery_id>/detail",views.DeliveryDetailview.as_view(),name="delivery-detail",),
    path("reccuring-order/<str:recurring_order_id>/overview",views.RecurringOrderOverview.as_view(),name="reccuring-order-overview",),
    path("order/<str:order_id>/process",views.OrderProcessview.as_view(),name="order-process",),
    path("create-delivery/<str:order_id>/", views.create_delivery_modal, name="create_delivery_modal"),
    path('create-delivery/', views.DeliveryCreateView.as_view(), name='create_delivery'),
    path("order/delete",views.OrderDelete.as_view(),name="order-delete",),
    path("reccuring-order/delete",views.RecurringOrderDelete.as_view(),name="reccuring-order-delete",),
    path("reccuring-order/<int:pk>/edit",views.RecurringOrderEdit.as_view(),name="reccuring-order-edit",),
    path('create-update-permission/', views.OrderPermissionCreateUpdateView.as_view(), name='order-permission'),

]
