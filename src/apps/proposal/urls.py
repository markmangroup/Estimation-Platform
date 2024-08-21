from django.urls import path
from . import views

app_name = "proposal"


warehouse_urls = [
    path("home", views.MapView.as_view(), name="map_view"),
    path("customer_list", views.CustomerListView.as_view(), name="customers"),
    path("customer_detail", views.CustomerDetail.as_view(), name="customer_detail"),
    path("warehouse_list", views.WarehouseList.as_view(), name="warehouse_list"),
    path("warehouse_detail", views.WarehouseDetailView.as_view(), name="warehouse_detail"),
    path("warehouse_products", views.WarehouseProducts.as_view(), name="warehouse_products"),
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
    path("return_delivery_list", views.ReturnDelivery.as_view(), name="return_delivery_list"),
    path("inbox", views.InboxView.as_view(), name="inbox")
]

reports_urls = [
     path("reports", views.ReportsView.as_view(), name="reports"),
     path("revenue_report", views.RevenueReport.as_view(), name="revenue_report"),
     path("stock_report", views.StockReport.as_view(), name="stock_report"),
     path("stock_movement_report", views.StockMovementReport.as_view(), name="stock_movement_report"),
     path("in_transit_report", views.InTransitReport.as_view(), name="in_transit_report"),
     path("planned_removal_report", views.PlannedRemovalReport.as_view(), name="planned_removal_report"),
     path("planned_deliveries_report", views.PlannedDeliveriesReport.as_view(), name="planned_deliveries_report"),
     path("usages_of_equipment_report", views.UsageOfEquipmentReport.as_view(), name="usages_of_equipment_report"),
]

urlpatterns = [
    #     path("", views.LoginView.as_view(), name="login"),

    path("dashboard", views.Dashboard.as_view(), name="dashboard"),
    path("proposal-list", views.ProposalList.as_view(), name="proposal_list"),
    path("proposal-preview", views.ProposalPreview.as_view(),
         name="proposal_preview"),
    path("opportunity-list", views.OpportunityList.as_view(),
         name="opportunity_list"),
    path("opportunity-details", views.OpportunityDetails.as_view(),
         name="opportunity_details"),
    path("opportunity", views.Opportunity.as_view(), name="opportunity"),
    path("generate_estimate_table", views.GenerateEstimateTable.as_view(),
         name="generate_estimate_table"),
    path("material-list", views.MaterialListView.as_view(), name="material_list"),
    path("glue-material-list", views.GlueListView.as_view(),
         name="glue_material_list"),
    path("final-ready-material-list", views.FinalReadyMaterialListView.as_view(),
         name="final_ready_material_list"),
    path("estimate", views.EstimateView.as_view(), name="estimate"),
    path("proposal", views.ProposalView.as_view(), name="proposal"),
    path("proposal-creation", views.ProposalCreateView.as_view(),
         name="proposal-creation"),
    path("products", views.ProductList.as_view(), name="product_list"),
    path("labor-cost", views.LaborCostList.as_view(), name="labor_cost_list"),
    path("customer", views.CustomerList.as_view(), name="customer_list"),
    path("task", views.TaskList.as_view(), name="task_list"),
    path("vendor", views.VendorList.as_view(), name="vendor_list"),
#     path("inbox", views.InboxList.as_view(), name="inbox_list"),
    path("update_profile", views.UpdateProfile.as_view(), name="update_profile"),
    path("motor_fla_calculator", views.MotorFLACalculator.as_view(),
         name="motor_fla_calculator"),
    path("pump_flo_calculator", views.PumpFLOCalculator.as_view(), name="pump_flo_calculator"),
    path("netafim_calculator", views.NetafimCalculator.as_view(), name="netafim_calculator"),
    path("overlap_pro_calculator", views.OverlapProCalculator.as_view(),
         name="overlap_pro_calculator"),
    path("southwire_calculator", views.SouthwireCalculator.as_view(),
         name="southwire_calculator"),
    path("paigewire_calculator", views.PaigewireCalculator.as_view(),
         name="paigewire_calculator"),
    path("choose_screens", views.ChooseScreens.as_view(), name="choose_screens"),
    path("coming_soon", views.ComingSoon.as_view(), name="coming_soon"),
]+warehouse_urls+reports_urls
