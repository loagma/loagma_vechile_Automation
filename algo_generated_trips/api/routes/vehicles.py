"""
Vehicle management API routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from api.models.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse, VehicleListResponse
from typing import List

router = APIRouter(prefix="/api/v1/vehicles", tags=["vehicles"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=VehicleResponse, status_code=201)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    """
    Create a new vehicle
    """
    try:
        # Check if vehicle number already exists
        result = db.execute(
            text("SELECT vehicle_id FROM vehicles WHERE vehicle_number = :number"),
            {"number": vehicle.vehicle_number}
        )
        if result.fetchone():
            raise HTTPException(status_code=400, detail=f"Vehicle number '{vehicle.vehicle_number}' already exists")
        
        # Insert vehicle
        result = db.execute(
            text("""
                INSERT INTO vehicles (vehicle_number, capacity_kg, is_active, created_at)
                VALUES (:number, :capacity, 1, NOW())
            """),
            {"number": vehicle.vehicle_number, "capacity": vehicle.capacity_kg}
        )
        db.commit()
        
        # Get the created vehicle
        vehicle_id = result.lastrowid
        result = db.execute(
            text("""
                SELECT vehicle_id, vehicle_number, capacity_kg, is_active, created_at
                FROM vehicles WHERE vehicle_id = :id
            """),
            {"id": vehicle_id}
        )
        row = result.fetchone()
        
        return VehicleResponse(
            vehicle_id=row[0],
            vehicle_number=row[1],
            capacity_kg=float(row[2]),
            is_active=bool(row[3]),
            created_at=row[4]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=VehicleListResponse)
def list_vehicles(active_only: bool = True, db: Session = Depends(get_db)):
    """
    List all vehicles
    """
    try:
        query = "SELECT vehicle_id, vehicle_number, capacity_kg, is_active, created_at FROM vehicles"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY vehicle_id"
        
        result = db.execute(text(query))
        vehicles = [
            VehicleResponse(
                vehicle_id=row[0],
                vehicle_number=row[1],
                capacity_kg=float(row[2]),
                is_active=bool(row[3]),
                created_at=row[4]
            )
            for row in result.fetchall()
        ]
        
        return VehicleListResponse(total=len(vehicles), vehicles=vehicles)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """
    Get vehicle by ID
    """
    try:
        result = db.execute(
            text("""
                SELECT vehicle_id, vehicle_number, capacity_kg, is_active, created_at
                FROM vehicles WHERE vehicle_id = :id
            """),
            {"id": vehicle_id}
        )
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
        
        return VehicleResponse(
            vehicle_id=row[0],
            vehicle_number=row[1],
            capacity_kg=float(row[2]),
            is_active=bool(row[3]),
            created_at=row[4]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: int, vehicle: VehicleUpdate, db: Session = Depends(get_db)):
    """
    Update vehicle details
    """
    try:
        # Check if vehicle exists
        result = db.execute(
            text("SELECT vehicle_id FROM vehicles WHERE vehicle_id = :id"),
            {"id": vehicle_id}
        )
        if not result.fetchone():
            raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
        
        # Build update query
        updates = []
        params = {"id": vehicle_id}
        
        if vehicle.vehicle_number is not None:
            # Check if new number already exists
            result = db.execute(
                text("SELECT vehicle_id FROM vehicles WHERE vehicle_number = :number AND vehicle_id != :id"),
                {"number": vehicle.vehicle_number, "id": vehicle_id}
            )
            if result.fetchone():
                raise HTTPException(status_code=400, detail=f"Vehicle number '{vehicle.vehicle_number}' already exists")
            updates.append("vehicle_number = :number")
            params["number"] = vehicle.vehicle_number
        
        if vehicle.capacity_kg is not None:
            updates.append("capacity_kg = :capacity")
            params["capacity"] = vehicle.capacity_kg
        
        if vehicle.is_active is not None:
            updates.append("is_active = :active")
            params["active"] = vehicle.is_active
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Update vehicle
        db.execute(
            text(f"UPDATE vehicles SET {', '.join(updates)} WHERE vehicle_id = :id"),
            params
        )
        db.commit()
        
        # Return updated vehicle
        return get_vehicle(vehicle_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, hard_delete: bool = False, db: Session = Depends(get_db)):
    """
    Delete (deactivate) vehicle
    """
    try:
        # Check if vehicle exists
        result = db.execute(
            text("SELECT vehicle_id FROM vehicles WHERE vehicle_id = :id"),
            {"id": vehicle_id}
        )
        if not result.fetchone():
            raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
        
        if hard_delete:
            # Hard delete (remove from database)
            db.execute(
                text("DELETE FROM vehicles WHERE vehicle_id = :id"),
                {"id": vehicle_id}
            )
            message = f"Vehicle {vehicle_id} permanently deleted"
        else:
            # Soft delete (deactivate)
            db.execute(
                text("UPDATE vehicles SET is_active = 0 WHERE vehicle_id = :id"),
                {"id": vehicle_id}
            )
            message = f"Vehicle {vehicle_id} deactivated"
        
        db.commit()
        
        return {"message": message, "vehicle_id": vehicle_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("")
def delete_all_vehicles(hard_delete: bool = False, confirm: bool = False, db: Session = Depends(get_db)):
    """
    Delete (deactivate) all vehicles
    
    WARNING: This will affect all vehicles in the system!
    Set confirm=true to proceed.
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=400, 
                detail="This operation requires confirmation. Set confirm=true to proceed."
            )
        
        # Get count of vehicles
        result = db.execute(text("SELECT COUNT(*) FROM vehicles"))
        total_count = result.fetchone()[0]
        
        if total_count == 0:
            return {"message": "No vehicles to delete", "deleted_count": 0}
        
        if hard_delete:
            # Hard delete (remove from database)
            # This will also remove zone_vehicle assignments due to CASCADE
            db.execute(text("DELETE FROM vehicles"))
            message = f"Permanently deleted {total_count} vehicles"
        else:
            # Soft delete (deactivate all)
            db.execute(text("UPDATE vehicles SET is_active = 0"))
            message = f"Deactivated {total_count} vehicles"
        
        db.commit()
        
        return {
            "message": message,
            "deleted_count": total_count,
            "hard_delete": hard_delete
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
