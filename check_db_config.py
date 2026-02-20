"""
Check Database Configuration

This script shows your current database configuration and tests the connection.
"""
from app.config.settings import settings

print("="*70)
print("DATABASE CONFIGURATION")
print("="*70)

print(f"\nHost: {settings.db_host}")
print(f"Port: {settings.db_port}")
print(f"User: {settings.db_user}")
print(f"Database: {settings.db_name}")
print(f"Pool Size: {settings.db_pool_size}")

print(f"\nDatabase URL: {settings.database_url}")

# Check if it's a local or cloud database
is_local = settings.db_host in ['localhost', '127.0.0.1', '0.0.0.0']
is_tidb_cloud = 'tidbcloud.com' in settings.db_host

print(f"\nDatabase Type:")
if is_local:
    print("  ✓ LOCAL DATABASE (No SSL required)")
    print("  Make sure MySQL/MariaDB is running locally")
elif is_tidb_cloud:
    print("  ✓ TIDB CLOUD (SSL required)")
    print("  Cloud database connection")
else:
    print("  ✓ REMOTE DATABASE")
    print("  May require SSL depending on configuration")

print("\n" + "="*70)
print("To change database:")
print("1. Edit .env file")
print("2. Update DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME")
print("="*70)

# Test connection
print("\nTesting connection...")
import asyncio
from app.database.connection import init_db, close_db, check_db_health

async def test():
    try:
        await init_db()
        result = await check_db_health()
        print(f"\nConnection Status: {result['status'].upper()}")
        if result['status'] == 'healthy':
            print("✓ Database connection successful!")
        else:
            print(f"✗ Database connection failed: {result.get('error', 'Unknown error')}")
        await close_db()
    except Exception as e:
        print(f"✗ Error: {e}")

asyncio.run(test())
