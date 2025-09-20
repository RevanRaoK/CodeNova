#!/usr/bin/env python3
"""
Script to check the actual database schema
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import engine
from sqlalchemy import inspect, text

def check_schema():
    """Check the actual database schema."""
    try:
        inspector = inspect(engine)
        
        # Get all tables
        tables = inspector.get_table_names()
        print("Available tables:")
        for table in tables:
            print(f"- {table}")
        
        # Check users table specifically
        if 'users' in tables:
            print("\nUsers table columns:")
            columns = inspector.get_columns('users')
            for column in columns:
                print(f"- {column['name']}: {column['type']}")
        else:
            print("\nUsers table does not exist!")
            
        # Try to query the users table
        print("\nTrying to query users table...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT * FROM users LIMIT 1"))
            print("Query successful!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()