"""
Populate trip_card_pincode table with pincode-to-zone mappings
Uses the PINCODE_TO_AREA mapping from config.py
"""

import sys
import os

# Add paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
algo_dir = os.path.dirname(script_dir)
root_dir = os.path.dirname(algo_dir)

sys.path.append(root_dir)
sys.path.append(algo_dir)

from database import SessionLocal
from sqlalchemy import text
from core.config import PINCODE_TO_AREA

def populate_pincodes():
    """
    Insert pincode mappings into trip_card_pincode table
    """
    db = SessionLocal()
    
    try:
        print("🚀 Populating pincode mappings...\n")
        
        # First, get all zone_ids
        result = db.execute(text("SELECT zone_id, zone_name FROM trip_cards"))
        zones = {row[1]: row[0] for row in result.fetchall()}
        
        print(f"Found {len(zones)} zones in database")
        print(f"Have {len(PINCODE_TO_AREA)} pincodes to map\n")
        
        inserted = 0
        skipped = 0
        
        for pincode, area_name in PINCODE_TO_AREA.items():
            # Get zone_id for this area
            zone_id = zones.get(area_name)
            
            if not zone_id:
                print(f"⚠️  Zone not found for {area_name} (pincode {pincode})")
                skipped += 1
                continue
            
            # Check if mapping already exists
            result = db.execute(text("""
                SELECT id FROM trip_card_pincode 
                WHERE zone_id = :zone_id AND pincode = :pincode
            """), {"zone_id": zone_id, "pincode": pincode})
            
            existing = result.fetchone()
            
            if existing:
                print(f"⏭️  {pincode} -> {area_name} already exists")
                skipped += 1
            else:
                # Insert mapping
                db.execute(text("""
                    INSERT INTO trip_card_pincode (zone_id, pincode, created_at)
                    VALUES (:zone_id, :pincode, NOW())
                """), {"zone_id": zone_id, "pincode": pincode})
                
                print(f"✅ {pincode} -> {area_name} (zone_id: {zone_id})")
                inserted += 1
        
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ Pincode mapping complete!")
        print(f"Inserted: {inserted}")
        print(f"Skipped: {skipped}")
        print(f"Total: {len(PINCODE_TO_AREA)}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_pincodes()
