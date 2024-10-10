from apps.mixin import TemplateViewMixin, WarehouseViewMixin

# Create your views here.


class ChooseScreens(TemplateViewMixin):
    template_name = "proposal/choose_screens.html"


class ComingSoon(TemplateViewMixin):
    template_name = "proposal/coming_soon.html"


##############################################
############ Warehouse View START ############
##############################################


class Dashboard(WarehouseViewMixin):
    render_template_name = "rental/dashboard.html"


class CustomerDetail(WarehouseViewMixin):
    """
    View class for rendering customer details.
    """

    render_template_name = "rental/map_customer_details.html"


class MapView(WarehouseViewMixin):
    """
    View class for rendering Map views with customer and warehouse locations.
    """

    render_template_name = "rental/map.html"


class WarehouseProducts(WarehouseViewMixin):
    """
    View class for rendering the list of warehouse products.
    """

    render_template_name = "rental/warehouse_product_list.html"


class WarehouseList(WarehouseViewMixin):
    """
    View class for rendering the list of warehouses.
    """

    render_template_name = "rental/warehouse_list.html"


class WarehouseDetailView(WarehouseViewMixin):
    """
    View class for rendering the detail of warehouse.
    """

    render_template_name = "rental/map_warehouse_detail.html"


class CustomerListView(WarehouseViewMixin):
    """
    View class for rendering the list of warehouses.
    """

    render_template_name = "rental/customer_list.html"


class UserList(WarehouseViewMixin):
    """
    View class for rendering the list of users.
    """

    render_template_name = "rental/user_list.html"


class OrderList(WarehouseViewMixin):
    """
    View class for rendering the list of orders.
    """

    render_template_name = "rental/order_list.html"


class OrderDetail(WarehouseViewMixin):
    """
    View class for rendering the list of orders.
    """

    render_template_name = "rental/orders/rental_order.html"


class RecurringOrder(WarehouseViewMixin):
    """
    View class for rendering recurring order details.
    """

    render_template_name = "rental/recurring_order.html"


class Order(WarehouseViewMixin):
    """
    View class for rendering a single order.
    """

    render_template_name = "rental/orders/order.html"


class ReturnOrder(WarehouseViewMixin):
    """
    View class for rendering a single return order.
    """

    render_template_name = "rental/orders/return_order.html"


class ExpressDelivery(WarehouseViewMixin):
    """
    View class for rendering express delivery details.
    """

    render_template_name = "rental/express_delivery.html"


class Delivery(WarehouseViewMixin):
    """
    View class for rendering list of delivery details.
    """

    render_template_name = "rental/delivery_list.html"


class Reports(WarehouseViewMixin):
    """

    View class for rendering report with details.
    """

    render_template_name = "rental/reports.html"


class Workflow(WarehouseViewMixin):
    """
    View class for rendering workflow details.
    """

    render_template_name = "rental/workflow.html"


class StockAdjustment(WarehouseViewMixin):
    """
    View class for rendering adjustment of stocks.
    """

    render_template_name = "rental/stock_adjustment.html"


class ReturnDelivery(WarehouseViewMixin):
    """
    View class for rendering list of delivery details.
    """

    render_template_name = "rental/return_delivery_list.html"


class AccountManagersList(WarehouseViewMixin):
    """
    View class for rendering the list of warehouses.
    """

    render_template_name = "rental/account_managers.html"


class OrderOverview(WarehouseViewMixin):
    """
    View class for rendering the list of orders.
    """

    render_template_name = "rental/orders/order_overview.html"


##############################################
############ Warehouse Reports START ############
##############################################


class ReportsView(WarehouseViewMixin):
    """
    View class for reports.
    """

    render_template_name = "rental/reports/reports.html"


class RevenueReport(WarehouseViewMixin):
    """
    View class for revenue report.
    """

    render_template_name = "rental/reports/revenue_report.html"


class StockReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "rental/reports/stock_report.html"


class StockMovementReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "rental/reports/stock_movement_report.html"


class InTransitReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "rental/reports/in_transit_report.html"


class PlannedRemovalReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "rental/reports/planned_removal_report.html"


class PlannedDeliveriesReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "rental/reports/planned_deliveries_report.html"


class UsageOfEquipmentReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "rental/reports/usages_of_equipment.html"


class InboxView(WarehouseViewMixin):
    """
    View class for inbox.
    """

    render_template_name = "rental/inbox.html"
