from django.urls import include, path

from . import views

app_name = "rental"


warehouse_urls = [
    path("order-overview", views.OrderOverview.as_view(), name="order_overview"),
    path("home", views.MapView.as_view(), name="map_view"),
    path(
        "warehouse_products",
        views.WarehouseProducts.as_view(),
        name="warehouse_products",
    ),
    path("user_list", views.UserList.as_view(), name="user_list"),
    path("order_list", views.OrderList.as_view(), name="order_list"),
    path("recurring_order", views.RecurringOrder.as_view(), name="recurring_order"),
    path("order-detail", views.OrderDetail.as_view(), name="order_detail"),
    path("order", views.Order.as_view(), name="order"),
    path("return_order", views.ReturnOrder.as_view(), name="return_order"),
    path("express_delivery", views.ExpressDelivery.as_view(), name="express_delivery"),
    path("delivery_list", views.Delivery.as_view(), name="delivery_list"),
    #     path("reports", views.Reports.as_view(), name="reports"),
    # path("workflow", views.Workflow.as_view(), name="workflow"),
    path("stock_adjustment", views.StockAdjustment.as_view(), name="stock_adjustment"),
    path(
        "return_delivery_list",
        views.ReturnDelivery.as_view(),
        name="return_delivery_list",
    ),
    path("inbox", views.InboxView.as_view(), name="inbox"),
]

reports_urls = [
    path("reports", views.ReportsView.as_view(), name="reports"),
    path("revenue_report", views.RevenueReport.as_view(), name="revenue_report"),
    path("stock_report", views.StockReport.as_view(), name="stock_report"),
    path(
        "stock_movement_report",
        views.StockMovementReport.as_view(),
        name="stock_movement_report",
    ),
    path("in_transit_report", views.InTransitReport.as_view(), name="in_transit_report"),
    path(
        "planned_removal_report",
        views.PlannedRemovalReport.as_view(),
        name="planned_removal_report",
    ),
    path(
        "planned_deliveries_report",
        views.PlannedDeliveriesReport.as_view(),
        name="planned_deliveries_report",
    ),
    path(
        "usages_of_equipment_report",
        views.UsageOfEquipmentReport.as_view(),
        name="usages_of_equipment_report",
    ),
]

urlpatterns = (
    [
        # path("dashboard", views.Dashboard.as_view(), name="dashboard"),
        path("coming_soon", views.ComingSoon.as_view(), name="coming_soon"),
        path("", include(("apps.rental.customer.urls", "rental_customer"), namespace="rental_customer")),
        path("", include(("apps.rental.product.urls", "rental_product"), namespace="rental_product")),
        path("", include(("apps.rental.warehouse.urls", "warehouse"), namespace="warehouse")),
        path("", include(("apps.rental.account_manager.urls", "account_manager"), namespace="account_manager")),
        path("", include(("apps.rental.workflow.urls", "rental_workflow"), namespace="rental_workflow")),
        path("", include(("apps.rental.stock_management.urls", "stock_management"), namespace="stock_management")),
        path("", include(("apps.rental.rent_process.urls", "rent_process"), namespace="rent_process")),
    ]
    + warehouse_urls
    + reports_urls
)
