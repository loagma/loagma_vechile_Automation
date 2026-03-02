"""
Zone-Vehicle assignment API routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from api.models.zone import VehicleAssignment, VehicleAssignmentResponse, AssignedVehiclesList

router = APIRouter(prefix="/api/v1/zones", tags=["zone-vehicles"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{zone_id}/vehicles", response_model=VehicleAssignmentResponse, status_code=201)
def assign_vehicle_to_zone(zone_id: int, assignment: VehicleAssignment, db: Session = Depends(get_db)):
    """
    Assign a vehicle to a zone
    """
    try:
        # Check if zone exists
        result = db.execute(
            text("SELECT zone_id, zone_name FROM trip_cards WHERE zone_id = :id"),
            {"id": zone_id}
        )
        zone = result.fetchone()
        if not zone:
            raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
        
        # Check if vehicle exists
        result = db.execute(
            text("SELECT vehicle_id, vehicle_number, capacity_kg FROM vehicles WHERE vehicle_id = :id AND is_active = 1"),
            {"id": assignment.vehicle_id}
        )
        vehicle = result.fetchone()
        if not vehicle:
            raise HTTPException(status_code=404, detail=f"Vehicle {assignment.vehicle_id} not found or inactive")
        
        # Check if already assigned
        result = db.execute(
            text("""
                SELECT id FROM zone_vehicles 
                WHERE zone_id = :zone_id AND vehicle_id = :vehicle_id AND is_active = 1
            """),
            {"zone_id": zone_id, "vehicle_id": assignment.vehicle_id}
        )
        if result.fetchone():
            raise HTTPException(status_code=400, detail=f"Vehicle {assignment.vehicle_id} already assigned to zone {zone_id}")
        
        # Insert assignment
        result = db.execute(
            text("""
                INSERT INTO zone_vehicles (zone_id, vehicle_id, assigned_at, is_active)
                VALUES (:zone_id, :vehicle_id, NOW(), 1)
            """),
            {"zone_id": zone_id, "vehicle_id": assignment.vehicle_id}
        )
        db.commit()
        
        assignment_id = result.lastrowid
        
        # Get the created assignment
        result = db.execute(
            text("""
                SELECT zv.id, zv.zone_id, tc.zone_name, zv.vehicle_id, v.vehicle_number, v.capacity_kg, zv.assigned_at, zv.is_active
                FROM zone_vehicles zv
                JOIN trip_cards tc ON zv.zone_id = tc.zone_id
                JOIN vehicles v ON zv.vehicle_id = v.vehicle_id
                WHERE zv.id = :id
            """),
            {"id": assignment_id}
        )
        row = result.fetchone()
        
        return VehicleAssignmentResponse(
            id=row[0],
            zone_id=row[1],
            zone_name=row[2],
            vehicle_id=row[3],
            vehicle_number=row[4],
            capacity_kg=float(row[5]),
            assigned_at=row[6],
            is_active=bool(row[7])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{zone_id}/vehicles", response_model=AssignedVehiclesList)
def list_zone_vehicles(zone_id: int, active_only: bool = True, db: Session = Depends(get_db)):
    """
    List all vehicles assigned to a zone
    """
    try:
        # Check if zone exists
        result = db.execute(
            text("SELECT zone_id, zone_name FROM trip_cards WHERE zone_id = :id"),
            {"id": zone_id}
        )
        zone = result.fetchone()
        if not zone:
            raise HTTPException(status_code=404, detail=f"Zone {zone_id} not found")
        
        # Get assigned vehicles
        query = """
            SELECT zv.id, zv.zone_id, tc.zone_name, zv.vehicle_id, v.vehicle_number, v.capacity_kg, zv.assigned_at, zv.is_active
            FROM zone_vehicles zv
            JOIN trip_cards tc ON zv.zone_id = tc.zone_id
            JOIN vehicles v ON zv.vehicle_id = v.vehicle_id
            WHERE zv.zone_id = :zone_id
        """
        if active_only:
            query += " AND zv.is_active = 1"
        query += " ORDER BY zv.assigned_at DESC"
        
        result = db.execute(text(query), {"zone_id": zone_id})
        
        vehicles = [
            VehicleAssignmentResponse(
                id=row[0],
                zone_id=row[1],
                zone_name=row[2],
                vehicle_id=row[3],
                vehicle_number=row[4],
                capacity_kg=float(row[5]),
                assigned_at=row[6],
                is_active=bool(row[7])
            )
            for row in result.fetchall()
        ]
        
        return AssignedVehiclesList(
            zone_id=zone[0],
            zone_name=zone[1],
            total=len(vehicles),
            vehicles=vehicles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{zone_id}/vehicles/{vehicle_id}")
def unassign_vehicle_from_zone(zone_id: int, vehicle_id: int, hard_delete: bool = False, db: Session = Depends(get_db)):
    """
    Unassign a vehicle from a zone
    """
    try:
        # Check if assignment exists
        result = db.execute(
            text("""
                SELECT id FROM zone_vehicles 
                WHERE zone_id = :zone_id AND vehicle_id = :vehicle_id AND is_active = 1
            """),
            {"zone_id": zone_id, "vehicle_id": vehicle_id}
        )
        assignment = result.fetchone()
        if not assignment:
            raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not assigned to zone {zone_id}")
        
        if hard_delete:
            # Hard delete
            db.execute(
                text("DELETE FROM zone_vehicles WHERE zone_id = :zone_id AND vehicle_id = :vehicle_id"),
                {"zone_id": zone_id, "vehicle_id": vehicle_id}
            )
            message = f"Vehicle {vehicle_id} permanently removed from zone {zone_id}"
        else:
            # Soft delete
            db.execute(
                text("""
                    UPDATE zone_vehicles SET is_active = 0 
                    WHERE zone_id = :zone_id AND vehicle_id = :vehicle_id
                """),
                {"zone_id": zone_id, "vehicle_id": vehicle_id}
            )
            message = f"Vehicle {vehicle_id} unassigned from zone {zone_id}"
        
        db.commit()
        
        return {"message": message, "zone_id": zone_id, "vehicle_id": vehicle_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
