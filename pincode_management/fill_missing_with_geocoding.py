import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text
from dotenv import load_dotenv
import json
import requests
import time
from datetime import datetime

load_dotenv()

def get_pincode_from_coordinates(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'LogmaDeliveryApp/1.0'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            pincode = address.get('postcode')
            
            if pincode:
                pincode = pincode.replace(' ', '').replace('-', '')
                if len(pincode) == 6 and pincode.isdigit():
                    return pincode
        
        return None
    except Exception as e:
        return None

db = SessionLocal()

try:
    print("=== Filling Missing Pincodes with Reverse Geocoding ===\n")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    result = db.execute(text("""
        SELECT 
            order_id,
            delivery_info
        FROM `orders`
        WHERE (pincode IS NULL OR pincode = '')
        AND delivery_info IS NOT NULL
        LIMIT 100
    """))
    
    missing_orders = result.fetchall()
    
    print(f"Found {len(missing_orders)} orders to process\n")
    
    if len(missing_orders) == 0:
        print("✓ No missing pincodes!")
    else:
        filled = 0
        failed = 0
        
        print("Processing (1 request per second due to API rate limit)...\n")
        
        for i, row in enumerate(missing_orders, 1):
            order_id = row[0]
            delivery_info_json = row[1]
            
            try:
                delivery_info = json.loads(delivery_info_json)
                latitude = delivery_info.get('latitude')
                longitude = delivery_info.get('longitude')
                
                if not latitude or not longitude:
                    print(f"[{i}/{len(missing_orders)}] Order {order_id}: ✗ No coordinates")
                    failed += 1
                    continue
                
                print(f"[{i}/{len(missing_orders)}] Order {order_id}: ", end='', flush=True)
                
                pincode = get_pincode_from_coordinates(float(latitude), float(longitude))
                
                if pincode:
                    db.execute(text("""
                        UPDATE `orders` 
                        SET pincode = :pincode 
                        WHERE order_id = :order_id
                    """), {'pincode': pincode, 'order_id': order_id})
                    db.commit()
                    print(f"✓ {pincode}")
                    filled += 1
                else:
                    print("✗ Not found")
                    failed += 1
                
                time.sleep(1)
                
            except Exception as e:
                print(f"✗ Error: {e}")
                failed += 1
        
        print(f"\n{'='*80}")
        print("COMPLETION SUMMARY")
        print(f"{'='*80}")
        print(f"Processed: {len(missing_orders)}")
        print(f"Successfully filled: {filled}")
        print(f"Failed: {failed}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
