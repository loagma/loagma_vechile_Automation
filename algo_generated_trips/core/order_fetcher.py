"""
Order fetcher module - Fetches orders from database for specific days
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SessionLocal
from sqlalchemy import text
import json
import random
import re

def extract_pincode_from_delivery_info(delivery_info: dict) -> str:
    """
    Extract pincode from delivery_info JSON
    
    Args:
        delivery_info: Delivery info dictionary
    
    Returns:
        Pincode string or None if not found
    """
    # Try direct pincode field
    if 'pincode' in delivery_info and delivery_info['pincode']:
        pincode = str(delivery_info['pincode']).strip()
        if pincode and len(pincode) == 6 and pincode.isdigit():
            return pincode
    
    # Try to extract from address using regex
    address = delivery_info.get('address', '')
    if address:
        # Look for 6-digit pincode pattern
        match = re.search(r'\b\d{6}\b', address)
        if match:
            return match.group(0)
    
    return None

def get_zone_from_pincode(pincode: str, db) -> str:
    """
    Get zone name from pincode using trip_card_pincode table
    
    Args:
        pincode: Pincode string
        db: Database session
    
    Returns:
        Zone name or 'UNKNOWN' if not found
    """
    if not pincode:
        return 'UNKNOWN'
    
    try:
        result = db.execute(text("""
            SELECT tc.zone_name 
            FROM trip_card_pincode tcp
            JOIN trip_cards tc ON tcp.zone_id = tc.zone_id
            WHERE tcp.pincode = :pincode
        """), {"pincode": pincode})
        
        row = result.fetchone()
        if row:
            return row[0]
    except Exception as e:
        print(f"⚠️  Error looking up zone for pincode {pincode}: {e}")
    
    return 'UNKNOWN'

def read_order_ids_from_sheet(file_path: str) -> list:
    """
    Parse user sheet file and extract order IDs
    
    Args:
        file_path: Path to user sheet txt file
    
    Returns:
        List of order IDs [244541, 244538, ...]
    """
    order_ids = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
            # Skip first line (prepareOrderNotify) and use second line as header
            if len(lines) < 2:
                print("⚠️  File is too short!")
                return order_ids
            
            # Find the header line
            header_line = lines[1].strip().split('\t')
            
            # Find OrderId column index
            try:
                order_id_index = header_line.index('OrderId')
            except ValueError:
                print(f"⚠️  OrderId column not found in header!")
                print(f"Available columns: {header_line}")
                return order_ids
            
            # Read data rows (starting from line 3, index 2)
            for line in lines[2:]:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                
                columns = line.split('\t')
                if len(columns) > order_id_index:
                    try:
                        order_id = int(columns[order_id_index].strip())
                        order_ids.append(order_id)
                    except ValueError:
                        continue
        
        print(f"✅ Read {len(order_ids)} order IDs from user sheet")
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
    
    return order_ids

def fetch_orders_from_db(order_ids: list) -> list:
    """
    Query database for order details
    
    Args:
        order_ids: List of order IDs to fetch
    
    Returns:
        List of order dictionaries with all details including zone
    """
    if not order_ids:
        return []
    
    db = SessionLocal()
    orders = []
    zone_stats = {'UNKNOWN': 0}
    
    try:
        order_ids_str = ','.join(map(str, order_ids))
        
        result = db.execute(text(f"""
            SELECT 
                order_id,
                delivery_info,
                order_total,
                area_name
            FROM `orders` 
            WHERE order_id IN ({order_ids_str})
        """))
        
        for row in result:
            order_id = row[0]
            delivery_info_json = row[1]
            order_total = float(row[2]) if row[2] else 0
            area_name = row[3] or 'Unknown'
            
            try:
                delivery_info = json.loads(delivery_info_json)
                
                latitude = delivery_info.get('latitude')
                longitude = delivery_info.get('longitude')
                address = delivery_info.get('address', 'N/A')
                name = delivery_info.get('name', 'N/A')
                contactno = delivery_info.get('contactno', 'N/A')
                
                if not latitude or not longitude:
                    print(f"⚠️  Order {order_id} missing coordinates, skipping...")
                    continue
                
                lat = float(latitude)
                lon = float(longitude)
                
                # Extract pincode
                pincode = extract_pincode_from_delivery_info(delivery_info)
                
                # Get zone from pincode
                zone_name = get_zone_from_pincode(pincode, db)
                
                # Track zone stats
                if zone_name not in zone_stats:
                    zone_stats[zone_name] = 0
                zone_stats[zone_name] += 1
                
                # Estimate weight from order total
                weight_kg = random.uniform(50, 100)  # Placeholder - adjust as needed
                
                orders.append({
                    'order_id': order_id,
                    'latitude': lat,
                    'longitude': lon,
                    'pincode': pincode or 'N/A',
                    'zone_name': zone_name,
                    'total_weight_kg': round(weight_kg, 2),
                    'order_total': order_total,
                    'address': address,
                    'name': name,
                    'contactno': contactno
                })
                
            except Exception as e:
                print(f"⚠️  Error processing order {order_id}: {e}")
                continue
        
        print(f"✅ Fetched {len(orders)} orders from database")
        print(f"\n📍 Zone distribution:")
        for zone, count in sorted(zone_stats.items()):
            print(f"   {zone}: {count} orders")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        db.close()
    
    return orders

def prepare_orders_for_algorithm(orders: list) -> list:
    """
    Format orders for AllocationEngine input
    
    Args:
        orders: List of order dictionaries
    
    Returns:
        List formatted for AllocationEngine
    """
    algo_orders = []
    
    for order in orders:
        algo_orders.append({
            'order_id': order['order_id'],
            'latitude': order['latitude'],
            'longitude': order['longitude'],
            'pincode': order['pincode'],
            'total_weight_kg': order['total_weight_kg']
        })
    
    return algo_orders

def fetch_orders_for_day(user_sheet_path: str) -> dict:
    """
    Complete workflow to fetch orders for a specific day
    
    Args:
        user_sheet_path: Path to user sheet file
    
    Returns:
        Dictionary with orders and details
    """
    print(f"\n📋 Reading order IDs from: {user_sheet_path}")
    order_ids = read_order_ids_from_sheet(user_sheet_path)
    
    if not order_ids:
        return {'orders': [], 'algo_orders': [], 'order_details': {}}
    
    print(f"\n🔍 Fetching order details from database...")
    orders = fetch_orders_from_db(order_ids)
    
    if not orders:
        return {'orders': [], 'algo_orders': [], 'order_details': {}}
    
    print(f"\n⚙️  Preparing orders for algorithm...")
    algo_orders = prepare_orders_for_algorithm(orders)
    
    # Create order details lookup
    order_details = {order['order_id']: order for order in orders}
    
    return {
        'orders': orders,
        'algo_orders': algo_orders,
        'order_details': order_details
    }
