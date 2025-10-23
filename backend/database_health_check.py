"""
Master database health check and fix script.
Runs all verification and fixes in the correct order.
"""
import asyncio
import sys

async def run_health_check():
    """Run complete database health check."""
    
    print("\n" + "=" * 80)
    print(" " * 20 + "DATABASE HEALTH CHECK")
    print("=" * 80 + "\n")
    
    # Step 1: Verify schema
    print("STEP 1: Verifying database schema...")
    print("-" * 80)
    from verify_database_schema import verify_database_schema
    schema_ok = await verify_database_schema()
    
    if not schema_ok:
        print("\n⚠️  Schema issues detected. Running fixes...")
        from fix_database_issues import fix_database_issues
        await fix_database_issues()
        
        print("\nRe-verifying schema...")
        schema_ok = await verify_database_schema()
    
    # Step 2: Check issues table
    print("\n\nSTEP 2: Checking issues table...")
    print("-" * 80)
    from check_issues_table import check_issues_table
    await check_issues_table()
    
    # Final summary
    print("\n\n" + "=" * 80)
    print(" " * 25 + "FINAL SUMMARY")
    print("=" * 80 + "\n")
    
    if schema_ok:
        print("✓ Database is healthy and ready to use!")
        print("\nYou can now:")
        print("  1. Restart your backend server")
        print("  2. Trigger a new repository analysis")
        print("  3. Provide feedback on issues")
        return 0
    else:
        print("❌ Database still has issues that need manual intervention")
        print("\nPlease check the errors above and fix manually")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_health_check())
    sys.exit(exit_code)
