#!/usr/bin/env python3
"""
Quick script to clear rate limiting for development.
Run this if you're still getting 429 errors after the code fix.
"""

import redis
import sys
from app.core.config import Settings

def clear_auth_rate_limits():
    """Clear all auth-related rate limits from Redis."""
    settings = Settings()
    
    try:
        # Connect to Redis
        r = redis.Redis.from_url(settings.REDIS_URL)
        
        # Find all rate limit keys for auth endpoints
        auth_keys = r.keys("rate_limit:*:auth")
        
        if auth_keys:
            # Delete all auth rate limit keys
            deleted = r.delete(*auth_keys)
            print(f"✅ Cleared {deleted} auth rate limit entries")
        else:
            print("ℹ️  No auth rate limit entries found")
            
        # Also clear any IP-based rate limits for auth
        ip_auth_keys = r.keys("rate_limit:*auth*")
        if ip_auth_keys:
            deleted = r.delete(*ip_auth_keys)
            print(f"✅ Cleared {deleted} IP-based auth rate limit entries")
            
        print("🎉 Rate limits cleared! You should now be able to use auth endpoints.")
        
    except redis.ConnectionError:
        print("❌ Could not connect to Redis. Make sure Redis is running.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error clearing rate limits: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clear_auth_rate_limits()