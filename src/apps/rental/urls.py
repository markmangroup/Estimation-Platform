from django.urls import path

from . import views

app_name = "rental"


warehouse_urls = [
    path("account_managers_list", views.AccountManagersList.as_view(), name="account_managers_list"),
    path("order-overview", views.OrderOverview.as_view(), name="order_overview"),
    path("home", views.MapView.as_view(), name="map_view"),
    path("customer_list", views.CustomerListView.as_view(), name="customers"),
    path("customer_detail", views.CustomerDetail.as_view(), name="customer_detail"),
    path("warehouse_list", views.WarehouseList.as_view(), name="warehouse_list"),
    path("warehouse_detail", views.WarehouseDetailView.as_view(), name="warehouse_detail"),
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
    path("workflow", views.Workflow.as_view(), name="workflow"),
    path("stock_adjustment", views.StockAdjustment.as_view(), name="stock_adjustment"),
    path(
        "return_delivery_list",
        views.ReturnDelivery.as_view(),
        name="return_delivery_list",
    ),
    path("inbox", views.InboxView.as_view(), name="inbox"),
    path("search", views.SearchView.as_view(), name="search"),
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
    ]
    + warehouse_urls
    + reports_urls
)
