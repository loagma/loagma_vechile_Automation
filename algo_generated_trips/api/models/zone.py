"""
Pydantic models for zone and zone-vehicle API
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ZoneCreate(BaseModel):
    zone_name: str = Field(..., min_length=1, max_length=100, description="Zone name")

class ZoneUpdate(BaseModel):
    zone_name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")

class ZoneResponse(BaseModel):
    zone_id: int
    zone_name: str
    vehicle_id: Optional[int]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ZoneDetailResponse(BaseModel):
    zone_id: int
    zone_name: str
    status: str
    pincode_count: int
    assigned_vehicles_count: int
    created_at: datetime

class ZoneListResponse(BaseModel):
    total: int
    zones: List[ZoneResponse]

# Zone-Vehicle Assignment Models
class VehicleAssignment(BaseModel):
    vehicle_id: int = Field(..., description="Vehicle ID to assign")

class VehicleAssignmentResponse(BaseModel):
    id: int
    zone_id: int
    zone_name: str
    vehicle_id: int
    vehicle_number: str
    capacity_kg: float
    assigned_at: datetime
    is_active: bool

class AssignedVehiclesList(BaseModel):
    zone_id: int
    zone_name: str
    total: int
    vehicles: List[VehicleAssignmentResponse]

# Pincode Models
class PincodeAdd(BaseModel):
    pincode: str = Field(..., pattern="^[0-9]{6}$", description="6-digit pincode")

class PincodeResponse(BaseModel):
    id: int
    zone_id: int
    zone_name: str
    pincode: str
    created_at: datetime

class PincodeListResponse(BaseModel):
    zone_id: int
    zone_name: str
    total: int
    pincodes: List[str]

class PincodeMove(BaseModel):
    new_zone_id: int = Field(..., description="Target zone ID")
