"""
Seed database using pymysql (synchronous)
This bypasses the async/SSL issues with aiomysql
"""
import pymysql
from app.config.settings import settings

def run_sql_file(cursor, filepath):
    """Execute SQL file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split by semicolon and execute each statement
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    for statement in statements:
        if statement:
            try:
                cursor.execute(statement)
                print(f"✓ Executed: {statement[:60]}...")
            except Exception as e:
                if 'Duplicate entry' in str(e):
                    print(f"⚠ Skipped (already exists): {statement[:60]}...")
                else:
                    print(f"✗ Error: {e}")
                    print(f"  Statement: {statement[:100]}...")

def main():
    print("="*70)
    print("SEEDING DATABASE WITH PYMYSQL")
    print("="*70)
    
    print(f"\nConnecting to: {settings.db_host}:{settings.db_port}")
    print(f"Database: {settings.db_name}")
    
    try:
        # Connect with SSL
        conn = pymysql.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            ssl={'ssl': True}
        )
        
        print("✓ Connected successfully!")
        
        cursor = conn.cursor()
        
        # Run seed script
        print("\nRunning seed script...")
        run_sql_file(cursor, 'migrations/seed_dummy_data.sql')
        
        # Commit
        conn.commit()
        print("\n✓ All changes committed!")
        
        # Verify
        print("\n" + "="*70)
        print("VERIFICATION")
        print("="*70)
        
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        print(f"Vehicles: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM trip_cards")
        print(f"Trip Cards: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM trip_card_pincode")
        print(f"Pincode Mappings: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM allocation_batches")
        print(f"Allocation Batches: {cursor.fetchone()[0]}")
        
        print("\n" + "="*70)
        print("✓ SEEDING COMPLETE!")
        print("="*70)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
