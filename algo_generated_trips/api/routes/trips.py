"""
Trip generation API routes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from api.models.trip import TripGenerationRequest, TripGenerationResponse, TripSummary
from core.config import DAY_CONFIGS
from core.order_fetcher import fetch_orders_for_day
from core.trip_generator import generate_trips_for_day
from utils.map_visualizer import create_trip_map
from utils.data_exporter import export_all_formats
from datetime import datetime
from typing import List

router = APIRouter(prefix="/api/v1/trips", tags=["trips"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/generate", response_model=TripGenerationResponse)
def generate_trips(request: TripGenerationRequest, db: Session = Depends(get_db)):
    """
    Trigger trip generation for a specific day
    """
    try:
        started_at = datetime.now()
        job_id = f"gen_{request.day}_{started_at.strftime('%Y%m%d_%H%M%S')}"
        
        # Validate day
        if request.day not in DAY_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Invalid day: {request.day}. Must be 26 or 30")
        
        config = DAY_CONFIGS[request.day]
        vehicle_capacity = request.capacity_override if request.capacity_override else config['vehicle_capacity']
        
        # Get user sheet path
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        user_sheet_path = os.path.join(script_dir, config['user_sheet'])
        
        if not os.path.exists(user_sheet_path):
            raise HTTPException(status_code=404, detail=f"User sheet not found: {user_sheet_path}")
        
        # Fetch orders
        orders_data = fetch_orders_for_day(user_sheet_path)
        
        if not orders_data['orders']:
            raise HTTPException(status_code=404, detail=f"No orders found for day {request.day}")
        
        # Filter zones if specified
        if request.zones:
            # Validate zones exist
            from sqlalchemy import text
            for zone_name in request.zones:
                result = db.execute(
                    text("SELECT zone_id FROM trip_cards WHERE zone_name = :name"),
                    {"name": zone_name}
                )
                if not result.fetchone():
                    raise HTTPException(status_code=404, detail=f"Zone '{zone_name}' not found")
            
            # Filter orders
            filtered_orders = [o for o in orders_data['orders'] if o['zone_name'] in request.zones]
            orders_data['orders'] = filtered_orders
            orders_data['order_details'] = {
                oid: details for oid, details in orders_data['order_details'].items()
                if details['zone_name'] in request.zones
            }
        
        # Generate trips
        trip_data = generate_trips_for_day(orders_data, vehicle_capacity)
        
        if not trip_data:
            raise HTTPException(status_code=500, detail="Failed to generate trips")
        
        # Create output files
        output_dir = os.path.join(script_dir, "outputs")
        map_file = create_trip_map(trip_data, request.day, output_dir)
        export_files = export_all_formats(trip_data, request.day, vehicle_capacity, output_dir)
        
        completed_at = datetime.now()
        
        # Get zones processed
        zones_processed = list(set(trip['zone'] for trip in trip_data['trips']))
        
        return TripGenerationResponse(
            job_id=job_id,
            status="completed",
            day=request.day,
            zones_processed=zones_processed,
            total_trips=len(trip_data['trips']),
            total_orders=len(trip_data['order_details']),
            started_at=started_at,
            completed_at=completed_at,
            output_files={
                "map": map_file,
                "json": export_files['json'],
                "csv": export_files['csv'],
                "summary": export_files['summary']
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results/{day}", response_model=List[TripSummary])
def get_trip_results(day: str, db: Session = Depends(get_db)):
    """
    Get trip generation results for a day (from last run)
    """
    try:
        # Read from output files
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        json_file = os.path.join(script_dir, "outputs", f"day_{day}", f"algo_trips_day_{day}.json")
        
        if not os.path.exists(json_file):
            raise HTTPException(status_code=404, detail=f"No results found for day {day}")
        
        import json
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        trips = [
            TripSummary(
                trip_name=trip['trip_name'],
                zone=trip['zone'],
                vehicle_number=trip['vehicle_number'],
                vehicle_capacity_kg=trip['vehicle_capacity_kg'],
                order_count=trip['order_count'],
                total_weight=trip['total_weight'],
                utilization_percent=trip['utilization_percent']
            )
            for trip in data['trips']
        ]
        
        return trips
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
