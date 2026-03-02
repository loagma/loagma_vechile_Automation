import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text
from dotenv import load_dotenv
import json
import re

load_dotenv()

db = SessionLocal()

try:
    print("=== Finding Orders with Missing Pincodes ===\n")
    
    result = db.execute(text("""
        SELECT 
            order_id,
            delivery_info,
            order_state,
            order_total
        FROM `orders`
        WHERE pincode IS NULL OR pincode = ''
        ORDER BY order_id DESC
        LIMIT 100
    """))
    
    missing_orders = result.fetchall()
    
    print(f"Found {len(missing_orders)} orders with missing pincodes (showing first 100)\n")
    
    if len(missing_orders) == 0:
        print("✓ All orders have pincodes!")
    else:
        print(f"{'Order ID':<12} {'Status':<15} {'Total':<12} {'Has Coords':<12} {'Address Preview'}")
        print("="*100)
        
        extractable = 0
        has_coords = 0
        no_data = 0
        
        for row in missing_orders:
            order_id = row[0]
            delivery_info_json = row[1]
            order_state = row[2]
            order_total = row[3]
            
            has_coordinates = False
            address_preview = "N/A"
            
            try:
                delivery_info = json.loads(delivery_info_json)
                address = delivery_info.get('address', '')
                latitude = delivery_info.get('latitude')
                longitude = delivery_info.get('longitude')
                
                if latitude and longitude:
                    has_coordinates = True
                    has_coords += 1
                
                pincode_match = re.search(r'\b(\d{6})\b', address)
                if pincode_match:
                    extractable += 1
                    address_preview = f"Has pincode: {pincode_match.group(1)}"
                else:
                    address_preview = address[:50] if address else "No address"
                
                if not has_coordinates and not pincode_match:
                    no_data += 1
                    
            except:
                no_data += 1
                address_preview = "Invalid data"
            
            coords_status = "Yes" if has_coordinates else "No"
            print(f"{order_id:<12} {order_state:<15} ₹{order_total:<10} {coords_status:<12} {address_preview}")
        
        print("\n" + "="*100)
        print("SUMMARY")
        print("="*100)
        print(f"Total missing: {len(missing_orders)}")
        print(f"Can extract from address: {extractable}")
        print(f"Have coordinates for geocoding: {has_coords}")
        print(f"No usable data: {no_data}")
        
        print("\nTo fill missing pincodes:")
        print("1. Run extract_pincodes.py to generate full report")
        print("2. Use reverse geocoding API for orders with coordinates")
        print("3. Manually update orders with no data")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
