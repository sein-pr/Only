#!/usr/bin/env python3
"""
Database migration script to add new columns to the user table.
Run this script to update your PostgreSQL database with the new user profile fields.
"""

from app import app, db
from sqlalchemy import text

def migrate_user_table():
    """Add new columns to the user table"""
    
    with app.app_context():
        try:
            print("Starting user table migration...")
            
            # List of columns to add
            columns_to_add = [
                ('first_name', 'VARCHAR(50)'),
                ('last_name', 'VARCHAR(50)'),
                ('phone', 'VARCHAR(20)'),
                ('address', 'TEXT'),
                ('avatar_url', 'VARCHAR(200)'),
                ('company_name', 'VARCHAR(100)'),
                ('company_description', 'TEXT'),
                ('company_logo_url', 'VARCHAR(200)'),
                ('company_website', 'VARCHAR(200)'),
                ('company_phone', 'VARCHAR(20)'),
                ('company_address', 'TEXT')
            ]
            
            # Add each column if it doesn't exist
            for column_name, column_type in columns_to_add:
                try:
                    sql = f'ALTER TABLE "user" ADD COLUMN IF NOT EXISTS {column_name} {column_type}'
                    db.session.execute(text(sql))
                    print(f"✓ Added column: {column_name}")
                except Exception as e:
                    print(f"✗ Error adding column {column_name}: {e}")
            
            # Create Wishlist table if it doesn't exist
            try:
                wishlist_sql = """
                CREATE TABLE IF NOT EXISTS wishlist (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES "user"(id),
                    product_id INTEGER NOT NULL REFERENCES product(id),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT unique_user_product_wishlist UNIQUE (user_id, product_id)
                )
                """
                db.session.execute(text(wishlist_sql))
                print("✓ Created/verified wishlist table")
            except Exception as e:
                print(f"✗ Error creating wishlist table: {e}")
            
            # Create ProductView table if it doesn't exist
            try:
                product_view_sql = """
                CREATE TABLE IF NOT EXISTS product_view (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES "user"(id),
                    product_id INTEGER NOT NULL REFERENCES product(id),
                    view_type VARCHAR(20) NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                db.session.execute(text(product_view_sql))
                print("✓ Created/verified product_view table")
            except Exception as e:
                print(f"✗ Error creating product_view table: {e}")
            
            # Commit all changes
            db.session.commit()
            print("\n🎉 Migration completed successfully!")
            print("Your database is now updated with the new user profile fields.")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {e}")
            print("Please check your database connection and try again.")

if __name__ == '__main__':
    migrate_user_table()
