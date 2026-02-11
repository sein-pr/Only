"""
Test product queries to see why they're not displaying
"""
from dotenv import load_dotenv
load_dotenv()

from models_b4a import Product
from back4app_client import Back4AppClient

print("=" * 60)
print("TESTING PRODUCT QUERIES")
print("=" * 60)

# Test 1: Direct API call
print("\n1. Direct API call to get all products...")
try:
    client = Back4AppClient()
    result = client.query('Product', limit=100)
    products = result.get('results', [])
    print(f"✅ Found {len(products)} products via direct API call")
    
    if products:
        print(f"\n   First product:")
        for key, value in products[0].items():
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"   - {key}: {value}")
except Exception as e:
    print(f"❌ Direct API call failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Using Product.query
print("\n2. Using Product.query.all()...")
try:
    products = Product.query.all()
    print(f"✅ Found {len(products)} products via Product.query.all()")
    
    if products:
        print(f"\n   First product:")
        print(f"   - ID: {products[0].id}")
        print(f"   - Name: {products[0].name if hasattr(products[0], 'name') else 'N/A'}")
        print(f"   - Status: {products[0].status if hasattr(products[0], 'status') else 'N/A'}")
        print(f"   - Price: {products[0].price if hasattr(products[0], 'price') else 'N/A'}")
        print(f"   - Data: {products[0]._data}")
except Exception as e:
    print(f"❌ Product.query.all() failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Filter by status
print("\n3. Using Product.query.filter_by(status='active')...")
try:
    products = Product.query.filter_by(status='active').all()
    print(f"✅ Found {len(products)} active products")
    
    if products:
        for i, product in enumerate(products[:3], 1):
            print(f"\n   Product {i}:")
            print(f"   - Name: {product.name if hasattr(product, 'name') else 'N/A'}")
            print(f"   - Status: {product.status if hasattr(product, 'status') else 'N/A'}")
except Exception as e:
    print(f"❌ Filter by status failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Order by created_at
print("\n4. Using Product.query.order_by(Product.created_at.desc())...")
try:
    products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    print(f"✅ Found {len(products)} products with ordering")
except Exception as e:
    print(f"❌ Order by failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Combined query (like in home page)
print("\n5. Testing home page query: filter_by + order_by + limit...")
try:
    products = Product.query.filter_by(status='active').order_by(Product.created_at.desc()).limit(8).all()
    print(f"✅ Found {len(products)} products with combined query")
    
    if products:
        print(f"\n   Products found:")
        for product in products:
            print(f"   - {product.name if hasattr(product, 'name') else 'Unknown'}")
except Exception as e:
    print(f"❌ Combined query failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
