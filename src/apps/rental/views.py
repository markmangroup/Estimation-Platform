from typing import Any, Dict

from django.urls import reverse

from apps.mixin import TemplateViewMixin, WarehouseViewMixin
from apps.rental.customer.models import RentalCustomer
from apps.rental.warehouse.models import RentalWarehouse

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


class MapView(WarehouseViewMixin):
    """
    View class for rendering map views with customer and warehouse locations.
    """

    render_template_name = "rental/map/map.html"

    def _get_warehouse_data(self) -> list:
        """Retrieve a list of warehouse data."""
        return [
            {
                "id": warehouse.id,
                "lat": float(warehouse.lat) if warehouse.lat is not None else None,
                "lng": float(warehouse.lng) if warehouse.lng is not None else None,
                "name": warehouse.location,
                "address": warehouse.address,
            }
            for warehouse in RentalWarehouse.objects.all()
            if warehouse.lat is not None and warehouse.lng is not None
        ]

    def _get_customer_data(self) -> list:
        """Retrieve a list of customer data."""
        return [
            {
                "id": customer.id,
                "lat": float(customer.lat) if customer.lat is not None else None,
                "lng": float(customer.lng) if customer.lng is not None else None,
                "name": customer.name,
                "address": customer.billing_address_1 or customer.billing_address_2,
                "product": {
                    "name": "name",
                    "url": reverse("rental:warehouse_products"),
                },
            }
            for customer in RentalCustomer.objects.filter(lat__isnull=False, lng__isnull=False)
        ]

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Add warehouse and customer data to context."""
        context = super().get_context_data(**kwargs)
        context["warehouse"] = self._get_warehouse_data()
        context["customer"] = self._get_customer_data()
        return context


class WarehouseProducts(WarehouseViewMixin):
    """
    View class for rendering the list of warehouse products.
    """

    render_template_name = "rental/warehouse_product_list.html"


class UserList(WarehouseViewMixin):
    """
    View class for rendering the list of users.
    """

    render_template_name = "rental/authorization/user_list.html"


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


# class Workflow(WarehouseViewMixin):
#     """
#     View class for rendering workflow details.
#     """

#     render_template_name = "rental/workflow.html"


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
