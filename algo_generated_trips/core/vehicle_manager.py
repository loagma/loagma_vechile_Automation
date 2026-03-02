"""
Vehicle manager module - Handles vehicle assignment to trips
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database import SessionLocal
from sqlalchemy import text

class VehicleManager:
    """
    Manages vehicle pool and assignment to trips
    """
    
    def __init__(self):
        self.vehicles = []
        self.current_index = 0
        self.load_vehicles()
    
    def load_vehicles(self):
        """
        Load available vehicles from database
        """
        db = SessionLocal()
        
        try:
            result = db.execute(text("""
                SELECT vehicle_id, vehicle_number, capacity_kg
                FROM vehicles
                WHERE is_active = 1
                ORDER BY vehicle_id
            """))
            
            self.vehicles = [
                {
                    'vehicle_id': row[0],
                    'vehicle_number': row[1],
                    'capacity_kg': float(row[2])  # Convert Decimal to float
                }
                for row in result.fetchall()
            ]
            
            print(f"✅ Loaded {len(self.vehicles)} available vehicles")
            
        except Exception as e:
            print(f"❌ Error loading vehicles: {e}")
        finally:
            db.close()
    
    def get_next_vehicle(self):
        """
        Get next available vehicle using round-robin assignment
        
        Returns:
            Vehicle dictionary with id, number, and capacity
        """
        if not self.vehicles:
            raise Exception("No vehicles available!")
        
        vehicle = self.vehicles[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.vehicles)
        
        return vehicle
    
    def get_vehicle_by_capacity(self, required_capacity: float):
        """
        Get vehicle with appropriate capacity
        
        Args:
            required_capacity: Minimum capacity needed
        
        Returns:
            Vehicle dictionary or None if no suitable vehicle found
        """
        suitable_vehicles = [v for v in self.vehicles if v['capacity_kg'] >= required_capacity]
        
        if not suitable_vehicles:
            return None
        
        # Return vehicle with closest capacity
        return min(suitable_vehicles, key=lambda v: v['capacity_kg'])
    
    def get_all_vehicles(self):
        """
        Get list of all available vehicles
        
        Returns:
            List of vehicle dictionaries
        """
        return self.vehicles
    
    def reset_assignment(self):
        """
        Reset round-robin counter
        """
        self.current_index = 0
