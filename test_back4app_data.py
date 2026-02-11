"""
Test script to check Back4App database contents
"""
import os
from dotenv import load_dotenv
from back4app_client import Back4AppClient

# Load environment variables
load_dotenv()

def test_back4app_connection():
    """Test connection and query all tables"""
    
    print("=" * 60)
    print("BACK4APP DATABASE TEST")
    print("=" * 60)
    
    # Initialize client
    try:
        client = Back4AppClient()
        print("✅ Back4App client initialized successfully")
        print(f"   App ID: {client.app_id[:10]}...")
        print(f"   API URL: {client.base_url}")
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        return
    
    print("\n" + "=" * 60)
    
    # Test each table
    tables = ['User', 'Category', 'Product', 'Order', 'OrderItem', 'CartItem', 'Wishlist', 'ProductView', 'PasswordResetToken']
    
    for table_name in tables:
        print(f"\n📊 Checking table: {table_name}")
        print("-" * 60)
        
        try:
            # Query all records from the table
            result = client.query(table_name, limit=10)
            
            if 'results' in result:
                records = result['results']
                count = len(records)
                
                if count > 0:
                    print(f"✅ Found {count} record(s)")
                    
                    # Show first record details
                    print(f"\n   First record:")
                    for key, value in records[0].items():
                        # Truncate long values
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"   - {key}: {value}")
                    
                    # If there are more records, show count
                    if count > 1:
                        print(f"\n   ... and {count - 1} more record(s)")
                else:
                    print(f"⚠️  Table is empty (0 records)")
            else:
                print(f"⚠️  Unexpected response format: {result}")
                
        except Exception as e:
            print(f"❌ Error querying {table_name}: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

def test_create_user():
    """Test creating a user directly"""
    print("\n" + "=" * 60)
    print("TESTING USER CREATION")
    print("=" * 60)
    
    try:
        client = Back4AppClient()
        
        # Try to create a test user
        test_user_data = {
            'username': 'test_user_direct',
            'email': 'test@example.com',
            'password_hash': 'test_hash_123',
            'role': 'buyer'
        }
        
        print(f"\n📝 Attempting to create user: {test_user_data['username']}")
        
        result = client.create('User', test_user_data)
        
        print(f"✅ User created successfully!")
        print(f"   Object ID: {result.get('objectId')}")
        print(f"   Created At: {result.get('createdAt')}")
        
        # Now query to verify
        print(f"\n🔍 Verifying user was saved...")
        users = client.query('User', where={'username': 'test_user_direct'})
        
        if users.get('results'):
            print(f"✅ User found in database!")
            print(f"   Data: {users['results'][0]}")
        else:
            print(f"⚠️  User not found after creation")
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_back4app_connection()
    test_create_user()
