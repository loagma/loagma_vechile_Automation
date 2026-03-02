"""
Build pincode to area mapping from human-made trip allocations
Analyzes Day 26 data to reverse-engineer which pincodes belong to which areas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SessionLocal
from sqlalchemy import text
import json
import re
from collections import defaultdict

def parse_user_sheet(file_path: str) -> dict:
    """
    Parse user sheet and extract order -> area mapping
    
    Returns:
        Dictionary: {order_id: area_name}
    """
    order_to_area = {}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        # Skip header lines
        for line in lines[2:]:
            line = line.strip()
            if not line:
                continue
            
            columns = line.split('\t')
            if len(columns) >= 3:
                try:
                    order_id = int(columns[1].strip())
                    vehicle_name = columns[2].strip()
                    
                    # Extract area from vehicle name (e.g., "ATTAPUR 1" -> "ATTAPUR")
                    area_name = vehicle_name.rsplit(' ', 1)[0].strip().upper()
                    order_to_area[order_id] = area_name
                except (ValueError, IndexError):
                    continue
    
    print(f"✅ Parsed {len(order_to_area)} order-to-area mappings")
    return order_to_area

def extract_pincode_from_json(delivery_info: dict) -> str:
    """
    Extract pincode from delivery_info JSON
    """
    # Try direct pincode field
    if 'pincode' in delivery_info and delivery_info['pincode']:
        return str(delivery_info['pincode']).strip()
    
    # Try to extract from address
    address = delivery_info.get('address', '')
    if address:
        # Look for 6-digit pincode pattern
        match = re.search(r'\b\d{6}\b', address)
        if match:
            return match.group(0)
    
    return None

def fetch_pincodes_from_db(order_ids: list) -> dict:
    """
    Query database for pincodes of given orders
    
    Returns:
        Dictionary: {order_id: pincode}
    """
    if not order_ids:
        return {}
    
    db = SessionLocal()
    order_to_pincode = {}
    
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
                
                if pincode:
                    order_to_pincode[order_id] = pincode
                    
            except Exception as e:
                print(f"⚠️  Error processing order {order_id}: {e}")
                continue
        
        print(f"✅ Extracted pincodes for {len(order_to_pincode)} orders")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        db.close()
    
    return order_to_pincode

def build_pincode_mapping(order_to_area: dict, order_to_pincode: dict) -> dict:
    """
    Build pincode -> area mapping
    
    Returns:
        Dictionary: {pincode: area_name}
    """
    # Group pincodes by area
    area_to_pincodes = defaultdict(list)
    
    for order_id, area in order_to_area.items():
        if order_id in order_to_pincode:
            pincode = order_to_pincode[order_id]
            area_to_pincodes[area].append(pincode)
    
    # Count pincode occurrences per area
    pincode_area_counts = defaultdict(lambda: defaultdict(int))
    
    for area, pincodes in area_to_pincodes.items():
        for pincode in pincodes:
            pincode_area_counts[pincode][area] += 1
    
    # Assign each pincode to dominant area
    pincode_to_area = {}
    conflicts = []
    
    for pincode, area_counts in pincode_area_counts.items():
        # Find area with most orders for this pincode
        dominant_area = max(area_counts.items(), key=lambda x: x[1])
        pincode_to_area[pincode] = dominant_area[0]
        
        # Log conflicts (pincode appears in multiple areas)
        if len(area_counts) > 1:
            conflicts.append({
                'pincode': pincode,
                'areas': dict(area_counts),
                'assigned_to': dominant_area[0]
            })
    
    return pincode_to_area, conflicts, area_to_pincodes

def print_mapping_summary(pincode_to_area: dict, conflicts: list, area_to_pincodes: dict):
    """
    Print summary of the mapping
    """
    print("\n" + "="*60)
    print("PINCODE TO AREA MAPPING SUMMARY")
    print("="*60)
    
    # Group by area
    area_pincodes = defaultdict(set)
    for pincode, area in pincode_to_area.items():
        area_pincodes[area].add(pincode)
    
    for area in sorted(area_pincodes.keys()):
        pincodes = sorted(area_pincodes[area])
        print(f"\n{area}:")
        print(f"  Pincodes: {', '.join(pincodes)}")
        print(f"  Total: {len(pincodes)} pincodes")
    
    print(f"\n{'='*60}")
    print(f"Total unique pincodes: {len(pincode_to_area)}")
    print(f"Total areas: {len(area_pincodes)}")
    
    if conflicts:
        print(f"\n⚠️  {len(conflicts)} pincodes found in multiple areas:")
        for conflict in conflicts[:5]:  # Show first 5
            print(f"  {conflict['pincode']}: {conflict['areas']} -> Assigned to {conflict['assigned_to']}")
        if len(conflicts) > 5:
            print(f"  ... and {len(conflicts) - 5} more")

def save_mapping_to_config(pincode_to_area: dict):
    """
    Update config.py with the pincode mapping
    """
    mapping_code = "\n# Pincode to Area Mapping (Generated from Day 26 human allocations)\n"
    mapping_code += "PINCODE_TO_AREA = {\n"
    
    for pincode in sorted(pincode_to_area.keys()):
        area = pincode_to_area[pincode]
        mapping_code += f'    "{pincode}": "{area}",\n'
    
    mapping_code += "}\n"
    
    # Read existing config
    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
    with open(config_path, 'r') as f:
        config_content = f.read()
    
    # Append mapping if not already present
    if "PINCODE_TO_AREA" not in config_content:
        with open(config_path, 'a') as f:
            f.write(mapping_code)
        print(f"\n✅ Added PINCODE_TO_AREA mapping to config.py")
    else:
        print(f"\n⚠️  PINCODE_TO_AREA already exists in config.py - manual update needed")

def main():
    """
    Main execution
    """
    print("🚀 Building Pincode to Area Mapping from Day 26 Data\n")
    
    # Path to Day 26 user sheet
    user_sheet_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "human_made_trips_visualization",
        "vy37r1dlj4_UserSheet.txt"
    )
    
    # Step 1: Parse user sheet
    print("📋 Step 1: Parsing user sheet...")
    order_to_area = parse_user_sheet(user_sheet_path)
    
    # Step 2: Fetch pincodes from database
    print("\n🔍 Step 2: Fetching pincodes from database...")
    order_ids = list(order_to_area.keys())
    order_to_pincode = fetch_pincodes_from_db(order_ids)
    
    # Step 3: Build mapping
    print("\n⚙️  Step 3: Building pincode mapping...")
    pincode_to_area, conflicts, area_to_pincodes = build_pincode_mapping(
        order_to_area, 
        order_to_pincode
    )
    
    # Step 4: Print summary
    print_mapping_summary(pincode_to_area, conflicts, area_to_pincodes)
    
    # Step 5: Save to config
    print("\n💾 Step 5: Saving mapping to config.py...")
    save_mapping_to_config(pincode_to_area)
    
    print("\n✅ Done! Pincode mapping has been generated.")
    print("\nNext steps:")
    print("1. Review the mapping above")
    print("2. Check config.py for the PINCODE_TO_AREA dictionary")
    print("3. Update order_fetcher.py to use pincodes instead of area_name")

if __name__ == "__main__":
    main()
