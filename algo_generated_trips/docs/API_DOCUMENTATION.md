API DOCUMENTATION
=================

base url: http://localhost:8000/api/v1


VEHICLE MANAGEMENT
==================

create vehicle
--------------
POST /vehicles

request:
{
  "vehicle_number": "V016",
  "capacity_kg": 1500
}

response: 201
{
  "vehicle_id": 16,
  "vehicle_number": "V016",
  "capacity_kg": 1500.0,
  "is_active": true,
  "created_at": "2024-12-26T10:00:00"
}


list vehicles
-------------
GET /vehicles?active_only=true

response: 200
{
  "total": 15,
  "vehicles": [...]
}


get vehicle
-----------
GET /vehicles/{vehicle_id}

response: 200
{
  "vehicle_id": 1,
  "vehicle_number": "V001",
  "capacity_kg": 1500.0,
  "is_active": true,
  "created_at": "2024-12-26T10:00:00"
}


update vehicle
--------------
PUT /vehicles/{vehicle_id}

request:
{
  "capacity_kg": 2000
}

response: 200
{...updated vehicle...}


delete vehicle
--------------
DELETE /vehicles/{vehicle_id}?hard_delete=false

response: 200
{
  "message": "Vehicle 16 deactivated",
  "vehicle_id": 16
}


ZONE-VEHICLE ASSIGNMENT
=======================

assign vehicle to zone
----------------------
POST /zones/{zone_id}/vehicles

request:
{
  "vehicle_id": 16
}

response: 201
{
  "id": 1,
  "zone_id": 30001,
  "zone_name": "ATTAPUR",
  "vehicle_id": 16,
  "vehicle_number": "V016",
  "capacity_kg": 1500.0,
  "assigned_at": "2024-12-26T10:00:00",
  "is_active": true
}


list zone vehicles
------------------
GET /zones/{zone_id}/vehicles?active_only=true

response: 200
{
  "zone_id": 30001,
  "zone_name": "ATTAPUR",
  "total": 2,
  "vehicles": [...]
}


unassign vehicle from zone
---------------------------
DELETE /zones/{zone_id}/vehicles/{vehicle_id}?hard_delete=false

response: 200
{
  "message": "Vehicle 16 unassigned from zone 30001",
  "zone_id": 30001,
  "vehicle_id": 16
}


PINCODE MANAGEMENT
==================

add pincode to zone
-------------------
POST /zones/{zone_id}/pincodes

request:
{
  "pincode": "500099"
}

response: 201
{
  "id": 36,
  "zone_id": 30001,
  "zone_name": "ATTAPUR",
  "pincode": "500099",
  "created_at": "2024-12-26T10:00:00"
}


list zone pincodes
------------------
GET /zones/{zone_id}/pincodes

response: 200
{
  "zone_id": 30001,
  "zone_name": "ATTAPUR",
  "total": 7,
  "pincodes": ["500030", "500048", "500052", "500064", "500077", "500264", "500099"]
}


remove pincode from zone
-------------------------
DELETE /zones/{zone_id}/pincodes/{pincode}

response: 200
{
  "message": "Pincode 500099 removed from zone 30001",
  "zone_id": 30001,
  "pincode": "500099"
}


get pincode zone
----------------
GET /pincodes/{pincode}

response: 200
{
  "id": 1,
  "zone_id": 30001,
  "zone_name": "ATTAPUR",
  "pincode": "500030",
  "created_at": "2024-12-26T10:00:00"
}


move pincode to different zone
-------------------------------
PUT /pincodes/{pincode}

request:
{
  "new_zone_id": 30002
}

response: 200
{
  "id": 1,
  "zone_id": 30002,
  "zone_name": "GOLCONDA",
  "pincode": "500030",
  "created_at": "2024-12-26T10:00:00"
}


TRIP GENERATION
===============

generate trips
--------------
POST /trips/generate

request (all zones):
{
  "day": "26"
}

request (specific zones):
{
  "day": "26",
  "zones": ["ATTAPUR", "GOLCONDA"]
}

request (with capacity override):
{
  "day": "26",
  "capacity_override": 2000
}

response: 200
{
  "job_id": "gen_26_20241226_100000",
  "status": "completed",
  "day": "26",
  "zones_processed": ["ATTAPUR", "GOLCONDA", "NARSINGI", ...],
  "total_trips": 12,
  "total_orders": 120,
  "started_at": "2024-12-26T10:00:00",
  "completed_at": "2024-12-26T10:01:30",
  "output_files": {
    "map": "path/to/map.html",
    "json": "path/to/data.json",
    "csv": "path/to/data.csv",
    "summary": "path/to/summary.txt"
  }
}


get trip results
----------------
GET /trips/results/{day}

response: 200
[
  {
    "trip_name": "ATTA1",
    "zone": "ATTAPUR",
    "vehicle_number": "V001",
    "vehicle_capacity_kg": 1500.0,
    "order_count": 12,
    "total_weight": 930.93,
    "utilization_percent": 62.1
  },
  ...
]


ERROR RESPONSES
===============

400 bad request
{
  "detail": "Vehicle number 'V001' already exists"
}

404 not found
{
  "detail": "Vehicle 999 not found"
}

500 internal server error
{
  "detail": "Database connection error"
}


TESTING WITH CURL
=================

create vehicle:
curl -X POST http://localhost:8000/api/v1/vehicles \
  -H "Content-Type: application/json" \
  -d '{"vehicle_number":"V016","capacity_kg":1500}'

list vehicles:
curl http://localhost:8000/api/v1/vehicles

assign vehicle to zone:
curl -X POST http://localhost:8000/api/v1/zones/30001/vehicles \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":16}'

add pincode:
curl -X POST http://localhost:8000/api/v1/zones/30001/pincodes \
  -H "Content-Type: application/json" \
  -d '{"pincode":"500099"}'

generate trips:
curl -X POST http://localhost:8000/api/v1/trips/generate \
  -H "Content-Type: application/json" \
  -d '{"day":"26"}'

generate trips for specific zones:
curl -X POST http://localhost:8000/api/v1/trips/generate \
  -H "Content-Type: application/json" \
  -d '{"day":"26","zones":["ATTAPUR","GOLCONDA"]}'


INTERACTIVE API DOCS
====================

fastapi provides automatic interactive api documentation:

swagger ui: http://localhost:8000/docs
redoc: http://localhost:8000/redoc

these provide:
- complete api reference
- request/response schemas
- try it out functionality
- authentication (if configured)
