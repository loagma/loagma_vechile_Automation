"""
Pincode management API routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from api.models.zone import PincodeAdd, PincodeResponse, PincodeListResponse, PincodeMove

router = APIRouter(prefix="/api/v1", tags=["pincodes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/zones/{zone_id}/pincodes", response_model=PincodeResponse, status_code=201)
def add_pincode_to_zone(zone_id: int, pincode_data: PincodeAdd, db: Session = Depends(get_db)):
    """
    Add a pincode to a zone
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
        
        # Check if pincode already exists in any zone
        result = db.execute(
            text("""
                SELECT tcp.zone_id, tc.zone_name 
                FROM trip_card_pincode tcp
                JOIN trip_cards tc ON tcp.zone_id = tc.zone_id
                WHERE tcp.pincode = :pincode
            """),
            {"pincode": pincode_data.pincode}
        )
        existing = result.fetchone()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Pincode {pincode_data.pincode} already exists in zone {existing[1]} (ID: {existing[0]})"
            )
        
        # Insert pincode
        result = db.execute(
            text("""
                INSERT INTO trip_card_pincode (zone_id, pincode, created_at)
                VALUES (:zone_id, :pincode, NOW())
            """),
            {"zone_id": zone_id, "pincode": pincode_data.pincode}
        )
        db.commit()
        
        pincode_id = result.lastrowid
        
        # Get the created pincode
        result = db.execute(
            text("""
                SELECT tcp.id, tcp.zone_id, tc.zone_name, tcp.pincode, tcp.created_at
                FROM trip_card_pincode tcp
                JOIN trip_cards tc ON tcp.zone_id = tc.zone_id
                WHERE tcp.id = :id
            """),
            {"id": pincode_id}
        )
        row = result.fetchone()
        
        return PincodeResponse(
            id=row[0],
            zone_id=row[1],
            zone_name=row[2],
            pincode=row[3],
            created_at=row[4]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/zones/{zone_id}/pincodes", response_model=PincodeListResponse)
def list_zone_pincodes(zone_id: int, db: Session = Depends(get_db)):
    """
    List all pincodes for a zone
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
        
        # Get pincodes
        result = db.execute(
            text("SELECT pincode FROM trip_card_pincode WHERE zone_id = :zone_id ORDER BY pincode"),
            {"zone_id": zone_id}
        )
        
        pincodes = [row[0] for row in result.fetchall()]
        
        return PincodeListResponse(
            zone_id=zone[0],
            zone_name=zone[1],
            total=len(pincodes),
            pincodes=pincodes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/zones/{zone_id}/pincodes/{pincode}")
def remove_pincode_from_zone(zone_id: int, pincode: str, db: Session = Depends(get_db)):
    """
    Remove a pincode from a zone
    """
    try:
        # Check if pincode exists in this zone
        result = db.execute(
            text("SELECT id FROM trip_card_pincode WHERE zone_id = :zone_id AND pincode = :pincode"),
            {"zone_id": zone_id, "pincode": pincode}
        )
        if not result.fetchone():
            raise HTTPException(status_code=404, detail=f"Pincode {pincode} not found in zone {zone_id}")
        
        # Delete pincode
        db.execute(
            text("DELETE FROM trip_card_pincode WHERE zone_id = :zone_id AND pincode = :pincode"),
            {"zone_id": zone_id, "pincode": pincode}
        )
        db.commit()
        
        return {"message": f"Pincode {pincode} removed from zone {zone_id}", "zone_id": zone_id, "pincode": pincode}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pincodes/{pincode}", response_model=PincodeResponse)
def get_pincode_zone(pincode: str, db: Session = Depends(get_db)):
    """
    Get which zone a pincode belongs to
    """
    try:
        result = db.execute(
            text("""
                SELECT tcp.id, tcp.zone_id, tc.zone_name, tcp.pincode, tcp.created_at
                FROM trip_card_pincode tcp
                JOIN trip_cards tc ON tcp.zone_id = tc.zone_id
                WHERE tcp.pincode = :pincode
            """),
            {"pincode": pincode}
        )
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Pincode {pincode} not found in any zone")
        
        return PincodeResponse(
            id=row[0],
            zone_id=row[1],
            zone_name=row[2],
            pincode=row[3],
            created_at=row[4]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/pincodes/{pincode}", response_model=PincodeResponse)
def move_pincode_to_zone(pincode: str, move_data: PincodeMove, db: Session = Depends(get_db)):
    """
    Move a pincode from one zone to another
    """
    try:
        # Check if pincode exists
        result = db.execute(
            text("SELECT zone_id FROM trip_card_pincode WHERE pincode = :pincode"),
            {"pincode": pincode}
        )
        current = result.fetchone()
        if not current:
            raise HTTPException(status_code=404, detail=f"Pincode {pincode} not found")
        
        # Check if target zone exists
        result = db.execute(
            text("SELECT zone_id, zone_name FROM trip_cards WHERE zone_id = :id"),
            {"id": move_data.new_zone_id}
        )
        new_zone = result.fetchone()
        if not new_zone:
            raise HTTPException(status_code=404, detail=f"Target zone {move_data.new_zone_id} not found")
        
        # Check if already in target zone
        if current[0] == move_data.new_zone_id:
            raise HTTPException(status_code=400, detail=f"Pincode {pincode} already in zone {move_data.new_zone_id}")
        
        # Update pincode zone
        db.execute(
            text("UPDATE trip_card_pincode SET zone_id = :new_zone_id WHERE pincode = :pincode"),
            {"new_zone_id": move_data.new_zone_id, "pincode": pincode}
        )
        db.commit()
        
        # Return updated pincode
        return get_pincode_zone(pincode, db)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
