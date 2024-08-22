from django.http import JsonResponse
from django.views.generic import TemplateView, View

from apps.opportunity.models import Opportunity
from apps.proposal.mixin import LoginBaseMixin, ProposalViewMixin, WarehouseViewMixin

################################################
################# Base View END ################
################################################


class InboxList(WarehouseViewMixin):
    render_template_name = "proposal/inbox_list.html"


class UpdateProfile(LoginBaseMixin, TemplateView):
    template_name = "proposal/update_profile.html"


class MotorFLACalculator(LoginBaseMixin, TemplateView):
    template_name = "proposal/motor_fla_calculator.html"


class PumpFLOCalculator(LoginBaseMixin, TemplateView):
    template_name = "proposal/pump_flo_calculator.html"


class NetafimCalculator(LoginBaseMixin, TemplateView):
    template_name = "proposal/netafim_calculator.html"


class OverlapProCalculator(LoginBaseMixin, TemplateView):
    template_name = "proposal/overlap_pro_calculator.html"


class SouthwireCalculator(LoginBaseMixin, TemplateView):
    template_name = "proposal/southwire_calculator.html"


class PaigewireCalculator(LoginBaseMixin, TemplateView):
    template_name = "proposal/paigewire_calculator.html"


class ChooseScreens(LoginBaseMixin, TemplateView):
    template_name = "proposal/choose_screens.html"


class ComingSoon(LoginBaseMixin, TemplateView):
    template_name = "proposal/coming_soon.html"


################################################
############ Opportunity View START ############
################################################


# class Opportunity(ProposalViewMixin):
#     """
#     View class for rendering the list of opportunity.
#     """
#     render_template_name = "proposal/opportunity.html"


class ProposalList(ProposalViewMixin):
    """
    View class for rendering the list of proposal.
    """

    render_template_name = "proposal/proposal_list.html"


class ProposalPreview(ProposalViewMixin):
    """
    View class for rendering the proposal preview.
    """

    render_template_name = "proposal/proposal_preview.html"


class OpportunityList(ProposalViewMixin):
    """
    View class for rendering the list of opportunity.
    """

    render_template_name = "proposal/opportunity_list.html"


class OpportunityDetails(ProposalViewMixin):
    """
    View class for rendering the opportunity details.
    """

    render_template_name = "proposal/opportunity_details.html"


class GenerateEstimateTable(ProposalViewMixin):
    """
    View class for rendering the estimate generation.
    """

    render_template_name = "proposal/generate_estimate_table.html"


class MaterialListView(ProposalViewMixin):
    """
    View class for rendering the list of materials.
    """

    render_template_name = "proposal/step_2.html"


class GlueListView(ProposalViewMixin):
    """
    View class for rendering the list of glue.
    """

    render_template_name = "proposal/step_3.html"


class FinalReadyMaterialListView(ProposalViewMixin):
    """
    View class for rendering the list of final ready materials.
    """

    render_template_name = "proposal/step_4.html"


class EstimateView(ProposalViewMixin):
    """
    View class for rendering the estimations.
    """

    render_template_name = "proposal/step_5.html"


class ProposalView(ProposalViewMixin):
    """
    View class for rendering the proposals.
    """

    render_template_name = "proposal/step_6.html"


class ProposalCreateView(ProposalViewMixin):
    """
    View class for rendering the proposal creation.
    """

    render_template_name = "proposal/proposel_creation.html"


# class ProductList(ProposalViewMixin):
#     """
#     View class for rendering the list of proposal product.
#     """
#     render_template_name = "proposal/product_list.html"


# class LaborCostList(ProposalViewMixin):
#     """
#     View class for rendering the list of proposal labor.
#     """
#     render_template_name = "proposal/labor_cost_list.html"


# class CustomerList(ProposalViewMixin):
#     """
#     View class for rendering the list of proposal customer.
#     """
#     render_template_name = "proposal/customer_list.html"


# class TaskList(ProposalViewMixin):
#     """
#     View class for rendering the list of proposal task.
#     """
#     render_template_name = "proposal/task_list.html"


# class VendorList(ProposalViewMixin):
#     """
#     View class for rendering the list of proposal vendor.
#     """
#     render_template_name = "proposal/vendor_list.html"

################################################
############ Opportunity View End ##############
################################################


##############################################
############ Warehouse View START ############
##############################################


class Dashboard(WarehouseViewMixin):
    render_template_name = "warehouse/dashboard.html"


class CustomerDetail(WarehouseViewMixin):
    """
    View class for rendering customer details.
    """

    render_template_name = "warehouse/map_customer_details.html"


class MapView(WarehouseViewMixin):
    """
    View class for rendering Map views with customer and warehouse locations.
    """

    render_template_name = "warehouse/map.html"


class WarehouseProducts(WarehouseViewMixin):
    """
    View class for rendering the list of warehouse products.
    """

    render_template_name = "warehouse/warehouse_product_list.html"


class WarehouseList(WarehouseViewMixin):
    """
    View class for rendering the list of warehouses.
    """

    render_template_name = "warehouse/warehouse_list.html"


class WarehouseDetailView(WarehouseViewMixin):
    """
    View class for rendering the detail of warehouse.
    """

    render_template_name = "warehouse/map_warehouse_detail.html"


class CustomerListView(WarehouseViewMixin):
    """
    View class for rendering the list of warehouses.
    """

    render_template_name = "warehouse/customer_list.html"


class UserList(WarehouseViewMixin):
    """
    View class for rendering the list of users.
    """

    render_template_name = "warehouse/user_list.html"


class OrderList(WarehouseViewMixin):
    """
    View class for rendering the list of orders.
    """

    render_template_name = "warehouse/order_list.html"


class OrderDetail(WarehouseViewMixin):
    """
    View class for rendering the list of orders.
    """

    render_template_name = "warehouse/orders/rental_order.html"


class RecurringOrder(WarehouseViewMixin):
    """
    View class for rendering recurring order details.
    """

    render_template_name = "warehouse/recurring_order.html"


class Order(WarehouseViewMixin):
    """
    View class for rendering a single order.
    """

    render_template_name = "warehouse/orders/order.html"


class ReturnOrder(WarehouseViewMixin):
    """
    View class for rendering a single return order.
    """

    render_template_name = "warehouse/orders/return_order.html"


class ExpressDelivery(WarehouseViewMixin):
    """
    View class for rendering express delivery details.
    """

    render_template_name = "warehouse/express_delivery.html"


class Delivery(WarehouseViewMixin):
    """
    View class for rendering list of delivery details.
    """

    render_template_name = "warehouse/delivery_list.html"


class Reports(WarehouseViewMixin):
    """

    View class for rendering report with details.
    """

    render_template_name = "warehouse/reports.html"


class Workflow(WarehouseViewMixin):
    """
    View class for rendering workflow details.
    """

    render_template_name = "warehouse/workflow.html"


class StockAdjustment(WarehouseViewMixin):
    """
    View class for rendering adjustment of stocks.
    """

    render_template_name = "warehouse/stock_adjustment.html"


class ReturnDelivery(WarehouseViewMixin):
    """
    View class for rendering list of delivery details.
    """

    render_template_name = "warehouse/return_delivery_list.html"


##############################################
############ Warehouse Reports START ############
##############################################


class ReportsView(WarehouseViewMixin):
    """
    View class for reports.
    """

    render_template_name = "warehouse/reports/reports.html"


class RevenueReport(WarehouseViewMixin):
    """
    View class for revenue report.
    """

    render_template_name = "warehouse/reports/revenue_report.html"


class StockReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "warehouse/reports/stock_report.html"


class StockMovementReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "warehouse/reports/stock_movement_report.html"


class InTransitReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "warehouse/reports/in_transit_report.html"


class PlannedRemovalReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "warehouse/reports/planned_removal_report.html"


class PlannedDeliveriesReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "warehouse/reports/planned_deliveries_report.html"


class UsageOfEquipmentReport(WarehouseViewMixin):
    """
    View class for stock report.
    """

    render_template_name = "warehouse/reports/usages_of_equipment.html"


class InboxView(WarehouseViewMixin):
    """
    View class for inbox.
    """

    render_template_name = "warehouse/inbox.html"


class SearchView(View):
    def get(self, request, *args, **kwargs) -> JsonResponse:
        """
        Handle GET requests to search for opportunities by document number.

        Retrieves the 'query' parameter from the request, filters `Opportunity`
        for records where `document_number` contains the query string, and returns
        the results in JSON format.

        :request (HttpRequest): The HTTP request object containing query parameters.

        Returns:
        - JsonResponse: JSON response with a list of matching `document_number` values.
        """
        query = request.GET.get("query", "")
        results = []
        # Check length of query
        if len(query) > 3 and query:
            # Set limit with results
            results = Opportunity.objects.filter(document_number__icontains=query).values("document_number")[:5]
        return JsonResponse({"results": list(results)})
