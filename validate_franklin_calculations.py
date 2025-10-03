#!/usr/bin/env python3
"""
Validation script: Verify our calculations match Franklin's Excel exactly
Run this after creating a bid item via UI to confirm numbers match
"""
import os, sys, django
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laurel.settings.local")
django.setup()

from apps.proposal.opportunity.models import Opportunity
from apps.proposal.bid.models import BidSchedule, BidItem, BidItemMaterial, BidItemLabor

print("=" * 80)
print("VALIDATION: Does our app match Franklin's Excel calculations?")
print("=" * 80)

# Franklin's expected numbers from "Example 2 - Small PW Job.xlsx", Bid Item 1
FRANKLIN_NUMBERS = {
    "materials_total": Decimal("26803.34"),  # Coating + Parts + Mob + Demob + Equip + Rental
    "labor_total": Decimal("15003.36"),
    "our_cost": Decimal("41806.70"),
    "margin_percent": Decimal("25.00"),
    "margin_amount": Decimal("10451.68"),  # 41806.70 * 0.25
    "sale_price": Decimal("52258.38"),  # 41806.70 * 1.25
}

def validate_bid_item(bid_item_id):
    """Validate a specific bid item against Franklin's numbers"""
    try:
        bi = BidItem.objects.get(id=bid_item_id)
    except BidItem.DoesNotExist:
        print(f"\n✗ Bid Item {bid_item_id} not found")
        return False

    print(f"\n✓ Found Bid Item: {bi.bid_schedule.description}")
    print(f"  Materials: {bi.materials.count()} items")
    print(f"  Labor: {bi.labor.count()} items")

    print(f"\n{'='*80}")
    print(f"{'FIELD':<20} {'FRANKLIN':>15} {'OUR APP':>15} {'MATCH':>10}")
    print(f"{'='*80}")

    all_match = True
    tolerance = Decimal("0.01")  # Allow 1 cent difference for rounding

    for field, expected in FRANKLIN_NUMBERS.items():
        actual = getattr(bi, field)
        diff = abs(actual - expected)
        match = diff <= tolerance
        all_match = all_match and match

        status = "✓" if match else f"✗ (±${diff})"
        print(f"{field:<20} ${expected:>13,.2f} ${actual:>13,.2f} {status:>10}")

    print(f"{'='*80}")

    if all_match:
        print(f"\n🎉 SUCCESS! All calculations match Franklin's Excel exactly!")
        print(f"   We can confidently show him: 'Your Excel vs Our App = Same Numbers'")
    else:
        print(f"\n⚠️  Some calculations don't match - review formulas")

    print(f"{'='*80}\n")
    return all_match

def list_bid_items():
    """List all bid items for testing"""
    items = BidItem.objects.all().select_related('bid_schedule__opportunity')

    if not items:
        print("\n⚠️  No bid items found")
        print("   Create one via the UI first, then run this script")
        return

    print(f"\nFound {items.count()} bid item(s):")
    for bi in items:
        opp = bi.bid_schedule.opportunity
        print(f"\n  ID: {bi.id}")
        print(f"  Opportunity: {opp.title if hasattr(opp, 'title') else opp.document_number}")
        print(f"  Bid Item: {bi.bid_schedule.item_code} - {bi.bid_schedule.description}")
        print(f"  Our Cost: ${bi.our_cost:,.2f}")
        print(f"  Sale Price: ${bi.sale_price:,.2f}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        bid_item_id = int(sys.argv[1])
        validate_bid_item(bid_item_id)
    else:
        list_bid_items()
        print(f"\nUsage: python3 validate_franklin_calculations.py <bid_item_id>")
        print(f"Example: python3 validate_franklin_calculations.py 1")
