#!/usr/bin/env python3
"""
Test script to verify the platform analytics endpoint works.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.admin_service import AdminService


async def test_platform_analytics():
    """Test the platform analytics method."""
    db = SessionLocal()
    
    try:
        admin_service = AdminService(db)
        
        print("Testing platform analytics...")
        
        # Call the platform analytics method
        analytics = await admin_service.get_platform_analytics()
        
        print("Platform Analytics Results:")
        for key, value in analytics.items():
            print(f"- {key}: {value}")
        
        print("\n✅ Platform analytics test completed successfully!")
        
        return analytics
        
    except Exception as e:
        print(f"❌ Error testing platform analytics: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()


if __name__ == "__main__":
    print("=== Platform Analytics Test ===\n")
    asyncio.run(test_platform_analytics())