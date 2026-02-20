"""
Example usage of the Allocation Engine

This script demonstrates how to use the Capacitated Spatial Clustering
algorithm for delivery trip generation.
"""
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.allocation.allocation_engine import AllocationEngine


def example_basic_usage():
    """Basic usage example with a few orders."""
    print("="*70)
    print("EXAMPLE 1: Basic Usage")
    print("="*70)
    
    # Sample orders (Bangalore area)
    orders = [
        {
            "order_id": 1,
            "latitude": 12.9716,
            "longitude": 77.5946,
            "pincode": "560001",
            "total_weight_kg": 25.5
        },
        {
            "order_id": 2,
            "latitude": 12.9720,
            "longitude": 77.5950,
            "pincode": "560001",
            "total_weight_kg": 30.0
        },
        {
            "order_id": 3,
            "latitude": 12.9725,
            "longitude": 77.5955,
            "pincode": "560001",
            "total_weight_kg": 45.0
        },
        {
            "order_id": 4,
            "latitude": 12.9800,
            "longitude": 77.6000,
            "pincode": "560002",
            "total_weight_kg": 20.0
        },
    ]
    
    # Initialize engine with 100kg capacity
    engine = AllocationEngine(vehicle_capacity_kg=100.0)
    
    # Run allocation
    result = engine.run(orders)
    
    # Print results
    print(f"\nGenerated {result['metrics']['number_of_trips']} trips")
    print(f"Average utilization: {result['metrics']['average_utilization_percent']}%")
    print(f"Total distance: {result['metrics']['total_distance_km']} km")
    print(f"Runtime: {result['metrics']['runtime_seconds']} seconds")
    
    print("\nTrip Details:")
    for trip in result['trips']:
        print(f"  Trip {trip['trip_id']}: {len(trip['orders'])} orders, "
              f"{trip['total_weight']} kg, {trip['route_distance_km']} km")
        print(f"    Order IDs: {trip['orders']}")
    
    print("\nFull JSON Output:")
    print(json.dumps(result, indent=2))


def example_with_heavy_orders():
    """Example with orders exceeding capacity."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Handling Heavy Orders")
    print("="*70)
    
    orders = [
        {"order_id": 1, "latitude": 12.9716, "longitude": 77.5946, "pincode": "560001", "total_weight_kg": 150},  # Too heavy
        {"order_id": 2, "latitude": 12.9720, "longitude": 77.5950, "pincode": "560001", "total_weight_kg": 20},
        {"order_id": 3, "latitude": 12.9725, "longitude": 77.5955, "pincode": "560001", "total_weight_kg": 30},
        {"order_id": 4, "latitude": 12.9730, "longitude": 77.5960, "pincode": "560001", "total_weight_kg": 25},
    ]
    
    engine = AllocationEngine(vehicle_capacity_kg=100.0)
    result = engine.run(orders)
    
    print(f"\nAllocated {result['metrics']['number_of_trips']} trips")
    print(f"Unallocatable orders: {result['unallocatable_orders']}")
    
    for trip in result['trips']:
        print(f"  Trip {trip['trip_id']}: Orders {trip['orders']}, Weight: {trip['total_weight']} kg")


def example_different_capacities():
    """Example showing different vehicle capacities."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Different Vehicle Capacities")
    print("="*70)
    
    orders = [
        {"order_id": i, "latitude": 12.9716 + i*0.001, "longitude": 77.5946 + i*0.001, 
         "pincode": "560001", "total_weight_kg": 15}
        for i in range(1, 11)
    ]
    
    capacities = [50, 100, 200]
    
    for capacity in capacities:
        engine = AllocationEngine(vehicle_capacity_kg=capacity)
        result = engine.run(orders)
        print(f"\nCapacity {capacity} kg:")
        print(f"  Trips: {result['metrics']['number_of_trips']}")
        print(f"  Utilization: {result['metrics']['average_utilization_percent']}%")


def example_integration_pattern():
    """Example showing how to integrate with FastAPI."""
    print("\n" + "="*70)
    print("EXAMPLE 4: FastAPI Integration Pattern")
    print("="*70)
    
    print("""
# In your FastAPI application:

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.allocation.allocation_engine import AllocationEngine

router = APIRouter()

class OrderInput(BaseModel):
    order_id: int
    latitude: float
    longitude: float
    pincode: str
    total_weight_kg: float

class AllocationRequest(BaseModel):
    orders: List[OrderInput]
    vehicle_capacity_kg: float

@router.post("/api/v1/allocate")
async def allocate_orders(request: AllocationRequest):
    '''Allocate orders to delivery trips.'''
    try:
        engine = AllocationEngine(vehicle_capacity_kg=request.vehicle_capacity_kg)
        orders = [order.dict() for order in request.orders]
        result = engine.run(orders)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Usage:
# POST /api/v1/allocate
# {
#   "vehicle_capacity_kg": 100,
#   "orders": [
#     {"order_id": 1, "latitude": 12.9716, "longitude": 77.5946, 
#      "pincode": "560001", "total_weight_kg": 25.5},
#     ...
#   ]
# }
    """)


if __name__ == "__main__":
    example_basic_usage()
    example_with_heavy_orders()
    example_different_capacities()
    example_integration_pattern()
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70 + "\n")
