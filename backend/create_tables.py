#!/usr/bin/env python3
"""
Script to create database tables for CodeNova application.
Run this script to initialize the database with all required tables.
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import Base, engine
from app.models.users import User, Token, UserRole
from app.models.repository import Repository
from app.models.analysis import Analysis

def create_tables():
    """Create all database tables."""
    try:
        print("Creating database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database tables created successfully!")
        print("\nTables created:")
        print("- users")
        print("- tokens") 
        print("- repositories")
        print("- analysis")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def check_tables():
    """Check if tables exist."""
    try:
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("Existing tables:")
        for table in tables:
            print(f"- {table}")
            
        return tables
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return []

if __name__ == "__main__":
    print("CodeNova Database Initialization")
    print("=" * 40)
    
    # Check existing tables
    existing_tables = check_tables()
    
    if not existing_tables:
        print("\nNo tables found. Creating tables...")
        create_tables()
    else:
        print(f"\nFound {len(existing_tables)} existing tables.")
        response = input("Do you want to recreate all tables? (y/N): ")
        if response.lower() == 'y':
            print("Dropping and recreating tables...")
            Base.metadata.drop_all(bind=engine)
            create_tables()
        else:
            print("Keeping existing tables.")
    
    print("\n✅ Database initialization complete!")