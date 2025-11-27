from dotenv import load_dotenv
load_dotenv()
from app import app
from models_b4a import Category, Product, User, db

def test_connection():
    print("Testing Back4App Connection...")
    try:
        # Try to fetch categories
        print("Fetching categories...")
        categories = Category.query.all()
        print(f"Found {len(categories)} categories.")
        for cat in categories:
            print(f"- {cat.name} ({cat.id})")
            
        # Try to create a test category if none exist
        if not categories:
            print("Creating test category...")
            new_cat = Category(name="Test Category", description="Created via migration script")
            db.session.add(new_cat)
            db.session.commit()
            print(f"Created category: {new_cat.name} ({new_cat.id})")
            
        print("Connection successful!")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_connection()
