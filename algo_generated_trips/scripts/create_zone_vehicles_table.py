"""
Create zone_vehicles table for many-to-many relationship between zones and vehicles
"""

import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
algo_dir = os.path.dirname(script_dir)
root_dir = os.path.dirname(algo_dir)

sys.path.append(root_dir)

from database import SessionLocal
from sqlalchemy import text

def create_zone_vehicles_table():
    """
    Create zone_vehicles table with proper foreign keys and indexes
    """
    db = SessionLocal()
    
    try:
        print("🚀 Creating zone_vehicles table...\n")
        
        # Create table
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS zone_vehicles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                zone_id INT NOT NULL,
                vehicle_id INT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (zone_id) REFERENCES trip_cards(zone_id) ON DELETE CASCADE,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
                UNIQUE KEY unique_zone_vehicle (zone_id, vehicle_id)
            )
        """))
        
        print("✅ Table created successfully")
        
        # Create indexes for performance
        print("\n📊 Creating indexes...")
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_zone_vehicles_zone_id 
            ON zone_vehicles(zone_id)
        """))
        print("✅ Index on zone_id created")
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_zone_vehicles_vehicle_id 
            ON zone_vehicles(vehicle_id)
        """))
        print("✅ Index on vehicle_id created")
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_zone_vehicles_is_active 
            ON zone_vehicles(is_active)
        """))
        print("✅ Index on is_active created")
        
        db.commit()
        
        print("\n" + "="*60)
        print("✅ zone_vehicles table setup complete!")
        print("="*60)
        
        # Show table structure
        print("\n📋 Table structure:")
        result = db.execute(text("DESCRIBE zone_vehicles"))
        for row in result:
            print(f"  {row[0]:<15} {row[1]:<20} {row[2]:<5} {row[3]:<5}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_zone_vehicles_table()
