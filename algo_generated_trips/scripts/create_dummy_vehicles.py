"""
Create dummy vehicles for testing
Vehicles are independent entities with varying capacities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SessionLocal
from sqlalchemy import text

def create_vehicles():
    """
    Create pool of vehicles with varying capacities
    """
    # Mix of capacities for realistic testing
    vehicles = [
        {"number": "V001", "capacity": 1500},
        {"number": "V002", "capacity": 1500},
        {"number": "V003", "capacity": 2000},
        {"number": "V004", "capacity": 1200},
        {"number": "V005", "capacity": 1500},
        {"number": "V006", "capacity": 2000},
        {"number": "V007", "capacity": 1500},
        {"number": "V008", "capacity": 1200},
        {"number": "V009", "capacity": 1800},
        {"number": "V010", "capacity": 1500},
        {"number": "V011", "capacity": 2000},
        {"number": "V012", "capacity": 1500},
        {"number": "V013", "capacity": 1200},
        {"number": "V014", "capacity": 1800},
        {"number": "V015", "capacity": 1500},
    ]
    
    db = SessionLocal()
    
    try:
        print("🚀 Creating dummy vehicles...\n")
        
        created = 0
        skipped = 0
        
        for vehicle in vehicles:
            # Check if vehicle already exists
            result = db.execute(text("""
                SELECT vehicle_id FROM vehicles WHERE vehicle_number = :number
            """), {"number": vehicle["number"]})
            
            existing = result.fetchone()
            
            if existing:
                print(f"⏭️  {vehicle['number']} already exists (capacity: {vehicle['capacity']}kg)")
                skipped += 1
            else:
                # Insert vehicle
                db.execute(text("""
                    INSERT INTO vehicles (vehicle_number, capacity_kg, is_active, created_at)
                    VALUES (:number, :capacity, 1, NOW())
                """), {
                    "number": vehicle["number"],
                    "capacity": vehicle["capacity"]
                })
                
                print(f"✅ Created {vehicle['number']} (capacity: {vehicle['capacity']}kg)")
                created += 1
        
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ Vehicle creation complete!")
        print(f"Created: {created}")
        print(f"Skipped: {skipped}")
        print(f"Total: {len(vehicles)}")
        print(f"\nCapacity distribution:")
        print(f"  1200kg: {sum(1 for v in vehicles if v['capacity'] == 1200)} vehicles")
        print(f"  1500kg: {sum(1 for v in vehicles if v['capacity'] == 1500)} vehicles")
        print(f"  1800kg: {sum(1 for v in vehicles if v['capacity'] == 1800)} vehicles")
        print(f"  2000kg: {sum(1 for v in vehicles if v['capacity'] == 2000)} vehicles")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_vehicles()
