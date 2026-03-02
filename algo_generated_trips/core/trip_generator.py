"""
Trip generator module - Groups orders by zone and generates trips with vehicle assignment
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.allocation_engine import AllocationEngine
from core.config import generate_trip_name, get_area_code
from core.zone_vehicle_manager import ZoneVehicleManager
from collections import Counter, defaultdict

def group_orders_by_zone(orders: list) -> dict:
    """
    Group orders by their zone
    
    Args:
        orders: List of order dictionaries with zone_name
    
    Returns:
        Dictionary mapping zone_name to list of orders
    """
    zone_orders = defaultdict(list)
    
    for order in orders:
        zone = order.get('zone_name', 'UNKNOWN')
        zone_orders[zone].append(order)
    
    print(f"\n📍 Grouped orders into {len(zone_orders)} zones:")
    for zone, orders_list in sorted(zone_orders.items()):
        total_weight = sum(o['total_weight_kg'] for o in orders_list)
        print(f"   {zone}: {len(orders_list)} orders ({total_weight:.1f} kg)")
    
    return dict(zone_orders)

def run_allocation_algorithm(orders: list, vehicle_capacity: float, zone_name: str = None) -> dict:
    """
    Run AllocationEngine on orders
    
    Args:
        orders: List of orders formatted for algorithm
        vehicle_capacity: Vehicle capacity in kg
        zone_name: Optional zone name for logging
    
    Returns:
        Algorithm output with trips and metrics
    """
    zone_label = f" for {zone_name}" if zone_name else ""
    print(f"\n🚚 Running allocation{zone_label}...")
    print(f"   Vehicle capacity: {vehicle_capacity} kg")
    print(f"   Total orders: {len(orders)}")
    
    engine = AllocationEngine(vehicle_capacity_kg=vehicle_capacity)
    result = engine.run(orders)
    
    return result

def assign_trip_names_and_vehicles(zone_trips: dict, zone_vehicle_manager: ZoneVehicleManager) -> dict:
    """
    Assign trip names and vehicles to all zone trips
    Uses zone-specific vehicle assignments
    
    Args:
        zone_trips: Dictionary mapping zone_name to list of trips
        zone_vehicle_manager: ZoneVehicleManager instance for vehicle assignment
    
    Returns:
        Dictionary with named trips, assignments, and metrics
    """
    print(f"\n🏷️  Assigning trip names and vehicles...")
    
    all_named_trips = []
    all_assignments = {}
    zone_trip_counters = {}
    zone_vehicle_indices = {}  # Track vehicle index per zone
    
    total_metrics = {
        'total_trips': 0,
        'total_distance_km': 0,
        'total_weight_kg': 0,
        'total_capacity_kg': 0
    }
    
    for zone_name, zone_data in sorted(zone_trips.items()):
        trips = zone_data['trips']
        zone_trip_counters[zone_name] = 0
        zone_vehicle_indices[zone_name] = 0  # Start at index 0 for each zone
        
        for trip in trips:
            zone_trip_counters[zone_name] += 1
            trip_number = zone_trip_counters[zone_name]
            
            # Generate trip name
            trip_name = generate_trip_name(zone_name, trip_number)
            
            # Get next vehicle for this zone
            vehicle, next_index = zone_vehicle_manager.get_next_vehicle_for_zone(
                zone_name, 
                zone_vehicle_indices[zone_name]
            )
            zone_vehicle_indices[zone_name] = next_index
            
            # Calculate utilization based on assigned vehicle capacity
            utilization = round((trip['total_weight'] / vehicle['capacity_kg']) * 100, 1)
            
            # Create named trip
            named_trip = {
                'trip_id': trip['trip_id'],
                'trip_name': trip_name,
                'zone': zone_name,
                'vehicle_id': vehicle['vehicle_id'],
                'vehicle_number': vehicle['vehicle_number'],
                'vehicle_capacity_kg': vehicle['capacity_kg'],
                'orders': trip['orders'],
                'order_count': len(trip['orders']),
                'total_weight': trip['total_weight'],
                'utilization_percent': utilization
            }
            
            all_named_trips.append(named_trip)
            
            # Map each order to its trip
            for order_id in trip['orders']:
                all_assignments[order_id] = {
                    'trip_name': trip_name,
                    'vehicle_number': vehicle['vehicle_number'],
                    'zone': zone_name
                }
            
            # Update metrics
            total_metrics['total_trips'] += 1
            total_metrics['total_weight_kg'] += trip['total_weight']
            total_metrics['total_capacity_kg'] += vehicle['capacity_kg']
            
            print(f"   {trip_name} → {vehicle['vehicle_number']} ({vehicle['capacity_kg']}kg): "
                  f"{len(trip['orders'])} orders, {trip['total_weight']}kg ({utilization}%)")
    
    # Calculate distance from zone metrics
    for zone_data in zone_trips.values():
        total_metrics['total_distance_km'] += zone_data['metrics']['total_distance_km']
    
    # Calculate average utilization
    avg_utilization = round(
        (total_metrics['total_weight_kg'] / total_metrics['total_capacity_kg'] * 100), 1
    ) if total_metrics['total_capacity_kg'] > 0 else 0
    
    final_metrics = {
        'number_of_trips': total_metrics['total_trips'],
        'total_distance_km': round(total_metrics['total_distance_km'], 2),
        'average_utilization_percent': avg_utilization,
        'total_weight_kg': round(total_metrics['total_weight_kg'], 2),
        'total_capacity_kg': round(total_metrics['total_capacity_kg'], 2)
    }
    
    return {
        'trips': all_named_trips,
        'assignments': all_assignments,
        'metrics': final_metrics
    }

def generate_trips_for_day(orders_data: dict, default_capacity: float = 1500) -> dict:
    """
    Complete workflow to generate zone-based trips with vehicle assignment
    
    Args:
        orders_data: Output from order_fetcher.fetch_orders_for_day()
        default_capacity: Default capacity (used as fallback, actual capacity from vehicles)
    
    Returns:
        Dictionary with named trips, vehicle assignments, and all details
    """
    orders = orders_data['orders']
    order_details = orders_data['order_details']
    
    if not orders:
        print("❌ No orders to process!")
        return None
    
    # Step 1: Group orders by zone
    zone_orders = group_orders_by_zone(orders)
    
    # Step 2: Initialize zone-vehicle manager
    zone_vehicle_manager = ZoneVehicleManager()
    
    # Step 3: Generate trips for each zone
    zone_trips = {}
    
    for zone_name, zone_order_list in zone_orders.items():
        print(f"\n{'='*60}")
        print(f"Processing zone: {zone_name}")
        print(f"{'='*60}")
        
        # Prepare orders for algorithm (need full details for clustering)
        algo_orders = [
            {
                'order_id': o['order_id'],
                'latitude': o['latitude'],
                'longitude': o['longitude'],
                'total_weight_kg': o['total_weight_kg']
            }
            for o in zone_order_list
        ]
        
        # Run allocation for this zone (use default capacity for clustering)
        result = run_allocation_algorithm(algo_orders, default_capacity, zone_name)
        
        zone_trips[zone_name] = {
            'trips': result['trips'],
            'metrics': result['metrics']
        }
    
    # Step 4: Assign trip names and vehicles to all trips
    # Vehicles are assigned per zone based on zone_vehicles table
    final_result = assign_trip_names_and_vehicles(zone_trips, zone_vehicle_manager)
    
    # Step 5: Add order details to result
    final_result['order_details'] = order_details
    final_result['zone_summary'] = {
        zone: {
            'order_count': len(zone_orders[zone]),
            'trip_count': len([t for t in final_result['trips'] if t['zone'] == zone])
        }
        for zone in zone_orders.keys()
    }
    
    return final_result
