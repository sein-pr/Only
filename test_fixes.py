"""
Test the query property and Decimal serialization fixes
"""
from dotenv import load_dotenv
load_dotenv()

from models_b4a import Product, User
from decimal import Decimal

print("=" * 60)
print("TESTING FIXES")
print("=" * 60)

# Test 1: Query property
print("\n1. Testing Product.query property...")
try:
    result = Product.query.filter_by(status='active').limit(5).all()
    print(f"✅ Product.query works! Found {len(result)} products")
except Exception as e:
    print(f"❌ Product.query failed: {e}")

# Test 2: User query
print("\n2. Testing User.query property...")
try:
    result = User.query.limit(3).all()
    print(f"✅ User.query works! Found {len(result)} users")
    if result:
        print(f"   First user: {result[0].username}")
except Exception as e:
    print(f"❌ User.query failed: {e}")

# Test 3: Decimal serialization
print("\n3. Testing Decimal serialization...")
try:
    from back4app_client import Back4AppClient, convert_decimals
    
    test_data = {
        'name': 'Test Product',
        'price': Decimal('19.99'),
        'stock': 10,
        'nested': {
            'discount': Decimal('5.50')
        }
    }
    
    converted = convert_decimals(test_data)
    print(f"✅ Decimal conversion works!")
    print(f"   Original price type: {type(test_data['price'])}")
    print(f"   Converted price type: {type(converted['price'])}")
    print(f"   Converted price value: {converted['price']}")
    
    # Try to JSON serialize it
    import json
    json_str = json.dumps(converted)
    print(f"✅ JSON serialization works!")
    
except Exception as e:
    print(f"❌ Decimal conversion failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
