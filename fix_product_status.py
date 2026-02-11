"""
Script to add status='active' to all existing products that don't have it
"""
from dotenv import load_dotenv
load_dotenv()

from back4app_client import Back4AppClient

print("=" * 60)
print("FIXING PRODUCT STATUS")
print("=" * 60)

client = Back4AppClient()

# Get all products
print("\n1. Fetching all products...")
result = client.query('Product', limit=1000)
products = result.get('results', [])
print(f"   Found {len(products)} products")

# Update products without status
updated_count = 0
for product in products:
    if 'status' not in product or not product.get('status'):
        print(f"\n2. Updating product: {product.get('name', 'Unknown')}")
        print(f"   ID: {product['objectId']}")
        
        try:
            client.update('Product', product['objectId'], {'status': 'active'})
            print(f"   ✅ Status set to 'active'")
            updated_count += 1
        except Exception as e:
            print(f"   ❌ Failed to update: {e}")

print("\n" + "=" * 60)
print(f"COMPLETE: Updated {updated_count} products")
print("=" * 60)

# Verify
print("\n3. Verifying updates...")
result = client.query('Product', where={'status': 'active'}, limit=1000)
active_products = result.get('results', [])
print(f"   ✅ Found {len(active_products)} active products")

if active_products:
    print(f"\n   Active products:")
    for p in active_products:
        print(f"   - {p.get('name')} (status: {p.get('status')})")
