MANAGEMENT API & ROUTES PLAN
=============================

goal: create api routes to manage vehicles, zones, pincodes, and trigger trip generation


REQUIREMENTS
============

1. vehicle management
   - create new vehicles
   - edit vehicle details (number, capacity)
   - delete/deactivate vehicles
   - list all vehicles

2. zone-vehicle assignment
   - assign vehicles to zones
   - unassign vehicles from zones
   - view zone-vehicle mappings
   - this defines which vehicles are available for which zones

3. zone management
   - create new zones
   - edit zone details (name)
   - delete/deactivate zones
   - list all zones

4. pincode management
   - add pincodes to zones
   - remove pincodes from zones
   - move pincodes between zones
   - list pincodes by zone
   - search which zone a pincode belongs to

5. trip generation control
   - trigger trip generation for specific day
   - specify which zones to process
   - specify custom parameters (capacity override, etc)
   - view generation status/results


ARCHITECTURE
============

option 1: fastapi routes (recommended)
  - add routes to existing main.py
  - use existing database connection
  - return json responses
  - can be called from frontend or postman

option 2: cli commands
  - create management scripts
  - run from command line
  - good for admin tasks

we'll do BOTH - fastapi for programmatic access, cli for quick admin tasks


API ROUTES STRUCTURE
====================

base path: /api/v1/

vehicles:
  POST   /vehicles                    - create vehicle
  GET    /vehicles                    - list all vehicles
  GET    /vehicles/{id}               - get vehicle details
  PUT    /vehicles/{id}               - update vehicle
  DELETE /vehicles/{id}               - deactivate vehicle

zones:
  POST   /zones                       - create zone
  GET    /zones                       - list all zones
  GET    /zones/{id}                  - get zone details
  PUT    /zones/{id}                  - update zone
  DELETE /zones/{id}                  - deactivate zone
  GET    /zones/{id}/pincodes         - get pincodes for zone
  POST   /zones/{id}/pincodes         - add pincode to zone
  DELETE /zones/{id}/pincodes/{pin}   - remove pincode from zone

zone-vehicles:
  POST   /zones/{id}/vehicles         - assign vehicle to zone
  DELETE /zones/{id}/vehicles/{vid}   - unassign vehicle from zone
  GET    /zones/{id}/vehicles         - list vehicles for zone

pincodes:
  GET    /pincodes                    - list all pincodes
  GET    /pincodes/{pin}              - get zone for pincode
  PUT    /pincodes/{pin}              - move pincode to different zone

trip-generation:
  POST   /trips/generate              - trigger trip generation
  GET    /trips/status/{job_id}       - check generation status
  GET    /trips/results/{day}         - get results for day


REQUEST/RESPONSE FORMATS
========================

create vehicle:
  POST /vehicles
  body: {
    "vehicle_number": "V016",
    "capacity_kg": 1500
  }
  response: {
    "vehicle_id": 16,
    "vehicle_number": "V016",
    "capacity_kg": 1500,
    "is_active": true,
    "created_at": "2024-12-26T10:00:00"
  }

assign vehicle to zone:
  POST /zones/30001/vehicles
  body: {
    "vehicle_id": 16
  }
  response: {
    "zone_id": 30001,
    "zone_name": "ATTAPUR",
    "vehicle_id": 16,
    "vehicle_number": "V016",
    "assigned_at": "2024-12-26T10:00:00"
  }

add pincode to zone:
  POST /zones/30001/pincodes
  body: {
    "pincode": "500099"
  }
  response: {
    "zone_id": 30001,
    "zone_name": "ATTAPUR",
    "pincode": "500099",
    "added_at": "2024-12-26T10:00:00"
  }

trigger trip generation:
  POST /trips/generate
  body: {
    "day": "26",
    "zones": ["ATTAPUR", "GOLCONDA"],  // optional, all if not specified
    "capacity_override": 2000           // optional
  }
  response: {
    "job_id": "gen_20241226_001",
    "status": "processing",
    "started_at": "2024-12-26T10:00:00"
  }


DATABASE CHANGES NEEDED
=======================

new table: zone_vehicles
  - id (primary key)
  - zone_id (foreign key to trip_cards)
  - vehicle_id (foreign key to vehicles)
  - assigned_at (timestamp)
  - is_active (boolean)

this allows many-to-many relationship:
  - one zone can have multiple vehicles
  - one vehicle can be assigned to multiple zones


IMPLEMENTATION STEPS
====================

phase 1: database setup
------------------------
step 1.1 - create zone_vehicles table
  script: create_zone_vehicles_table.py
  
  CREATE TABLE zone_vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    zone_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (zone_id) REFERENCES trip_cards(zone_id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    UNIQUE KEY unique_zone_vehicle (zone_id, vehicle_id)
  );

step 1.2 - add indexes for performance
  - index on zone_id
  - index on vehicle_id
  - index on is_active


phase 2: api routes - vehicles
-------------------------------
step 2.1 - create routes/vehicles.py
  implement:
    - create_vehicle()
    - list_vehicles()
    - get_vehicle()
    - update_vehicle()
    - delete_vehicle()

step 2.2 - add validation
  - vehicle_number must be unique
  - capacity_kg must be positive
  - proper error messages

step 2.3 - register routes in main.py
  from routes.vehicles import router as vehicles_router
  app.include_router(vehicles_router, prefix="/api/v1")


phase 3: api routes - zones
----------------------------
step 3.1 - create routes/zones.py
  implement:
    - create_zone()
    - list_zones()
    - get_zone()
    - update_zone()
    - delete_zone()

step 3.2 - add zone details endpoint
  GET /zones/{id}
  returns:
    - zone info
    - pincode count
    - assigned vehicles count
    - recent trip stats


phase 4: api routes - pincodes
-------------------------------
step 4.1 - create routes/pincodes.py
  implement:
    - add_pincode_to_zone()
    - remove_pincode_from_zone()
    - move_pincode()
    - list_pincodes()
    - get_pincode_zone()

step 4.2 - add validation
  - pincode must be 6 digits
  - can't add duplicate pincode to same zone
  - can't remove pincode if it doesn't exist


phase 5: api routes - zone-vehicles
------------------------------------
step 5.1 - create routes/zone_vehicles.py
  implement:
    - assign_vehicle_to_zone()
    - unassign_vehicle_from_zone()
    - list_zone_vehicles()
    - list_vehicle_zones()

step 5.2 - update vehicle_manager.py
  modify get_vehicles_for_zone() to:
    - query zone_vehicles table
    - return only vehicles assigned to that zone
    - if no vehicles assigned, return all available vehicles


phase 6: api routes - trip generation
--------------------------------------
step 6.1 - create routes/trips.py
  implement:
    - trigger_generation()
    - get_generation_status()
    - get_generation_results()

step 6.2 - async job handling
  option 1: simple - run synchronously, return when done
  option 2: advanced - use celery/background tasks
  
  for v1: go with option 1 (simple)

step 6.3 - update generate_trips.py
  add function: generate_trips_api()
  parameters:
    - day: str
    - zones: list (optional)
    - capacity_override: float (optional)
  
  returns:
    - trip_data dict
    - generation_stats


phase 7: cli management commands
---------------------------------
step 7.1 - create cli/manage_vehicles.py
  commands:
    python manage_vehicles.py create --number V016 --capacity 1500
    python manage_vehicles.py list
    python manage_vehicles.py update --id 16 --capacity 2000
    python manage_vehicles.py delete --id 16

step 7.2 - create cli/manage_zones.py
  commands:
    python manage_zones.py create --name "NEW AREA"
    python manage_zones.py list
    python manage_zones.py add-pincode --zone-id 30001 --pincode 500099
    python manage_zones.py remove-pincode --zone-id 30001 --pincode 500099

step 7.3 - create cli/manage_assignments.py
  commands:
    python manage_assignments.py assign --zone-id 30001 --vehicle-id 16
    python manage_assignments.py unassign --zone-id 30001 --vehicle-id 16
    python manage_assignments.py list --zone-id 30001

step 7.4 - create cli/run_generation.py
  commands:
    python run_generation.py --day 26
    python run_generation.py --day 26 --zones ATTAPUR,GOLCONDA
    python run_generation.py --day 26 --capacity 2000


phase 8: update trip generation logic
--------------------------------------
step 8.1 - modify trip_generator.py
  change: generate_trips_for_day()
  
  new logic:
    for each zone:
      get assigned vehicles from zone_vehicles table
      if no vehicles assigned:
        use all available vehicles (current behavior)
      else:
        use only assigned vehicles
      
      for each trip in zone:
        assign vehicle from zone's vehicle pool
        use that vehicle's capacity

step 8.2 - add zone filtering
  add parameter: zones_to_process (optional)
  if specified, only process those zones
  skip other zones

step 8.3 - add capacity override
  add parameter: capacity_override (optional)
  if specified, use this capacity for all trips
  useful for testing different scenarios


phase 9: testing
----------------
step 9.1 - test vehicle crud
  - create vehicles via api
  - update vehicles
  - list vehicles
  - delete vehicles

step 9.2 - test zone-vehicle assignment
  - assign vehicles to zones
  - verify assignments
  - unassign vehicles
  - test with multiple vehicles per zone

step 9.3 - test pincode management
  - add pincodes to zones
  - move pincodes between zones
  - remove pincodes
  - verify trip generation uses new mappings

step 9.4 - test trip generation
  - generate trips for specific zones
  - verify only assigned vehicles are used
  - test capacity override
  - compare results with full generation


phase 10: documentation
------------------------
step 10.1 - create API_DOCUMENTATION.md
  - list all endpoints
  - request/response examples
  - error codes
  - authentication (if needed)

step 10.2 - create CLI_GUIDE.md
  - list all commands
  - usage examples
  - common workflows

step 10.3 - update README.md
  - add management section
  - link to api docs
  - link to cli guide


FOLDER STRUCTURE
================

algo_generated_trips/
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── vehicles.py
│   │   ├── zones.py
│   │   ├── pincodes.py
│   │   ├── zone_vehicles.py
│   │   └── trips.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── vehicle.py
│   │   ├── zone.py
│   │   └── responses.py
│   └── dependencies.py
├── cli/
│   ├── __init__.py
│   ├── manage_vehicles.py
│   ├── manage_zones.py
│   ├── manage_assignments.py
│   └── run_generation.py
├── core/
│   ├── (existing files)
│   └── zone_vehicle_manager.py (new)
├── scripts/
│   ├── (existing files)
│   └── create_zone_vehicles_table.py (new)
└── docs/
    ├── API_DOCUMENTATION.md (new)
    └── CLI_GUIDE.md (new)


EXAMPLE WORKFLOWS
=================

workflow 1: setup new vehicle and assign to zone
  1. POST /vehicles - create vehicle V016 with 1500kg capacity
  2. POST /zones/30001/vehicles - assign V016 to ATTAPUR zone
  3. POST /trips/generate - generate trips, ATTAPUR will use V016

workflow 2: add new pincode to zone
  1. POST /zones/30001/pincodes - add pincode 500099 to ATTAPUR
  2. POST /trips/generate - orders with 500099 will go to ATTAPUR

workflow 3: move pincode between zones
  1. GET /pincodes/500048 - check current zone (ATTAPUR)
  2. DELETE /zones/30001/pincodes/500048 - remove from ATTAPUR
  3. POST /zones/30002/pincodes - add to GOLCONDA
  4. POST /trips/generate - orders with 500048 now go to GOLCONDA

workflow 4: generate trips for specific zones only
  1. POST /trips/generate with body: {"day": "26", "zones": ["ATTAPUR", "GOLCONDA"]}
  2. only ATTAPUR and GOLCONDA trips are generated
  3. other zones are skipped


PRIORITY ORDER
==============

high priority (must have):
  1. vehicle crud api
  2. zone-vehicle assignment api
  3. pincode management api
  4. trip generation api with zone filtering
  5. update trip_generator to use zone-vehicle assignments

medium priority (should have):
  6. cli commands for quick management
  7. zone crud api
  8. api documentation

low priority (nice to have):
  9. async job handling for trip generation
  10. generation status tracking
  11. historical results api


ESTIMATED EFFORT
================

phase 1 (database): 1 hour
phase 2 (vehicle api): 2 hours
phase 3 (zone api): 1 hour
phase 4 (pincode api): 2 hours
phase 5 (zone-vehicle api): 2 hours
phase 6 (trip generation api): 2 hours
phase 7 (cli commands): 2 hours
phase 8 (update trip logic): 2 hours
phase 9 (testing): 2 hours
phase 10 (documentation): 1 hour

total: 17 hours


NEXT STEPS
==========

1. create zone_vehicles table
2. implement vehicle crud api
3. implement zone-vehicle assignment api
4. test basic flow
5. continue with remaining phases

ready to start?
