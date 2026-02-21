"""
Test Allocation Engine with REAL Orders from Database

This script fetches actual orders from your database and runs the allocation algorithm.
"""
import pymysql
import json
import random
from app.allocation.allocation_engine import AllocationEngine

def fetch_real_orders(limit=1000, days=2):
    """Fetch real orders from database with coordinates from last N days."""
    print(f"Fetching orders from last {days} days (max {limit})...")
    
    conn = pymysql.connect(
        host='gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
        port=4000,
        user='3JkMn3GrMm4dpze.root',
        password='VNcMbAz5zqDYXKcd',
        database='loagma',
        ssl={'ssl': True}
    )
    
    cursor = conn.cursor()
    
    # Calculate timestamp for N days ago (Unix timestamp)
    import time
    days_ago_timestamp = int(time.time()) - (days * 24 * 60 * 60)
    
    # Fetch orders with delivery_info from last N days
    query = """
        SELECT 
            order_id,
            delivery_info,
            area_name,
            start_time
        FROM orders
        WHERE delivery_info IS NOT NULL
        AND delivery_info != ''
        AND start_time >= %s
        ORDER BY start_time DESC
        LIMIT %s
    """
    
    cursor.execute(query, (days_ago_timestamp, limit))
    rows = cursor.fetchall()
    
    print(f"  Found {len(rows)} orders in database")
    
    orders = []
    skipped = 0
    
    for row in rows:
        order_id = row[0]
        delivery_info = row[1]
        area_name = row[2]
        start_time = row[3]
        
        try:
            # Parse delivery_info JSON
            info = json.loads(delivery_info)
            
            # Extract coordinates
            latitude = info.get('latitude')
            longitude = info.get('longitude')
            
            if latitude and longitude:
                # Generate dummy pincode from area_name or use default
                pincode = area_name[:6] if area_name else '500001'
                
                # Generate dummy weight (1-50 kg)
                weight = round(random.uniform(1.0, 50.0), 2)
                
                orders.append({
                    'order_id': order_id,
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'pincode': pincode,
                    'total_weight_kg': weight,
                    'timestamp': start_time
                })
        except Exception as e:
            skipped += 1
            continue
    
    conn.close()
    
    print(f"✓ Fetched {len(orders)} orders with valid coordinates")
    if skipped > 0:
        print(f"  (Skipped {skipped} orders without valid coordinates)")
    
    return orders


def print_results(result, vehicle_capacity):
    """Print allocation results."""
    print("\n" + "="*70)
    print("ALLOCATION RESULTS - REAL ORDERS")
    print("="*70)
    
    print(f"\nVehicle Capacity: {vehicle_capacity} kg")
    print(f"Total Orders: {sum(len(trip['orders']) for trip in result['trips'])}")
    
    print(f"\nMETRICS:")
    print(f"  Number of Trips: {result['metrics']['number_of_trips']}")
    print(f"  Average Utilization: {result['metrics']['average_utilization_percent']}%")
    print(f"  Total Distance: {result['metrics']['total_distance_km']} km")
    print(f"  Runtime: {result['metrics']['runtime_seconds']} seconds")
    
    if result['unallocatable_orders']:
        print(f"\n  ⚠ Unallocatable Orders: {len(result['unallocatable_orders'])}")
    
    print(f"\nTRIP DETAILS (First 10 trips):")
    for trip in result['trips'][:10]:
        utilization = (trip['total_weight'] / vehicle_capacity) * 100
        print(f"  Trip {trip['trip_id']:3d}: "
              f"{len(trip['orders']):3d} orders, "
              f"{trip['total_weight']:6.2f} kg ({utilization:5.1f}% full), "
              f"{trip['route_distance_km']:7.2f} km")
        print(f"    Order IDs: {trip['orders'][:10]}{'...' if len(trip['orders']) > 10 else ''}")
    
    if len(result['trips']) > 10:
        print(f"  ... and {len(result['trips']) - 10} more trips")
    
    print("\n" + "="*70)


def main():
    print("="*70)
    print("TESTING ALLOCATION WITH REAL ORDERS")
    print("="*70)
    
    # Try different time ranges
    for days in [2, 7, 30, 60]:
        print(f"\nTrying last {days} days...")
        orders = fetch_real_orders(limit=1000, days=days)
        if orders:
            break
    
    if not orders:
        print("\n✗ No orders found with coordinates!")
        print("Fetching most recent 500 orders instead...")
        # Fallback: get most recent orders regardless of date
        orders = fetch_recent_orders(limit=500)
    
    if not orders:
        print("\n✗ Still no orders found!")
        return
    
    # Show date range
    from datetime import datetime
    timestamps = [o['timestamp'] for o in orders]
    oldest = datetime.fromtimestamp(min(timestamps))
    newest = datetime.fromtimestamp(max(timestamps))
    print(f"\nDate Range: {oldest.strftime('%Y-%m-%d %H:%M')} to {newest.strftime('%Y-%m-%d %H:%M')}")
    print(f"Total Orders: {len(orders)}")
    
    # Show sample
    print(f"\nSample orders (first 5):")
    for order in orders[:5]:
        order_time = datetime.fromtimestamp(order['timestamp'])
        print(f"  Order {order['order_id']}: "
              f"Lat={order['latitude']:.4f}, "
              f"Lon={order['longitude']:.4f}, "
              f"Pincode={order['pincode']}, "
              f"Weight={order['total_weight_kg']}kg, "
              f"Time={order_time.strftime('%Y-%m-%d %H:%M')}")
    
    # Run allocation
    print(f"\nRunning allocation algorithm on {len(orders)} orders...")
    vehicle_capacity = 100.0  # kg
    
    engine = AllocationEngine(vehicle_capacity_kg=vehicle_capacity)
    result = engine.run(orders)
    
    # Print results
    print_results(result, vehicle_capacity)
    
    # Test with different capacities
    print("\n" + "="*70)
    print("TESTING WITH DIFFERENT VEHICLE CAPACITIES")
    print("="*70)
    
    capacities = [50, 100, 150, 200, 300, 500]
    
    print(f"\n{'Capacity':<12} {'Trips':<8} {'Utilization':<15} {'Distance':<15} {'Runtime':<12}")
    print("-"*70)
    
    for capacity in capacities:
        engine = AllocationEngine(vehicle_capacity_kg=capacity)
        result = engine.run(orders)
        
        print(f"{capacity:>4d} kg     "
              f"{result['metrics']['number_of_trips']:>4d}     "
              f"{result['metrics']['average_utilization_percent']:>6.1f}%        "
              f"{result['metrics']['total_distance_km']:>8.2f} km    "
              f"{result['metrics']['runtime_seconds']:>6.3f}s")
    
    print("\n" + "="*70)
    print("✓ TEST COMPLETE!")
    print("="*70)
    print(f"\nProcessed {len(orders)} orders")
    print(f"Date range: {oldest.strftime('%Y-%m-%d')} to {newest.strftime('%Y-%m-%d')}")
    print(f"Recommended capacity: 150-200 kg for best efficiency")


def fetch_recent_orders(limit=500):
    """Fetch most recent orders regardless of date."""
    print(f"Fetching {limit} most recent orders...")
    
    conn = pymysql.connect(
        host='gateway01.ap-northeast-1.prod.aws.tidbcloud.com',
        port=4000,
        user='3JkMn3GrMm4dpze.root',
        password='VNcMbAz5zqDYXKcd',
        database='loagma',
        ssl={'ssl': True}
    )
    
    cursor = conn.cursor()
    
    query = """
        SELECT 
            order_id,
            delivery_info,
            area_name,
            start_time
        FROM orders
        WHERE delivery_info IS NOT NULL
        AND delivery_info != ''
        AND start_time > 0
        ORDER BY start_time DESC
        LIMIT %s
    """
    
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    
    print(f"  Found {len(rows)} orders")
    
    orders = []
    skipped = 0
    
    for row in rows:
        order_id = row[0]
        delivery_info = row[1]
        area_name = row[2]
        start_time = row[3]
        
        try:
            info = json.loads(delivery_info)
            latitude = info.get('latitude')
            longitude = info.get('longitude')
            
            if latitude and longitude:
                pincode = area_name[:6] if area_name else '500001'
                weight = round(random.uniform(1.0, 50.0), 2)
                
                orders.append({
                    'order_id': order_id,
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'pincode': pincode,
                    'total_weight_kg': weight,
                    'timestamp': start_time
                })
        except:
            skipped += 1
            continue
    
    conn.close()
    
    print(f"✓ Fetched {len(orders)} orders with valid coordinates")
    if skipped > 0:
        print(f"  (Skipped {skipped} orders)")
    
    return orders


if __name__ == "__main__":
    main()
