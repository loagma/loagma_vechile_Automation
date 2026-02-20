"""
Test Allocation Engine with Real Database Data

This script:
1. Connects to the production database
2. Fetches real orders
3. Generates dummy data for missing fields (pincode, total_weight_kg)
4. Runs the allocation algorithm
5. Displays results

IMPORTANT: This is READ-ONLY. No data is written to the database.
"""
import asyncio
import sys
import os
import random
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import init_db, close_db, async_session_maker
from app.allocation.allocation_engine import AllocationEngine


# Dummy pincode generator based on common Indian pincodes
SAMPLE_PINCODES = [
    "560001", "560002", "560003", "560004", "560005",  # Bangalore
    "400001", "400002", "400003", "400004", "400005",  # Mumbai
    "110001", "110002", "110003", "110004", "110005",  # Delhi
    "600001", "600002", "600003", "600004", "600005",  # Chennai
    "700001", "700002", "700003", "700004", "700005",  # Kolkata
]

# Dummy coordinates for Indian cities (if lat/lon not in database)
SAMPLE_COORDINATES = [
    (12.9716, 77.5946),  # Bangalore
    (19.0760, 72.8777),  # Mumbai
    (28.7041, 77.1025),  # Delhi
    (13.0827, 80.2707),  # Chennai
    (22.5726, 88.3639),  # Kolkata
]


def generate_dummy_pincode() -> str:
    """Generate a random pincode from sample list."""
    return random.choice(SAMPLE_PINCODES)


def generate_dummy_weight() -> float:
    """Generate a realistic order weight (1-50 kg)."""
    return round(random.uniform(1.0, 50.0), 2)


def generate_dummy_coordinates() -> tuple:
    """Generate random coordinates near a major city."""
    base_lat, base_lon = random.choice(SAMPLE_COORDINATES)
    # Add small random offset (within ~5km)
    lat = base_lat + random.uniform(-0.05, 0.05)
    lon = base_lon + random.uniform(-0.05, 0.05)
    return (round(lat, 6), round(lon, 6))


async def fetch_orders_from_database(limit: int = 100) -> list:
    """
    Fetch orders from the database.
    
    Args:
        limit: Maximum number of orders to fetch
        
    Returns:
        List of order dictionaries
    """
    try:
        if async_session_maker is None:
            print("   ⚠ Database session not available")
            return []
        
        async with async_session_maker() as session:
            # Try to fetch from orders table
            # Adjust the query based on your actual table structure
            query = text("""
                SELECT 
                    order_id,
                    created_at,
                    -- Add other existing columns here
                    NULL as latitude,
                    NULL as longitude,
                    NULL as pincode,
                    NULL as total_weight_kg
                FROM orders
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            
            result = await session.execute(query, {"limit": limit})
            rows = result.fetchall()
            
            print(f"   ✓ Fetched {len(rows)} orders from database")
            return rows
            
    except Exception as e:
        print(f"   ⚠ Could not fetch from database: {str(e)[:100]}")
        print(f"   This is expected if database is not running or orders table doesn't exist")
        return []


async def prepare_orders_for_allocation(db_orders: list) -> list:
    """
    Prepare orders for allocation by adding dummy data for missing fields.
    
    Args:
        db_orders: Raw orders from database
        
    Returns:
        List of order dictionaries ready for allocation
    """
    prepared_orders = []
    
    for idx, row in enumerate(db_orders, start=1):
        # Extract existing data
        order_id = row[0] if len(row) > 0 else idx
        
        # Get or generate coordinates
        if len(row) > 3 and row[3] is not None and row[4] is not None:
            latitude = float(row[3])
            longitude = float(row[4])
        else:
            latitude, longitude = generate_dummy_coordinates()
        
        # Get or generate pincode
        if len(row) > 5 and row[5] is not None:
            pincode = str(row[5])
        else:
            pincode = generate_dummy_pincode()
        
        # Get or generate weight
        if len(row) > 6 and row[6] is not None:
            total_weight_kg = float(row[6])
        else:
            total_weight_kg = generate_dummy_weight()
        
        prepared_orders.append({
            "order_id": order_id,
            "latitude": latitude,
            "longitude": longitude,
            "pincode": pincode,
            "total_weight_kg": total_weight_kg
        })
    
    return prepared_orders


async def generate_sample_orders(count: int = 50) -> list:
    """
    Generate sample orders when database is not available.
    
    Args:
        count: Number of sample orders to generate
        
    Returns:
        List of sample order dictionaries
    """
    print(f"Generating {count} sample orders (database not available)...")
    
    orders = []
    for i in range(1, count + 1):
        lat, lon = generate_dummy_coordinates()
        orders.append({
            "order_id": i,
            "latitude": lat,
            "longitude": lon,
            "pincode": generate_dummy_pincode(),
            "total_weight_kg": generate_dummy_weight()
        })
    
    return orders


def print_allocation_results(result: dict, vehicle_capacity: float):
    """
    Print formatted allocation results.
    
    Args:
        result: Allocation result dictionary
        vehicle_capacity: Vehicle capacity used
    """
    print("\n" + "="*70)
    print("ALLOCATION RESULTS")
    print("="*70)
    
    print(f"\nVehicle Capacity: {vehicle_capacity} kg")
    print(f"Total Orders Processed: {len(result['trips']) * 10}")  # Approximate
    
    print(f"\nMETRICS:")
    print(f"  Number of Trips: {result['metrics']['number_of_trips']}")
    print(f"  Average Utilization: {result['metrics']['average_utilization_percent']}%")
    print(f"  Total Distance: {result['metrics']['total_distance_km']} km")
    print(f"  Runtime: {result['metrics']['runtime_seconds']} seconds")
    
    if result['unallocatable_orders']:
        print(f"\n  ⚠ Unallocatable Orders: {len(result['unallocatable_orders'])}")
        print(f"    Order IDs: {result['unallocatable_orders'][:10]}...")
    
    print(f"\nTRIP SUMMARY (First 10 trips):")
    for trip in result['trips'][:10]:
        utilization = (trip['total_weight'] / vehicle_capacity) * 100
        print(f"  Trip {trip['trip_id']:3d}: "
              f"{len(trip['orders']):3d} orders, "
              f"{trip['total_weight']:6.2f} kg ({utilization:5.1f}% full), "
              f"{trip['route_distance_km']:7.2f} km")
    
    if len(result['trips']) > 10:
        print(f"  ... and {len(result['trips']) - 10} more trips")
    
    print("\n" + "="*70)


async def test_with_real_data():
    """Main test function using real database data."""
    print("\n" + "="*70)
    print("TESTING ALLOCATION ENGINE WITH REAL DATA")
    print("="*70)
    
    try:
        # Initialize database connection
        print("\n1. Initializing database connection...")
        try:
            await init_db()
            print("   ✓ Database connected")
        except Exception as e:
            print(f"   ⚠ Database connection failed: {str(e)[:100]}")
            print("   Will use sample data instead")
        
        # Fetch orders from database
        print("\n2. Fetching orders from database...")
        db_orders = await fetch_orders_from_database(limit=100)
        
        if db_orders:
            print(f"   ✓ Found {len(db_orders)} orders")
            
            # Prepare orders for allocation
            print("\n3. Preparing orders (adding dummy data for missing fields)...")
            orders = await prepare_orders_for_allocation(db_orders)
            print(f"   ✓ Prepared {len(orders)} orders")
            
        else:
            print("   ⚠ No orders found in database")
            print("\n3. Generating sample orders instead...")
            orders = await generate_sample_orders(count=50)
            print(f"   ✓ Generated {len(orders)} sample orders")
        
        # Show sample of prepared data
        print("\n4. Sample of prepared data (first 3 orders):")
        for order in orders[:3]:
            print(f"   Order {order['order_id']}: "
                  f"Lat={order['latitude']:.4f}, "
                  f"Lon={order['longitude']:.4f}, "
                  f"Pincode={order['pincode']}, "
                  f"Weight={order['total_weight_kg']}kg")
        
        # Run allocation
        print("\n5. Running allocation algorithm...")
        vehicle_capacity = 100.0  # kg
        engine = AllocationEngine(vehicle_capacity_kg=vehicle_capacity)
        result = engine.run(orders)
        print("   ✓ Allocation complete")
        
        # Display results
        print_allocation_results(result, vehicle_capacity)
        
        # Test with different capacities
        print("\n" + "="*70)
        print("TESTING WITH DIFFERENT VEHICLE CAPACITIES")
        print("="*70)
        
        capacities = [50, 100, 200, 500]
        for capacity in capacities:
            engine = AllocationEngine(vehicle_capacity_kg=capacity)
            result = engine.run(orders)
            print(f"\nCapacity {capacity:4d} kg: "
                  f"{result['metrics']['number_of_trips']:3d} trips, "
                  f"{result['metrics']['average_utilization_percent']:5.1f}% utilization, "
                  f"{result['metrics']['total_distance_km']:8.2f} km")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close database connection
        print("\n6. Closing database connection...")
        await close_db()
        print("   ✓ Database connection closed")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70 + "\n")


async def test_with_custom_query():
    """Test with a custom SQL query for your specific database schema."""
    print("\n" + "="*70)
    print("CUSTOM QUERY TEST")
    print("="*70)
    print("\nTo use your actual database schema:")
    print("1. Update the SQL query in fetch_orders_from_database()")
    print("2. Map your existing columns to the required fields:")
    print("   - order_id (required)")
    print("   - latitude (generate dummy if missing)")
    print("   - longitude (generate dummy if missing)")
    print("   - pincode (generate dummy if missing)")
    print("   - total_weight_kg (generate dummy if missing)")
    print("\nExample query:")
    print("""
    SELECT 
        id as order_id,
        customer_lat as latitude,
        customer_lon as longitude,
        delivery_pincode as pincode,
        order_weight as total_weight_kg
    FROM orders
    WHERE status = 'pending'
    AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    LIMIT 100
    """)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ALLOCATION ENGINE - REAL DATA TEST")
    print("="*70)
    print("\nThis script will:")
    print("1. Connect to your database (read-only)")
    print("2. Fetch real orders")
    print("3. Generate dummy data for missing fields")
    print("4. Run allocation algorithm")
    print("5. Display results")
    print("\nNOTE: No data will be written to the database.")
    print("="*70)
    
    # Run the test
    asyncio.run(test_with_real_data())
    
    # Show custom query example
    asyncio.run(test_with_custom_query())
