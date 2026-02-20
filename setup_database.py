"""
Complete Database Setup
1. Run migration (create tables)
2. Seed dummy data
"""
import pymysql
from app.config.settings import settings

def run_sql_file(cursor, filepath, description):
    """Execute SQL file."""
    print(f"\n{description}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Split by semicolon and execute each statement
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    executed = 0
    skipped = 0
    errors = 0
    
    for statement in statements:
        # Skip comments and empty statements
        if not statement or statement.startswith('--') or statement.startswith('/*'):
            continue
            
        try:
            cursor.execute(statement)
            executed += 1
            if executed <= 5 or executed % 10 == 0:
                print(f"  OK Executed statement {executed}")
        except Exception as e:
            error_msg = str(e)
            if 'Duplicate entry' in error_msg or 'already exists' in error_msg:
                skipped += 1
            else:
                errors += 1
                if errors <= 3:  # Only show first 3 errors
                    print(f"  X Error: {error_msg[:100]}")
    
    print(f"  Summary: {executed} executed, {skipped} skipped, {errors} errors")
    return executed, skipped, errors

def main():
    print("="*70)
    print("DATABASE SETUP - MIGRATION + SEEDING")
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
            ssl={'ssl': True},
            autocommit=False
        )
        
        print("OK Connected successfully!")
        
        cursor = conn.cursor()
        
        # Step 1: Run migration
        print("\n" + "="*70)
        print("STEP 1: RUNNING MIGRATION")
        print("="*70)
        exec1, skip1, err1 = run_sql_file(cursor, 'migrations/phase1_vehicle_allocation.sql', 'Creating tables')
        conn.commit()
        print("OK Migration committed!")
        
        # Step 2: Run seeding
        print("\n" + "="*70)
        print("STEP 2: SEEDING DATA")
        print("="*70)
        exec2, skip2, err2 = run_sql_file(cursor, 'migrations/seed_dummy_data.sql', 'Inserting dummy data')
        conn.commit()
        print("OK Seeding committed!")
        
        # Step 3: Verify
        print("\n" + "="*70)
        print("STEP 3: VERIFICATION")
        print("="*70)
        
        tables = [
            ('vehicles', 'Vehicles'),
            ('trip_cards', 'Trip Cards'),
            ('trip_card_pincode', 'Pincode Mappings'),
            ('allocation_batches', 'Allocation Batches')
        ]
        
        for table, label in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  OK {label}: {count} records")
            except Exception as e:
                print(f"  X {label}: Error - {e}")
        
        # Show sample data
        print("\n" + "="*70)
        print("SAMPLE DATA")
        print("="*70)
        
        print("\nVehicles (first 5):")
        cursor.execute("SELECT vehicle_number, capacity_kg, is_active FROM vehicles LIMIT 5")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} kg, Active: {row[2]}")
        
        print("\nTrip Cards (first 5):")
        cursor.execute("""
            SELECT tc.zone_name, v.vehicle_number, tc.status 
            FROM trip_cards tc 
            LEFT JOIN vehicles v ON tc.vehicle_id = v.vehicle_id 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            vehicle = row[1] if row[1] else 'Unassigned'
            print(f"  - {row[0]}: {vehicle}, Status: {row[2]}")
        
        print("\n" + "="*70)
        print("OK SETUP COMPLETE!")
        print("="*70)
        print("\nYou can now:")
        print("  1. Test allocation: python test_real_data.py")
        print("  2. Start API server: uvicorn app.main:app --reload")
        print("  3. View API docs: http://localhost:8000/docs")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\nX Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
