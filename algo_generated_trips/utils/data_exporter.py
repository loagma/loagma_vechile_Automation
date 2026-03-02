"""
Data exporter module - Exports trip data in various formats
"""

import json
import csv
import os

def export_to_json(trip_data: dict, day: str, vehicle_capacity: float, output_dir: str = "outputs") -> str:
    """
    Export trip data to JSON format
    
    Args:
        trip_data: Output from trip_generator
        day: Day identifier
        vehicle_capacity: Vehicle capacity used
        output_dir: Directory to save output
    
    Returns:
        Filename of saved JSON
    """
    trips = trip_data['trips']
    assignments = trip_data['assignments']
    metrics = trip_data['metrics']
    order_details = trip_data['order_details']
    
    export_data = {
        "day": day,
        "date": f"2024-12-{day}",
        "vehicle_capacity_default": vehicle_capacity,
        "total_orders": len(order_details),
        "total_trips": len(trips),
        "metrics": metrics,
        "trips": [
            {
                "trip_name": trip['trip_name'],
                "zone": trip['zone'],
                "vehicle_id": trip['vehicle_id'],
                "vehicle_number": trip['vehicle_number'],
                "vehicle_capacity_kg": trip['vehicle_capacity_kg'],
                "orders": trip['orders'],
                "order_count": trip['order_count'],
                "total_weight": trip['total_weight'],
                "utilization_percent": trip['utilization_percent']
            }
            for trip in trips
        ],
        "order_assignments": assignments
    }
    
    os.makedirs(os.path.join(output_dir, f"day_{day}"), exist_ok=True)
    filename = os.path.join(output_dir, f"day_{day}", f"algo_trips_day_{day}.json")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON saved: {filename}")
    return filename

def export_to_csv(trip_data: dict, day: str, output_dir: str = "outputs") -> str:
    """
    Export trip data to CSV format
    
    Args:
        trip_data: Output from trip_generator
        day: Day identifier
        output_dir: Directory to save output
    
    Returns:
        Filename of saved CSV
    """
    assignments = trip_data['assignments']
    order_details = trip_data['order_details']
    
    os.makedirs(os.path.join(output_dir, f"day_{day}"), exist_ok=True)
    filename = os.path.join(output_dir, f"day_{day}", f"algo_trips_day_{day}.csv")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'order_id', 'trip_name', 'zone', 'vehicle_number', 'vehicle_capacity_kg',
            'weight_kg', 'order_total', 'latitude', 'longitude', 
            'customer_name', 'contact', 'address'
        ])
        
        for order_id, assignment in sorted(assignments.items()):
            if order_id in order_details:
                order = order_details[order_id]
                writer.writerow([
                    order_id,
                    assignment['trip_name'],
                    assignment['zone'],
                    assignment['vehicle_number'],
                    '',  # Will be filled from trip data if needed
                    order['total_weight_kg'],
                    order['order_total'],
                    order['latitude'],
                    order['longitude'],
                    order['name'],
                    order['contactno'],
                    order['address'][:100]
                ])
    
    print(f"✅ CSV saved: {filename}")
    return filename

def export_summary_text(trip_data: dict, day: str, vehicle_capacity: float, output_dir: str = "outputs") -> str:
    """
    Export trip summary to text format
    
    Args:
        trip_data: Output from trip_generator
        day: Day identifier
        vehicle_capacity: Vehicle capacity used
        output_dir: Directory to save output
    
    Returns:
        Filename of saved text file
    """
    trips = trip_data['trips']
    metrics = trip_data['metrics']
    order_details = trip_data['order_details']
    
    os.makedirs(os.path.join(output_dir, f"day_{day}"), exist_ok=True)
    filename = os.path.join(output_dir, f"day_{day}", f"algo_trips_day_{day}_summary.txt")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Day {day} Algorithm Trip Generation Summary\n")
        f.write("=" * 60 + "\n")
        f.write(f"Date: 2024-12-{day}\n")
        f.write(f"Vehicle Capacity: {vehicle_capacity} kg\n")
        f.write(f"Total Orders: {len(order_details)}\n")
        f.write(f"Total Trips: {len(trips)}\n")
        f.write(f"Average Utilization: {metrics['average_utilization_percent']}%\n")
        f.write(f"Total Distance: {metrics['total_distance_km']} km\n")
        f.write("\n")
        
        f.write("Trip Details:\n")
        f.write("-" * 60 + "\n")
        
        for trip in trips:
            f.write(f"\n{trip['trip_name']} ({trip['zone']}):\n")
            f.write(f"  Orders: {trip['order_count']}\n")
            f.write(f"  Weight: {trip['total_weight']} kg ({trip['utilization_percent']}%)\n")
            f.write(f"  Order IDs: {', '.join(map(str, trip['orders'][:10]))}")
            if len(trip['orders']) > 10:
                f.write(f" ... and {len(trip['orders']) - 10} more")
            f.write("\n")
    
    print(f"✅ Summary saved: {filename}")
    return filename

def export_all_formats(trip_data: dict, day: str, vehicle_capacity: float, output_dir: str = "outputs") -> dict:
    """
    Export trip data in all formats
    
    Args:
        trip_data: Output from trip_generator
        day: Day identifier
        vehicle_capacity: Vehicle capacity used
        output_dir: Directory to save outputs
    
    Returns:
        Dictionary with all filenames
    """
    print(f"\n💾 Exporting data in multiple formats...")
    
    files = {
        'json': export_to_json(trip_data, day, vehicle_capacity, output_dir),
        'csv': export_to_csv(trip_data, day, output_dir),
        'summary': export_summary_text(trip_data, day, vehicle_capacity, output_dir)
    }
    
    return files
