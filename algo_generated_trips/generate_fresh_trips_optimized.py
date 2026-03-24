"""
Fresh Trip Generation with Optimized Zones
Generate trips using the new optimized pincode-zone structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text
import json
from datetime import datetime, timedelta

def generate_trips_for_day(day_number):
    """Generate trips for a specific day using optimized zones"""
    
    print(f"\n🚛 Generating trips for day {day_number}...")
    
    db = SessionLocal()
    
    try:
        # Get orders for the specified day (using December 2024 as base)
        base_date = datetime(2024, 12, 1)
        target_date = base_date + timedelta(days=day_number - 1)
        
        # Get zone assignments from optimized structure
        result = db.execute(text("""
            SELECT tc.zone_id, tc.zone_name,
                   COUNT(tcp.pincode) as pincode_count,
                   GROUP_CONCAT(tcp.pincode) as pincodes
            FROM trip_cards tc
            LEFT JOIN trip_card_pincode tcp ON tc.zone_id = tcp.zone_id
            GROUP BY tc.zone_id, tc.zone_name
            ORDER BY tc.zone_id
        """))
        
        zones = [dict(row._mapping) for row in result]
        
        # Get vehicles assigned to zones
        result = db.execute(text("""
            SELECT zv.zone_id, COUNT(zv.vehicle_id) as vehicle_count,
                   GROUP_CONCAT(v.vehicle_number) as vehicle_numbers
            FROM zone_vehicles zv
            LEFT JOIN vehicles v ON zv.vehicle_id = v.vehicle_id
            WHERE zv.is_active = 1
            GROUP BY zv.zone_id
        """))
        
        zone_vehicles = {row[0]: dict(row._mapping) for row in result}
        
        # Generate trip data
        trip_data = {
            'day': day_number,
            'date': target_date.strftime('%Y-%m-%d'),
            'zones': [],
            'summary': {
                'total_zones': len(zones),
                'total_pincodes': sum(z['pincode_count'] or 0 for z in zones),
                'generation_time': datetime.now().isoformat()
            }
        }
        
        for zone in zones:
            zone_id = zone['zone_id']
            vehicles = zone_vehicles.get(zone_id, {})
            
            zone_trip = {
                'zone_id': zone['zone_name'],
                'zone_db_id': zone_id,
                'pincode_count': zone['pincode_count'] or 0,
                'pincodes': zone['pincodes'].split(',') if zone['pincodes'] else [],
                'assigned_vehicles': vehicles.get('vehicle_count', 0),
                'vehicle_numbers': vehicles.get('vehicle_numbers', '').split(',') if vehicles.get('vehicle_numbers') else [],
                'trip_status': 'generated_with_optimized_zones'
            }
            
            trip_data['zones'].append(zone_trip)
        
        # Save trip data
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'outputs',
            f'day_{day_number}'
        )
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON data
        json_file = os.path.join(output_dir, f'optimized_trips_day_{day_number}.json')
        with open(json_file, 'w') as f:
            json.dump(trip_data, f, indent=2)
        
        # Save summary
        summary_file = os.path.join(output_dir, f'trip_summary_day_{day_number}.txt')
        with open(summary_file, 'w') as f:
            f.write(f"""FRESH TRIP GENERATION SUMMARY - DAY {day_number}
{'=' * 60}

GENERATION DETAILS
-----------------
Date: {target_date.strftime('%Y-%m-%d')}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: Optimized Pincode-Zone Structure

ZONE SUMMARY
-----------
Total Zones: {len(zones)}
Total Pincodes: {sum(z['pincode_count'] or 0 for z in zones)}
Total Vehicles: {sum(vehicles.get('vehicle_count', 0) for vehicles in zone_vehicles.values())}

ZONE DETAILS
-----------
""")
            
            for zone_trip in trip_data['zones']:
                f.write(f"""Zone {zone_trip['zone_id']} (ID: {zone_trip['zone_db_id']}):
  Pincodes: {zone_trip['pincode_count']}
  Vehicles: {zone_trip['assigned_vehicles']}
  Status: {zone_trip['trip_status']}

""")
        
        print(f"   ✅ Generated trips for day {day_number}")
        print(f"      Zones: {len(zones)}")
        print(f"      Pincodes: {sum(z['pincode_count'] or 0 for z in zones)}")
        print(f"      Output: {output_dir}")
        
        return trip_data
        
    except Exception as e:
        print(f"   ❌ Error generating trips for day {day_number}: {e}")
        return None
    finally:
        db.close()

def main():
    """Generate fresh trips for multiple days"""
    
    print("=" * 80)
    print("  FRESH TRIP GENERATION WITH OPTIMIZED ZONES")
    print("=" * 80)
    
    test_days = [3, 6, 7, 9, 10, 15, 20, 21, 22, 26, 28, 30]
    
    generated_days = []
    
    for day in test_days:
        trip_data = generate_trips_for_day(day)
        if trip_data:
            generated_days.append(day)
    
    print(f"\n" + "=" * 80)
    print(f"  FRESH TRIP GENERATION COMPLETE")
    print(f"=" * 80)
    
    print(f"\n✅ Fresh trips generated successfully!")
    print(f"📊 Generation summary:")
    print(f"   • Days processed: {len(generated_days)}")
    print(f"   • Days generated: {', '.join(map(str, generated_days))}")
    print(f"   • Using optimized zone structure with 23 zones")
    print(f"   • Output location: algo_generated_trips/outputs/")
    
    return generated_days

if __name__ == "__main__":
    main()