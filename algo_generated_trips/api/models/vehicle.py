"""
Pydantic models for vehicle API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class VehicleCreate(BaseModel):
    vehicle_number: str = Field(..., min_length=1, max_length=50, description="Vehicle number/identifier")
    capacity_kg: float = Field(..., gt=0, description="Vehicle capacity in kg")

class VehicleUpdate(BaseModel):
    vehicle_number: Optional[str] = Field(None, min_length=1, max_length=50)
    capacity_kg: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None

class VehicleResponse(BaseModel):
    vehicle_id: int
    vehicle_number: str
    capacity_kg: float
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class VehicleListResponse(BaseModel):
    total: int
    vehicles: list[VehicleResponse]
