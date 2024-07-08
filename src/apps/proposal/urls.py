from django.urls import path
from . import views

app_name = "proposal"


warehouse_urls = [
    path("warehouse_list", views.WarehouseList.as_view(), name="warehouse_list"),
    path("warehouse_products", views.WarehouseProducts.as_view(), name="warehouse_products"),
    path("user_list", views.UserList.as_view(), name="user_list"),
    path("order_list", views.OrderList.as_view(), name="order_list"),
    path("recurring_order", views.RecurringOrder.as_view(), name="recurring_order"),
    path("order", views.Order.as_view(), name="order"),
    path("return_order", views.ReturnOrder.as_view(), name="return_order"),
    path("express_delivery", views.ExpressDelivery.as_view(), name="express_delivery"),
    path("delivery_list", views.Delivery.as_view(), name="delivery_list"),
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
    path("home", views.Home.as_view(), name="home"),
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
    path("inbox", views.InboxList.as_view(), name="inbox_list"),
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
]+warehouse_urls
