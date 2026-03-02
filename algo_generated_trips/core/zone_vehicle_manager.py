"""
Zone-Vehicle Manager - Handles vehicle assignment per zone
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SessionLocal
from sqlalchemy import text

class ZoneVehicleManager:
    """
    Manages vehicle assignments for zones
    """
    
    def __init__(self):
        self.zone_vehicles = {}  # Cache: {zone_id: [vehicles]}
        self.all_vehicles = []
        self.load_all_vehicles()
    
    def load_all_vehicles(self):
        """
        Load all available vehicles from database
        """
        db = SessionLocal()
        
        try:
            result = db.execute(text("""
                SELECT vehicle_id, vehicle_number, capacity_kg
                FROM vehicles
                WHERE is_active = 1
                ORDER BY vehicle_id
            """))
            
            self.all_vehicles = [
                {
                    'vehicle_id': row[0],
                    'vehicle_number': row[1],
                    'capacity_kg': float(row[2])
                }
                for row in result.fetchall()
            ]
            
            print(f"✅ Loaded {len(self.all_vehicles)} total available vehicles")
            
        except Exception as e:
            print(f"❌ Error loading vehicles: {e}")
        finally:
            db.close()
    
    def get_vehicles_for_zone(self, zone_name: str):
        """
        Get vehicles assigned to a specific zone
        If no vehicles assigned, returns all available vehicles
        
        Args:
            zone_name: Zone name (e.g., "ATTAPUR")
        
        Returns:
            List of vehicle dictionaries
        """
        db = SessionLocal()
        
        try:
            # Get zone_id from zone_name
            result = db.execute(
                text("SELECT zone_id FROM trip_cards WHERE zone_name = :name"),
                {"name": zone_name}
            )
            zone = result.fetchone()
            
            if not zone:
                print(f"⚠️  Zone '{zone_name}' not found, using all vehicles")
                return self.all_vehicles
            
            zone_id = zone[0]
            
            # Check cache
            if zone_id in self.zone_vehicles:
                return self.zone_vehicles[zone_id]
            
            # Get assigned vehicles for this zone
            result = db.execute(text("""
                SELECT v.vehicle_id, v.vehicle_number, v.capacity_kg
                FROM zone_vehicles zv
                JOIN vehicles v ON zv.vehicle_id = v.vehicle_id
                WHERE zv.zone_id = :zone_id AND zv.is_active = 1 AND v.is_active = 1
                ORDER BY v.vehicle_id
            """), {"zone_id": zone_id})
            
            assigned_vehicles = [
                {
                    'vehicle_id': row[0],
                    'vehicle_number': row[1],
                    'capacity_kg': float(row[2])
                }
                for row in result.fetchall()
            ]
            
            # If no vehicles assigned to zone, use all available vehicles
            if not assigned_vehicles:
                print(f"ℹ️  No vehicles assigned to {zone_name}, using all available vehicles")
                self.zone_vehicles[zone_id] = self.all_vehicles
                return self.all_vehicles
            
            print(f"✅ Zone {zone_name} has {len(assigned_vehicles)} assigned vehicles")
            self.zone_vehicles[zone_id] = assigned_vehicles
            return assigned_vehicles
            
        except Exception as e:
            print(f"❌ Error getting vehicles for zone {zone_name}: {e}")
            return self.all_vehicles
        finally:
            db.close()
    
    def get_next_vehicle_for_zone(self, zone_name: str, current_index: int):
        """
        Get next vehicle for a zone using round-robin
        
        Args:
            zone_name: Zone name
            current_index: Current vehicle index
        
        Returns:
            Tuple of (vehicle dict, next_index)
        """
        vehicles = self.get_vehicles_for_zone(zone_name)
        
        if not vehicles:
            raise Exception(f"No vehicles available for zone {zone_name}")
        
        vehicle = vehicles[current_index % len(vehicles)]
        next_index = (current_index + 1) % len(vehicles)
        
        return vehicle, next_index
    
    def clear_cache(self):
        """
        Clear the zone-vehicle cache (useful after assignments change)
        """
        self.zone_vehicles = {}
        self.load_all_vehicles()
