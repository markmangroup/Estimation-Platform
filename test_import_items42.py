#!/usr/bin/env python3
"""
Test importing Items42.xlsx via Django
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "laurel.settings.local")
django.setup()

from apps.proposal.product.tasks import import_product_from_file
from django.core.files.uploadedfile import SimpleUploadedFile

# Read the converted Items42.xlsx
items_file = Path("src/laurel/example_bids/Items42.xlsx")
print(f"📦 Reading {items_file.name}...")

with open(items_file, "rb") as f:
    file_content = f.read()
    uploaded_file = SimpleUploadedFile(
        name="Items42.xlsx",
        content=file_content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    print(f"📤 Importing products...")
    result = import_product_from_file(uploaded_file)

    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        messages = result.get("messages", [])
        created_count = sum(1 for msg in messages if "Created" in msg)
        updated_count = sum(1 for msg in messages if "Updated" in msg)

        print(f"\n✅ Import complete!")
        print(f"   Created: {created_count:,}")
        print(f"   Updated: {updated_count:,}")
        print(f"   Total:   {created_count + updated_count:,}")

        # Show sample
        if messages[:3]:
            print(f"\n   Sample messages:")
            for msg in messages[:3]:
                print(f"     • {msg}")

# Verify in database
from apps.proposal.product.models import Product
total_products = Product.objects.count()
print(f"\n🗄️  Database verification: {total_products:,} products total")

# Show sample products
print(f"\n   Sample products:")
for p in Product.objects.all()[:3]:
    print(f"     • [{p.internal_id}] {p.name} - ${p.std_cost}")
