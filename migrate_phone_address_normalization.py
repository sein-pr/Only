#!/usr/bin/env python3
"""
Migration script to normalize phone numbers and addresses in the User table.
This script adds new structured fields while keeping the old ones for backward compatibility.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models.models import db

def migrate_phone_address_normalization():
    """Add new structured phone and address fields to the User table"""
    
    with app.app_context():
        try:
            # Add new phone fields
            print("Adding phone normalization fields...")
            db.engine.execute(text("""
                ALTER TABLE user 
                ADD COLUMN phone_country_code VARCHAR(5),
                ADD COLUMN phone_number VARCHAR(15)
            """))
            print("✅ Phone normalization fields added")
            
            # Add new address fields
            print("Adding address normalization fields...")
            db.engine.execute(text("""
                ALTER TABLE user 
                ADD COLUMN address_line1 VARCHAR(100),
                ADD COLUMN address_line2 VARCHAR(100),
                ADD COLUMN city VARCHAR(50),
                ADD COLUMN state_province VARCHAR(50),
                ADD COLUMN postal_code VARCHAR(20),
                ADD COLUMN country VARCHAR(50)
            """))
            print("✅ Address normalization fields added")
            
            # Add new company phone fields
            print("Adding company phone normalization fields...")
            db.engine.execute(text("""
                ALTER TABLE user 
                ADD COLUMN company_phone_country_code VARCHAR(5),
                ADD COLUMN company_phone_number VARCHAR(15)
            """))
            print("✅ Company phone normalization fields added")
            
            # Add new company address fields
            print("Adding company address normalization fields...")
            db.engine.execute(text("""
                ALTER TABLE user 
                ADD COLUMN company_address_line1 VARCHAR(100),
                ADD COLUMN company_address_line2 VARCHAR(100),
                ADD COLUMN company_city VARCHAR(50),
                ADD COLUMN company_state_province VARCHAR(50),
                ADD COLUMN company_postal_code VARCHAR(20),
                ADD COLUMN company_country VARCHAR(50)
            """))
            print("✅ Company address normalization fields added")
            
            print("\n🎉 Migration completed successfully!")
            print("New structured fields have been added to the User table.")
            print("The old fields (phone, address, company_phone, company_address) are kept for backward compatibility.")
            
        except SQLAlchemyError as e:
            print(f"❌ Migration failed: {e}")
            return False
            
    return True

if __name__ == "__main__":
    print("Starting phone and address normalization migration...")
    print("This will add new structured fields to the User table.\n")
    
    # Confirm before proceeding
    response = input("Do you want to proceed with the migration? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        sys.exit(0)
    
    success = migrate_phone_address_normalization()
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
