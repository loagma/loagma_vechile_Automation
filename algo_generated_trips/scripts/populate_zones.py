"""
Populate trip_cards table with zones (areas)
Creates 11 zones: 10 main areas + 1 UNKNOWN zone
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SessionLocal
from sqlalchemy import text

def create_zones():
    """
    Insert zones into trip_cards table
    """
    zones = [
        "ATTAPUR",
        "GOLCONDA",
        "ASIF NAGAR",
        "GUDIMALKAPUR",
        "NARSINGI",
        "BEGUMPET",
        "HAKIMPET",
        "MANIKONDA",
        "HAFEEZPET",
        "BADANGPET",
        "YOUSUFGUDA",
        "BORABANDA",
        "UNKNOWN"
    ]
    
    db = SessionLocal()
    
    try:
        print("🚀 Creating zones in trip_cards table...\n")
        
        for zone_name in zones:
            # Check if zone already exists
            result = db.execute(text("""
                SELECT zone_id FROM trip_cards WHERE zone_name = :zone_name
            """), {"zone_name": zone_name})
            
            existing = result.fetchone()
            
            if existing:
                print(f"⏭️  {zone_name} already exists (zone_id: {existing[0]})")
            else:
                # Insert new zone
                db.execute(text("""
                    INSERT INTO trip_cards (zone_name, vehicle_id, status, created_at)
                    VALUES (:zone_name, NULL, 'active', NOW())
                """), {"zone_name": zone_name})
                
                db.commit()
                
                # Get the inserted zone_id
                result = db.execute(text("""
                    SELECT zone_id FROM trip_cards WHERE zone_name = :zone_name
                """), {"zone_name": zone_name})
                
                zone_id = result.fetchone()[0]
                print(f"✅ Created {zone_name} (zone_id: {zone_id})")
        
        print(f"\n✅ Zone creation complete!")
        print(f"Total zones: {len(zones)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_zones()
