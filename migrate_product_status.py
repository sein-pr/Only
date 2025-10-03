#!/usr/bin/env python3
"""
Migration script to add status field to Product model
This script adds the status field to existing products and sets them all to 'active' by default
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add the parent directory to the path so we can import our models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the app and models
from app import app
from models.models import db, Product # Ensure db is imported correctly

def migrate_product_status():
    """Add status field to existing products"""
    with app.app_context():
        try:
            # Check if status column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('product')]
            
            if 'status' in columns:
                print("✅ Status column already exists in Product table")
                return True # Changed to return True since no error occurred
            
            # Use a connection and transaction for raw SQL execution (SQLAlchemy 2.0 style)
            with db.engine.connect() as connection:
                
                # 1. Add the status column
                print("🔄 Adding status column to Product table...")
                with connection.begin():
                    connection.execute(
                        db.text("""
                            ALTER TABLE product 
                            ADD COLUMN status VARCHAR(20) DEFAULT 'active'
                        """)
                    )
                print("✅ Successfully added status field to Product model")

                # 2. Update all existing products to have 'active' status
                with connection.begin():
                    connection.execute(
                        db.text("""
                            UPDATE product 
                            SET status = 'active' 
                            WHERE status IS NULL
                        """)
                    )
                print("✅ All existing products set to 'active' status")
            
        except Exception as e:
            # This will now catch the correct database error, not the socket error
            print(f"❌ Error during migration: {e}")
            return False
        
        return True

if __name__ == '__main__':
    print("🚀 Starting Product Status Migration...")
    success = migrate_product_status()
    
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)