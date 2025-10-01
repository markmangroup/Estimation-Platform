from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.proposal.template.models import EstimationTemplate


class Command(BaseCommand):
    help = "Seed 10 agriculture/irrigation estimation templates for quick start"

    def handle(self, *args, **options):
        templates = [
            {
                "name": "Drip Irrigation System - Vineyard",
                "description": "Complete drip irrigation system for vineyard applications with emitters, filters, and controls. Includes mainline, drip tubing, and fertigation equipment.",
                "industry": "Agriculture",
                "project_type": "Drip Irrigation",
                "estimated_hours": 120,
                "estimated_cost_min": Decimal("15000.00"),
                "estimated_cost_max": Decimal("35000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "Site Survey & Design", "hours": 8},
                        {"id": 2, "name": "Trenching & Mainline Installation", "hours": 40},
                        {"id": 3, "name": "Drip Line Installation", "hours": 48},
                        {"id": 4, "name": "Filter & Control Installation", "hours": 16},
                        {"id": 5, "name": "System Testing & Training", "hours": 8}
                    ],
                    "products": [
                        {"name": "Drip Tubing (per 1000ft)", "quantity": 50, "unit_cost": 75},
                        {"name": "Emitters (per 100)", "quantity": 200, "unit_cost": 25},
                        {"name": "Main Line PVC 3\" (per 20ft)", "quantity": 150, "unit_cost": 45},
                        {"name": "Sand Media Filter", "quantity": 1, "unit_cost": 2500},
                        {"name": "Fertilizer Injector", "quantity": 1, "unit_cost": 1200}
                    ],
                    "labor_rate": 45
                }
            },
            {
                "name": "Sprinkler System Installation - Field",
                "description": "Overhead sprinkler system for open field applications with PVC laterals, risers, and impact sprinklers.",
                "industry": "Agriculture",
                "project_type": "Sprinkler Installation",
                "estimated_hours": 80,
                "estimated_cost_min": Decimal("12000.00"),
                "estimated_cost_max": Decimal("25000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "Layout & Staking", "hours": 8},
                        {"id": 2, "name": "Trenching", "hours": 24},
                        {"id": 3, "name": "Lateral Installation", "hours": 32},
                        {"id": 4, "name": "Sprinkler Head Installation", "hours": 12},
                        {"id": 5, "name": "System Startup", "hours": 4}
                    ],
                    "products": [
                        {"name": "Impact Sprinkler Heads", "quantity": 50, "unit_cost": 35},
                        {"name": "PVC Lateral 2\" (per 20ft)", "quantity": 200, "unit_cost": 28},
                        {"name": "Riser Assemblies", "quantity": 50, "unit_cost": 18},
                        {"name": "Control Valves 2\"", "quantity": 4, "unit_cost": 95}
                    ],
                    "labor_rate": 45
                }
            },
            {
                "name": "Well Pump & Filtration System",
                "description": "Deep well pump installation with pressure tank, control panel, and filtration system for agricultural water supply.",
                "industry": "Agriculture",
                "project_type": "Well Pump System",
                "estimated_hours": 32,
                "estimated_cost_min": Decimal("8000.00"),
                "estimated_cost_max": Decimal("18000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "Well Assessment", "hours": 4},
                        {"id": 2, "name": "Pump Installation", "hours": 8},
                        {"id": 3, "name": "Electrical & Controls", "hours": 12},
                        {"id": 4, "name": "Filtration System", "hours": 6},
                        {"id": 5, "name": "Testing & Commissioning", "hours": 2}
                    ],
                    "products": [
                        {"name": "Submersible Pump 10HP", "quantity": 1, "unit_cost": 3500},
                        {"name": "Pressure Tank 120gal", "quantity": 1, "unit_cost": 850},
                        {"name": "Control Panel", "quantity": 1, "unit_cost": 1200},
                        {"name": "Sand Filter System", "quantity": 1, "unit_cost": 2200}
                    ],
                    "labor_rate": 55
                }
            },
            {
                "name": "Landscape Grading & Drainage",
                "description": "Land grading, contour work, and drainage system installation for proper water management and erosion control.",
                "industry": "Agriculture",
                "project_type": "Grading & Drainage",
                "estimated_hours": 60,
                "estimated_cost_min": Decimal("10000.00"),
                "estimated_cost_max": Decimal("22000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "Topographic Survey", "hours": 8},
                        {"id": 2, "name": "Excavation & Grading", "hours": 32},
                        {"id": 3, "name": "Drainage Pipe Installation", "hours": 16},
                        {"id": 4, "name": "Final Grading & Compaction", "hours": 4}
                    ],
                    "products": [
                        {"name": "Corrugated Drainage Pipe 6\" (per 20ft)", "quantity": 100, "unit_cost": 35},
                        {"name": "Catch Basins", "quantity": 4, "unit_cost": 225},
                        {"name": "Gravel Base (per ton)", "quantity": 15, "unit_cost": 45}
                    ],
                    "labor_rate": 50,
                    "equipment": "Excavator, Grader"
                }
            },
            {
                "name": "Agricultural Fencing - Perimeter",
                "description": "Perimeter fencing with T-posts, wire, and gates for livestock or crop protection.",
                "industry": "Agriculture",
                "project_type": "Fencing",
                "estimated_hours": 40,
                "estimated_cost_min": Decimal("5000.00"),
                "estimated_cost_max": Decimal("12000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "Property Line Survey", "hours": 4},
                        {"id": 2, "name": "Post Installation", "hours": 20},
                        {"id": 3, "name": "Wire Stringing", "hours": 12},
                        {"id": 4, "name": "Gate Installation", "hours": 4}
                    ],
                    "products": [
                        {"name": "T-Posts 6ft", "quantity": 200, "unit_cost": 8},
                        {"name": "Barbed Wire (per 1000ft)", "quantity": 10, "unit_cost": 95},
                        {"name": "Farm Gates 14ft", "quantity": 2, "unit_cost": 450}
                    ],
                    "labor_rate": 40
                }
            },
            {
                "name": "Greenhouse Installation - 30x100",
                "description": "Commercial greenhouse structure with environmental controls, benches, and irrigation system.",
                "industry": "Agriculture",
                "project_type": "Greenhouse",
                "estimated_hours": 160,
                "estimated_cost_min": Decimal("35000.00"),
                "estimated_cost_max": Decimal("65000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "Site Preparation & Foundation", "hours": 32},
                        {"id": 2, "name": "Frame Assembly", "hours": 48},
                        {"id": 3, "name": "Glazing Installation", "hours": 40},
                        {"id": 4, "name": "HVAC & Controls", "hours": 24},
                        {"id": 5, "name": "Benches & Irrigation", "hours": 16}
                    ],
                    "products": [
                        {"name": "Greenhouse Frame Kit 30x100", "quantity": 1, "unit_cost": 18000},
                        {"name": "Polycarbonate Panels (per 10)", "quantity": 150, "unit_cost": 125},
                        {"name": "Climate Control System", "quantity": 1, "unit_cost": 4500},
                        {"name": "Rolling Benches (per 10ft)", "quantity": 20, "unit_cost": 85}
                    ],
                    "labor_rate": 50
                }
            },
            {
                "name": "Solar Pump System - Off-Grid",
                "description": "Solar-powered water pump system for remote irrigation applications with panels, controller, and battery bank.",
                "industry": "Agriculture",
                "project_type": "Solar Pump",
                "estimated_hours": 48,
                "estimated_cost_min": Decimal("12000.00"),
                "estimated_cost_max": Decimal("28000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "System Design & Sizing", "hours": 8},
                        {"id": 2, "name": "Solar Panel Installation", "hours": 16},
                        {"id": 3, "name": "Pump & Plumbing", "hours": 12},
                        {"id": 4, "name": "Electrical & Controls", "hours": 8},
                        {"id": 5, "name": "Testing & Optimization", "hours": 4}
                    ],
                    "products": [
                        {"name": "Solar Panels 400W", "quantity": 8, "unit_cost": 350},
                        {"name": "Solar Charge Controller", "quantity": 1, "unit_cost": 1200},
                        {"name": "DC Pump 1HP", "quantity": 1, "unit_cost": 2500},
                        {"name": "Battery Bank 48V", "quantity": 1, "unit_cost": 3800}
                    ],
                    "labor_rate": 60
                }
            },
            {
                "name": "Water Storage Tank - 10,000 Gallon",
                "description": "Above-ground water storage tank installation with foundation, piping, and level controls.",
                "industry": "Agriculture",
                "project_type": "Water Storage",
                "estimated_hours": 24,
                "estimated_cost_min": Decimal("8000.00"),
                "estimated_cost_max": Decimal("15000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "Site Preparation & Foundation", "hours": 8},
                        {"id": 2, "name": "Tank Installation", "hours": 8},
                        {"id": 3, "name": "Plumbing & Valves", "hours": 6},
                        {"id": 4, "name": "Level Controls & Testing", "hours": 2}
                    ],
                    "products": [
                        {"name": "Poly Tank 10000gal", "quantity": 1, "unit_cost": 5500},
                        {"name": "Float Valve Assembly", "quantity": 1, "unit_cost": 185},
                        {"name": "Piping & Fittings", "quantity": 1, "unit_cost": 450},
                        {"name": "Concrete Pad 12x12", "quantity": 1, "unit_cost": 1200}
                    ],
                    "labor_rate": 45
                }
            },
            {
                "name": "Center Pivot Irrigation System",
                "description": "Automated center pivot irrigation system for large-scale field watering with GPS controls.",
                "industry": "Agriculture",
                "project_type": "Pivot Irrigation",
                "estimated_hours": 200,
                "estimated_cost_min": Decimal("80000.00"),
                "estimated_cost_max": Decimal("150000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "Site Assessment & Design", "hours": 16},
                        {"id": 2, "name": "Foundation & Pivot Point", "hours": 32},
                        {"id": 3, "name": "Tower & Span Installation", "hours": 96},
                        {"id": 4, "name": "Nozzle & Drop Installation", "hours": 32},
                        {"id": 5, "name": "Electrical & GPS Controls", "hours": 16},
                        {"id": 6, "name": "Testing & Commissioning", "hours": 8}
                    ],
                    "products": [
                        {"name": "Center Pivot System 1/4 Mile", "quantity": 1, "unit_cost": 65000},
                        {"name": "GPS Control Panel", "quantity": 1, "unit_cost": 8500},
                        {"name": "Nozzle Package", "quantity": 1, "unit_cost": 3200}
                    ],
                    "labor_rate": 55,
                    "equipment": "Crane, Trencher"
                }
            },
            {
                "name": "Frost Protection System - Orchard",
                "description": "Overhead sprinkler system specifically designed for frost protection in orchards with quick activation controls.",
                "industry": "Agriculture",
                "project_type": "Frost Protection",
                "estimated_hours": 100,
                "estimated_cost_min": Decimal("20000.00"),
                "estimated_cost_max": Decimal("40000.00"),
                "template_data": {
                    "tasks": [
                        {"id": 1, "name": "Orchard Assessment", "hours": 8},
                        {"id": 2, "name": "Mainline Installation", "hours": 32},
                        {"id": 3, "name": "Lateral & Riser Installation", "hours": 40},
                        {"id": 4, "name": "Sprinkler Head Installation", "hours": 12},
                        {"id": 5, "name": "Control System & Sensors", "hours": 8}
                    ],
                    "products": [
                        {"name": "Micro-Sprinklers (per 100)", "quantity": 50, "unit_cost": 180},
                        {"name": "PVC Mainline 4\" (per 20ft)", "quantity": 200, "unit_cost": 65},
                        {"name": "Temperature Sensors", "quantity": 4, "unit_cost": 250},
                        {"name": "Automatic Control Valves", "quantity": 6, "unit_cost": 145}
                    ],
                    "labor_rate": 50
                }
            }
        ]

        created_count = 0
        for template_data in templates:
            template, created = EstimationTemplate.objects.get_or_create(
                name=template_data["name"],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {template.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'→ Already exists: {template.name}'))

        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully seeded {created_count} new templates!'))
        self.stdout.write(self.style.SUCCESS(f'Total templates in database: {EstimationTemplate.objects.count()}'))
