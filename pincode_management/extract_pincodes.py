import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text
from dotenv import load_dotenv
import json
import re
import csv
from datetime import datetime

load_dotenv()

db = SessionLocal()

try:
    print("=== Extracting Pincodes from Orders ===\n")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    count_result = db.execute(text("SELECT COUNT(*) FROM `orders`"))
    total_orders = count_result.fetchone()[0]
    print(f"Total orders: {total_orders:,}\n")
    
    result = db.execute(text("""
        SELECT 
            order_id,
            pincode,
            delivery_info
        FROM `orders`
    """))
    
    orders = result.fetchall()
    
    with_pincode = 0
    without_pincode = 0
    extracted_from_address = 0
    
    csv_file = open('pincode_extraction_report.csv', 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['order_id', 'pincode_in_db', 'pincode_from_address', 'latitude', 'longitude', 'status'])
    
    pincode_stats = {}
    
    for row in orders:
        order_id = row[0]
        pincode_db = row[1]
        delivery_info_json = row[2]
        
        pincode_from_address = None
        latitude = None
        longitude = None
        status = 'has_pincode'
        
        try:
            delivery_info = json.loads(delivery_info_json)
            address = delivery_info.get('address', '')
            latitude = delivery_info.get('latitude')
            longitude = delivery_info.get('longitude')
            
            pincode_match = re.search(r'\b(\d{6})\b', address)
            if pincode_match:
                pincode_from_address = pincode_match.group(1)
        except:
            pass
        
        if pincode_db:
            with_pincode += 1
            if pincode_db in pincode_stats:
                pincode_stats[pincode_db] += 1
            else:
                pincode_stats[pincode_db] = 1
        else:
            without_pincode += 1
            if pincode_from_address:
                status = 'missing_but_extractable'
                extracted_from_address += 1
            elif latitude and longitude:
                status = 'missing_has_coordinates'
            else:
                status = 'missing_no_data'
        
        csv_writer.writerow([
            order_id, 
            pincode_db or 'NULL', 
            pincode_from_address or 'NULL',
            latitude or 'NULL',
            longitude or 'NULL',
            status
        ])
    
    csv_file.close()
    
    print(f"{'='*80}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*80}\n")
    print(f"Total Orders: {total_orders:,}")
    print(f"With Pincode in DB: {with_pincode:,} ({with_pincode/total_orders*100:.2f}%)")
    print(f"Without Pincode: {without_pincode:,} ({without_pincode/total_orders*100:.2f}%)")
    print(f"  - Can extract from address: {extracted_from_address:,}")
    print(f"  - Have coordinates for geocoding: {without_pincode - extracted_from_address:,}")
    
    print(f"\n{'='*80}")
    print("TOP 20 PINCODES")
    print(f"{'='*80}\n")
    
    sorted_pincodes = sorted(pincode_stats.items(), key=lambda x: x[1], reverse=True)
    for pincode, count in sorted_pincodes[:20]:
        print(f"{pincode}: {count:,} orders")
    
    print(f"\nTotal unique pincodes: {len(pincode_stats)}")
    print(f"\nReport saved to: pincode_extraction_report.csv")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
