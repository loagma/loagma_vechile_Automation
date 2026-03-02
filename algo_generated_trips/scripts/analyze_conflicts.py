"""
Analyze why certain pincodes appear in multiple areas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text
import json
import re
from collections import defaultdict

def parse_user_sheet(file_path: str) -> dict:
    """Parse user sheet and extract order -> area mapping"""
    order_to_area = {}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        for line in lines[2:]:
            line = line.strip()
            if not line:
                continue
            
            columns = line.split('\t')
            if len(columns) >= 3:
                try:
                    order_id = int(columns[1].strip())
                    vehicle_name = columns[2].strip()
                    area_name = vehicle_name.rsplit(' ', 1)[0].strip().upper()
                    order_to_area[order_id] = area_name
                except (ValueError, IndexError):
                    continue
    
    return order_to_area

def extract_pincode_from_json(delivery_info: dict) -> str:
    """Extract pincode from delivery_info JSON"""
    if 'pincode' in delivery_info and delivery_info['pincode']:
        return str(delivery_info['pincode']).strip()
    
    address = delivery_info.get('address', '')
    if address:
        match = re.search(r'\b\d{6}\b', address)
        if match:
            return match.group(0)
    
    return None

def fetch_order_details(order_ids: list) -> dict:
    """Fetch full order details including address"""
    if not order_ids:
        return {}
    
    db = SessionLocal()
    order_details = {}
    
    try:
        order_ids_str = ','.join(map(str, order_ids))
        
        result = db.execute(text(f"""
            SELECT 
                order_id,
                delivery_info
            FROM `orders` 
            WHERE order_id IN ({order_ids_str})
        """))
        
        for row in result:
            order_id = row[0]
            delivery_info_json = row[1]
            
            try:
                delivery_info = json.loads(delivery_info_json)
                pincode = extract_pincode_from_json(delivery_info)
                
                order_details[order_id] = {
                    'pincode': pincode,
                    'address': delivery_info.get('address', 'N/A'),
                    'name': delivery_info.get('name', 'N/A'),
                    'latitude': delivery_info.get('latitude'),
                    'longitude': delivery_info.get('longitude')
                }
                    
            except Exception as e:
                print(f"⚠️  Error processing order {order_id}: {e}")
                continue
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        db.close()
    
    return order_details

def analyze_conflicts():
    """Analyze pincode conflicts in detail"""
    
    # Path to Day 26 user sheet
    user_sheet_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "human_made_trips_visualization",
        "vy37r1dlj4_UserSheet.txt"
    )
    
    print("🔍 Analyzing Pincode Conflicts\n")
    
    # Parse user sheet
    order_to_area = parse_user_sheet(user_sheet_path)
    print(f"✅ Parsed {len(order_to_area)} orders\n")
    
    # Fetch order details
    order_ids = list(order_to_area.keys())
    order_details = fetch_order_details(order_ids)
    print(f"✅ Fetched details for {len(order_details)} orders\n")
    
    # Build pincode -> orders mapping
    pincode_to_orders = defaultdict(list)
    
    for order_id, area in order_to_area.items():
        if order_id in order_details:
            details = order_details[order_id]
            pincode = details['pincode']
            if pincode:
                pincode_to_orders[pincode].append({
                    'order_id': order_id,
                    'area': area,
                    'address': details['address'],
                    'name': details['name'],
                    'lat': details['latitude'],
                    'lon': details['longitude']
                })
    
    # Find conflicts
    conflicts = {}
    for pincode, orders in pincode_to_orders.items():
        areas = set(order['area'] for order in orders)
        if len(areas) > 1:
            conflicts[pincode] = orders
    
    print("="*80)
    print(f"FOUND {len(conflicts)} PINCODES WITH CONFLICTS")
    print("="*80)
    
    for pincode, orders in sorted(conflicts.items()):
        print(f"\n📍 PINCODE: {pincode}")
        print(f"   Total Orders: {len(orders)}")
        
        # Group by area
        area_groups = defaultdict(list)
        for order in orders:
            area_groups[order['area']].append(order)
        
        print(f"   Areas: {list(area_groups.keys())}")
        
        for area, area_orders in sorted(area_groups.items()):
            print(f"\n   🏘️  {area} ({len(area_orders)} orders):")
            for order in area_orders[:3]:  # Show first 3
                print(f"      Order {order['order_id']}: {order['name']}")
                print(f"      Address: {order['address'][:80]}...")
                print(f"      Coords: ({order['lat']}, {order['lon']})")
            if len(area_orders) > 3:
                print(f"      ... and {len(area_orders) - 3} more")
        
        print("\n   " + "-"*70)
    
    # Summary
    print("\n" + "="*80)
    print("ANALYSIS SUMMARY")
    print("="*80)
    print("\nPossible reasons for conflicts:")
    print("1. Border areas - Pincodes at boundaries between service areas")
    print("2. Large pincodes - Single pincode covering multiple neighborhoods")
    print("3. Human decision - Delivery person assigned based on availability, not strict geography")
    print("4. Missing/wrong pincode data - Database quality issues")
    print("\nRecommendation:")
    print("- Use dominant area (most orders) for each pincode")
    print("- Consider geographic coordinates for border cases")
    print("- Manual review of high-conflict pincodes")

if __name__ == "__main__":
    analyze_conflicts()
