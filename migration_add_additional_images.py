#!/usr/bin/env python3
"""
Database migration script to add additional_images field to Product table.
Run this script to update your existing database schema.
"""

from app import app, db
from models.models import Product

def migrate_database():
    """Add additional_images column to Product table if it doesn't exist."""
    
    with app.app_context():
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('product')]
            
            if 'additional_images' not in columns:
                print("Adding additional_images column to Product table...")
                
                # Add the column using raw SQL
                db.engine.execute(
                    "ALTER TABLE product ADD COLUMN additional_images JSON"
                )
                
                print("✅ Successfully added additional_images column!")
            else:
                print("✅ additional_images column already exists!")
                
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            print("You may need to run this manually or recreate your database.")

if __name__ == '__main__':
    print("🔄 Starting database migration...")
    migrate_database()
    print("✅ Migration completed!")
