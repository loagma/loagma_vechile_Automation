"""
Pydantic models for trip generation API
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TripGenerationRequest(BaseModel):
    day: str = Field(..., pattern="^(26|30)$", description="Day to generate trips for (26 or 30)")
    zones: Optional[List[str]] = Field(None, description="Specific zones to process (optional, all if not specified)")
    capacity_override: Optional[float] = Field(None, gt=0, description="Override vehicle capacity for testing")

class TripGenerationResponse(BaseModel):
    job_id: str
    status: str
    day: str
    zones_processed: List[str]
    total_trips: int
    total_orders: int
    started_at: datetime
    completed_at: Optional[datetime]
    output_files: Optional[dict]

class TripSummary(BaseModel):
    trip_name: str
    zone: str
    vehicle_number: str
    vehicle_capacity_kg: float
    order_count: int
    total_weight: float
    utilization_percent: float
