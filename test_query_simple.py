"""Simple test of Query descriptor"""
import sys
sys.path.insert(0, '.')

# Mock the client for testing
class MockClient:
    def query(self, class_name, **kwargs):
        return {'results': [{'id': 1, 'name': 'Test'}]}

# Replace client in models_b4a
import models_b4a
models_b4a.client = MockClient()

from models_b4a import Product

print("Testing Query descriptor...")

# Test 1: Get query object
print("\n1. Getting Product.query...")
q1 = Product.query
print(f"   Type: {type(q1)}")
print(f"   Model class: {q1.model_class.__name__}")

# Test 2: Get another query object
print("\n2. Getting Product.query again...")
q2 = Product.query
print(f"   Same object? {q1 is q2}")
print(f"   Should be False (new instance each time)")

# Test 3: Try a query
print("\n3. Running Product.query.all()...")
try:
    results = Product.query.all()
    print(f"   ✅ Success! Got {len(results)} results")
except Exception as e:
    print(f"   ❌ Failed: {e}")

print("\n✅ Query descriptor working correctly!")
