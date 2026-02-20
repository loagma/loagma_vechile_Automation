"""
Seed Dummy Data to Database

This script creates dummy data for testing the vehicle allocation system:
1. Vehicles
2. Trip Cards (Zones)
3. Trip Card Pincodes
4. Allocation Batches
5. Sample Orders (if orders table exists)

IMPORTANT: This will INSERT data into your database.
"""
import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import text
from app.database.connection import init_db, close_db, async_session_maker


# Sample data for Indian cities
CITIES_DATA = [
    {
        "name": "Bangalore",
        "pincodes": ["560001", "560002", "560003", "560004", "560005", "560006", "560007", "560008"],
        "base_lat": 12.9716,
        "base_lon": 77.5946
    },
    {
        "name": "Mumbai",
        "pincodes": ["400001", "400002", "400003", "400004", "400005", "400006", "400007", "400008"],
        "base_lat": 19.0760,
        "base_lon": 72.8777
    },
    {
        "name": "Delhi",
        "pincodes": ["110001", "110002", "110003", "110004", "110005", "110006", "110007", "110008"],
        "base_lat": 28.7041,
        "base_lon": 77.1025
    },
    {
        "name": "Chennai",
        "pincodes": ["600001", "600002", "600003", "600004", "600005", "600006", "600007", "600008"],
        "base_lat": 13.0827,
        "base_lon": 80.2707
    },
]


async def seed_vehicles(session, count: int = 10):
    """Seed vehicle data."""
    print(f"\n1. Seeding {count} vehicles...")
    
    vehicles = []
    for i in range(1, count + 1):
        vehicle_number = f"KA{random.randint(10, 99)}AB{random.randint(1000, 9999)}"
        capacity = random.choice([100, 150, 200, 250, 300, 500])
        
        query = text("""
            INSERT INTO vehicles (vehicle_number, capacity_kg, is_active)
            VALUES (:vehicle_number, :capacity_kg, :is_active)
        """)
        
        await session.execute(query, {
            "vehicle_number": vehicle_number,
            "capacity_kg": capacity,
            "is_active": True
        })
        
        vehicles.append({
            "number": vehicle_number,
            "capacity": capacity
        })
    
    await session.commit()
    print(f"   ✓ Created {count} vehicles")
    for v in vehicles[:5]:
        print(f"     - {v['number']}: {v['capacity']} kg")
    if len(vehicles) > 5:
        print(f"     ... and {len(vehicles) - 5} more")
    
    return vehicles


async def seed_trip_cards(session, count: int = 20):
    """Seed trip card (zone) data."""
    print(f"\n2. Seeding {count} trip cards (zones)...")
    
    # Get vehicle IDs
    result = await session.execute(text("SELECT vehicle_id FROM vehicles LIMIT 10"))
    vehicle_ids = [row[0] for row in result.fetchall()]
    
    trip_cards = []
    for i in range(1, count + 1):
        city = random.choice(CITIES_DATA)
        zone_name = f"{city['name']} Zone {i}"
        vehicle_id = random.choice(vehicle_ids) if vehicle_ids and random.random() > 0.3 else None
        status = random.choice(['IDLE', 'IDLE', 'IDLE', 'ACTIVE', 'OVERWEIGHT'])
        
        query = text("""
            INSERT INTO trip_cards (zone_name, vehicle_id, status)
            VALUES (:zone_name, :vehicle_id, :status)
        """)
        
        await session.execute(query, {
            "zone_name": zone_name,
            "vehicle_id": vehicle_id,
            "status": status
        })
        
        trip_cards.append({
            "name": zone_name,
            "vehicle_id": vehicle_id,
            "status": status
        })
    
    await session.commit()
    print(f"   ✓ Created {count} trip cards")
    for tc in trip_cards[:5]:
        print(f"     - {tc['name']}: {tc['status']}")
    if len(trip_cards) > 5:
        print(f"     ... and {len(trip_cards) - 5} more")
    
    return trip_cards


async def seed_trip_card_pincodes(session):
    """Seed pincode mappings to trip cards."""
    print(f"\n3. Seeding trip card pincodes...")
    
    # Get zone IDs
    result = await session.execute(text("SELECT zone_id, zone_name FROM trip_cards"))
    zones = result.fetchall()
    
    total_mappings = 0
    for zone_id, zone_name in zones:
        # Extract city from zone name
        city_name = zone_name.split(" Zone")[0]
        city_data = next((c for c in CITIES_DATA if c['name'] == city_name), None)
        
        if city_data:
            # Assign 2-4 pincodes per zone
            num_pincodes = random.randint(2, 4)
            pincodes = random.sample(city_data['pincodes'], min(num_pincodes, len(city_data['pincodes'])))
            
            for pincode in pincodes:
                query = text("""
                    INSERT INTO trip_card_pincode (zone_id, pincode)
                    VALUES (:zone_id, :pincode)
                    ON DUPLICATE KEY UPDATE zone_id = zone_id
                """)
                
                await session.execute(query, {
                    "zone_id": zone_id,
                    "pincode": pincode
                })
                total_mappings += 1
    
    await session.commit()
    print(f"   ✓ Created {total_mappings} pincode mappings")


async def seed_allocation_batches(session, count: int = 5):
    """Seed allocation batch data."""
    print(f"\n4. Seeding {count} allocation batches...")
    
    batches = []
    for i in range(count):
        window_start = datetime.now() - timedelta(days=count-i)
        window_end = window_start + timedelta(hours=2)
        triggered_by = random.choice(['CRON', 'CRON', 'ADMIN'])
        status = random.choice(['COMPLETED', 'COMPLETED', 'COMPLETED', 'RUNNING', 'FAILED'])
        
        query = text("""
            INSERT INTO allocation_batches (window_start, window_end, triggered_by, status)
            VALUES (:window_start, :window_end, :triggered_by, :status)
        """)
        
        await session.execute(query, {
            "window_start": window_start,
            "window_end": window_end,
            "triggered_by": triggered_by,
            "status": status
        })
        
        batches.append({
            "window": f"{window_start.strftime('%Y-%m-%d %H:%M')} - {window_end.strftime('%H:%M')}",
            "status": status
        })
    
    await session.commit()
    print(f"   ✓ Created {count} allocation batches")
    for b in batches:
        print(f"     - {b['window']}: {b['status']}")


async def check_orders_table(session):
    """Check if orders table exists and has the new columns."""
    try:
        result = await session.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'orders'
            AND COLUMN_NAME IN ('pincode', 'total_weight_kg', 'allocated_zone_id', 'allocation_batch_id')
        """))
        count = result.scalar()
        return count == 4  # All 4 columns exist
    except Exception as e:
        print(f"   ⚠ Could not check orders table: {e}")
        return False


async def seed_sample_orders(session, count: int = 50):
    """Seed sample orders with allocation data."""
    print(f"\n5. Checking orders table...")
    
    has_columns = await check_orders_table(session)
    
    if not has_columns:
        print("   ⚠ Orders table doesn't have allocation columns yet")
        print("   Run the migration first: migrations/phase1_vehicle_allocation.sql")
        return
    
    print(f"   ✓ Orders table has allocation columns")
    print(f"   Seeding {count} sample orders...")
    
    # Get zone IDs and batch IDs
    zones_result = await session.execute(text("SELECT zone_id FROM trip_cards LIMIT 10"))
    zone_ids = [row[0] for row in zones_result.fetchall()]
    
    batches_result = await session.execute(text("SELECT batch_id FROM allocation_batches LIMIT 5"))
    batch_ids = [row[0] for row in batches_result.fetchall()]
    
    orders = []
    for i in range(1, count + 1):
        city = random.choice(CITIES_DATA)
        pincode = random.choice(city['pincodes'])
        
        # Generate coordinates near city center
        lat = city['base_lat'] + random.uniform(-0.05, 0.05)
        lon = city['base_lon'] + random.uniform(-0.05, 0.05)
        
        weight = round(random.uniform(1.0, 50.0), 2)
        
        # 70% allocated, 30% unallocated
        if random.random() < 0.7 and zone_ids and batch_ids:
            allocated_zone_id = random.choice(zone_ids)
            allocation_batch_id = random.choice(batch_ids)
        else:
            allocated_zone_id = None
            allocation_batch_id = None
        
        try:
            query = text("""
                INSERT INTO orders (pincode, total_weight_kg, allocated_zone_id, allocation_batch_id)
                VALUES (:pincode, :total_weight_kg, :allocated_zone_id, :allocation_batch_id)
            """)
            
            await session.execute(query, {
                "pincode": pincode,
                "total_weight_kg": weight,
                "allocated_zone_id": allocated_zone_id,
                "allocation_batch_id": allocation_batch_id
            })
            
            orders.append({
                "pincode": pincode,
                "weight": weight,
                "allocated": allocated_zone_id is not None
            })
        except Exception as e:
            print(f"   ⚠ Could not insert order: {e}")
            break
    
    if orders:
        await session.commit()
        allocated_count = sum(1 for o in orders if o['allocated'])
        print(f"   ✓ Created {len(orders)} sample orders")
        print(f"     - {allocated_count} allocated")
        print(f"     - {len(orders) - allocated_count} unallocated")


async def verify_data(session):
    """Verify seeded data."""
    print(f"\n6. Verifying seeded data...")
    
    # Count vehicles
    result = await session.execute(text("SELECT COUNT(*) FROM vehicles"))
    vehicle_count = result.scalar()
    print(f"   ✓ Vehicles: {vehicle_count}")
    
    # Count trip cards
    result = await session.execute(text("SELECT COUNT(*) FROM trip_cards"))
    trip_card_count = result.scalar()
    print(f"   ✓ Trip Cards: {trip_card_count}")
    
    # Count pincodes
    result = await session.execute(text("SELECT COUNT(*) FROM trip_card_pincode"))
    pincode_count = result.scalar()
    print(f"   ✓ Pincode Mappings: {pincode_count}")
    
    # Count batches
    result = await session.execute(text("SELECT COUNT(*) FROM allocation_batches"))
    batch_count = result.scalar()
    print(f"   ✓ Allocation Batches: {batch_count}")
    
    # Count orders (if table exists)
    try:
        result = await session.execute(text("SELECT COUNT(*) FROM orders WHERE pincode IS NOT NULL"))
        order_count = result.scalar()
        print(f"   ✓ Orders with allocation data: {order_count}")
    except:
        print(f"   ⚠ Orders table not accessible")


async def main():
    """Main seeding function."""
    print("="*70)
    print("SEEDING DUMMY DATA TO DATABASE")
    print("="*70)
    print("\nThis will INSERT data into your database.")
    print("Make sure you have run the migration first!")
    print("="*70)
    
    try:
        # Initialize database
        print("\nInitializing database connection...")
        await init_db()
        print("✓ Database connected")
        
        # Create session
        async with async_session_maker() as session:
            # Seed data
            await seed_vehicles(session, count=10)
            await seed_trip_cards(session, count=20)
            await seed_trip_card_pincodes(session)
            await seed_allocation_batches(session, count=5)
            await seed_sample_orders(session, count=50)
            
            # Verify
            await verify_data(session)
        
        print("\n" + "="*70)
        print("✓ SEEDING COMPLETE!")
        print("="*70)
        print("\nYou can now:")
        print("1. Test the allocation algorithm with real data")
        print("2. View data in Prisma Studio (if using Prisma)")
        print("3. Query the database to verify data")
        print("\nExample queries:")
        print("  SELECT * FROM vehicles;")
        print("  SELECT * FROM trip_cards;")
        print("  SELECT * FROM trip_card_pincode;")
        print("  SELECT * FROM allocation_batches;")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database
        await close_db()
        print("\n✓ Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
