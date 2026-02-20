"""
Simple database connection test for TiDB Cloud
"""
import asyncio
import aiomysql
from app.config.settings import settings

async def test_connection():
    """Test direct connection to TiDB Cloud."""
    print("Testing TiDB Cloud connection...")
    print(f"Host: {settings.db_host}")
    print(f"Port: {settings.db_port}")
    print(f"User: {settings.db_user}")
    print(f"Database: {settings.db_name}")
    
    try:
        # Try connection with SSL
        print("\nAttempting connection with SSL...")
        conn = await aiomysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            db=settings.db_name,
            ssl=True
        )
        
        print("✓ Connection successful!")
        
        # Test query
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT 1 as test")
            result = await cursor.fetchone()
            print(f"✓ Query test: {result}")
            
            # Check tables
            await cursor.execute("SHOW TABLES")
            tables = await cursor.fetchall()
            print(f"✓ Found {len(tables)} tables:")
            for table in tables[:10]:
                print(f"  - {table[0]}")
        
        conn.close()
        print("\n✓ Connection test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
