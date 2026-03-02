"""
Main script to generate algorithm-based trips for historical days
"""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config import DAY_CONFIGS
from core.order_fetcher import fetch_orders_for_day
from core.trip_generator import generate_trips_for_day
from utils.map_visualizer import create_trip_map
from utils.data_exporter import export_all_formats

def print_banner():
    """Print welcome banner"""
    print("\n" + "=" * 70)
    print("  ALGORITHM-BASED TRIP GENERATION")
    print("  Generate trips using allocation algorithm for historical days")
    print("=" * 70 + "\n")

def print_summary(trip_data: dict, day: str):
    """Print trip generation summary"""
    trips = trip_data['trips']
    metrics = trip_data['metrics']
    zone_summary = trip_data.get('zone_summary', {})
    
    print(f"\n{'=' * 70}")
    print(f"  TRIP GENERATION SUMMARY - DAY {day}")
    print(f"{'=' * 70}\n")
    
    print(f"📊 Overall Statistics:")
    print(f"   Total Trips: {len(trips)}")
    print(f"   Total Zones: {len(zone_summary)}")
    print(f"   Average Utilization: {metrics['average_utilization_percent']}%")
    print(f"   Total Distance: {metrics['total_distance_km']} km")
    print(f"   Total Weight: {metrics['total_weight_kg']} kg")
    print(f"   Total Capacity: {metrics['total_capacity_kg']} kg")
    
    print(f"\n📍 Zone Breakdown:")
    for zone, summary in sorted(zone_summary.items()):
        print(f"   {zone}: {summary['order_count']} orders → {summary['trip_count']} trips")
    
    print(f"\n🚚 Trip Details:")
    print(f"   {'Trip':<12} {'Zone':<15} {'Vehicle':<10} {'Cap(kg)':<8} {'Orders':<8} {'Weight':<10} {'Util%':<8}")
    print(f"   {'-' * 75}")
    
    for trip in trips:
        print(f"   {trip['trip_name']:<12} {trip['zone']:<15} {trip['vehicle_number']:<10} "
              f"{trip['vehicle_capacity_kg']:<8} {trip['order_count']:<8} "
              f"{trip['total_weight']:<10} {trip['utilization_percent']:<8}")
    
    print(f"\n{'=' * 70}\n")

def generate_for_day(day: str, custom_capacity: float = None):
    """
    Generate trips for a specific day
    
    Args:
        day: Day identifier ("26" or "30")
        custom_capacity: Optional custom vehicle capacity
    """
    if day not in DAY_CONFIGS:
        print(f"❌ Invalid day: {day}")
        print(f"   Available days: {', '.join(DAY_CONFIGS.keys())}")
        return False
    
    config = DAY_CONFIGS[day]
    vehicle_capacity = custom_capacity if custom_capacity else config['vehicle_capacity']
    
    print(f"\n🗓️  Processing Day {day} ({config['description']})")
    print(f"   Vehicle Capacity: {vehicle_capacity} kg")
    
    # Get user sheet path (relative to this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    user_sheet_path = os.path.join(script_dir, config['user_sheet'])
    
    if not os.path.exists(user_sheet_path):
        print(f"❌ User sheet not found: {user_sheet_path}")
        return False
    
    # Step 1: Fetch orders
    orders_data = fetch_orders_for_day(user_sheet_path)
    
    if not orders_data['orders']:
        print(f"❌ No orders found for day {day}")
        return False
    
    # Step 2: Generate trips
    trip_data = generate_trips_for_day(orders_data, vehicle_capacity)
    
    if not trip_data:
        print(f"❌ Failed to generate trips for day {day}")
        return False
    
    # Step 3: Print summary
    print_summary(trip_data, day)
    
    # Step 4: Create map
    output_dir = os.path.join(script_dir, "outputs")
    map_file = create_trip_map(trip_data, day, output_dir)
    
    # Step 5: Export data
    export_files = export_all_formats(trip_data, day, vehicle_capacity, output_dir)
    
    print(f"\n✅ Day {day} processing complete!")
    print(f"\n📁 Output files:")
    print(f"   Map: {map_file}")
    print(f"   JSON: {export_files['json']}")
    print(f"   CSV: {export_files['csv']}")
    print(f"   Summary: {export_files['summary']}")
    
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate algorithm-based trips for historical days',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_trips.py --day 26
  python generate_trips.py --day 30
  python generate_trips.py --day all
  python generate_trips.py --day 26 --capacity 2000
        """
    )
    
    parser.add_argument(
        '--day',
        type=str,
        required=True,
        choices=['26', '30', 'all'],
        help='Day to process (26, 30, or all)'
    )
    
    parser.add_argument(
        '--capacity',
        type=float,
        default=None,
        help='Custom vehicle capacity in kg (default: 1500)'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.day == 'all':
        # Process all days
        success_count = 0
        for day in ['26', '30']:
            if generate_for_day(day, args.capacity):
                success_count += 1
            print("\n")
        
        print(f"\n{'=' * 70}")
        print(f"  Processed {success_count}/2 days successfully")
        print(f"{'=' * 70}\n")
    else:
        # Process single day
        generate_for_day(args.day, args.capacity)

if __name__ == "__main__":
    main()
