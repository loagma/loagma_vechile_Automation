V1 COMPLETION PLAN - Zone-Based Trip Generation

current state:
  - pincode mapping done (35 pincodes -> 10 zones)
  - database tables exist (trip_cards, trip_card_pincode, vehicles)
  - tables are empty, need to populate
  - allocation algorithm exists
  - NOT storing trips in db yet, only local output for review

goal:
  generate trips grouped by zones using pincode mapping, output locally for review


PHASE 1: DATABASE SETUP
========================

step 1.1 - create zones in trip_cards table
  need to insert 11 zones (10 areas + 1 UNKNOWN)
  
  zones to create:
    ATTAPUR
    GOLCONDA
    ASIF NAGAR
    GUDIMALKAPUR
    NARSINGI
    BEGUMPET
    HAKIMPET
    MANIKONDA
    HAFEEZPET
    BADANGPET
    YOUSUFGUDA
    BORABANDA
    UNKNOWN (for orders without pincodes)
  
  fields to populate:
    zone_id: auto increment
    zone_name: area name (ATTAPUR, GOLCONDA, etc)
    vehicle_id: null for now
    status: 'active'
  
  script needed: populate_zones.py

step 1.2 - populate trip_card_pincode table
  insert pincode mappings from our generated PINCODE_TO_AREA dict
  
  for each pincode in mapping:
    get zone_id from trip_cards where zone_name = area
    insert (zone_id, pincode) into trip_card_pincode
  
  35 pincodes to insert
  
  script needed: populate_pincodes.py

step 1.3 - create dummy vehicles
  vehicles are independent entities with their own capacity
  NOT linked to zones in advance
  
  create pool of vehicles for testing:
    10-15 vehicles with varying capacities
    
  fields:
    vehicle_number: V001, V002, V003, etc
    capacity_kg: 1500, 2000, 1200 (mix of capacities)
    is_active: 1
  
  these vehicles will be assigned to trips dynamically
  each trip uses the capacity of its assigned vehicle
  
  script needed: create_dummy_vehicles.py

step 1.4 - NO LINKING NEEDED
  vehicles are NOT pre-linked to zones
  trip_cards.vehicle_id stays null initially
  vehicles get assigned when trips are created


PHASE 2: UPDATE ORDER FETCHER
==============================

step 2.1 - add pincode extraction to order_fetcher.py
  currently it sets pincode = 'N/A'
  need to actually extract from delivery_info
  
  logic:
    try delivery_info['pincode']
    if not found, try regex on address
    if still not found, return None
  
  function: extract_pincode_from_delivery_info(delivery_info)

step 2.2 - add zone lookup function
  given a pincode, find which zone it belongs to
  
  logic:
    query trip_card_pincode table
    SELECT zone_id FROM trip_card_pincode WHERE pincode = ?
    get zone_name from trip_cards
    return zone_name
  
  if pincode not found: return 'UNKNOWN'
  
  function: get_zone_from_pincode(pincode)

step 2.3 - update fetch_orders_from_db
  for each order:
    extract pincode
    get zone from pincode
    add zone_name to order dict
  
  order dict should have:
    order_id
    latitude
    longitude
    zone_name (NEW)
    total_weight_kg
    order_total
    address
    name
    contactno
    pincode (NEW)


PHASE 3: UPDATE TRIP GENERATOR
===============================

step 3.1 - group orders by zone
  after fetching orders, group them by zone_name
  
  zone_orders = {
    'ATTAPUR': [order1, order2, ...],
    'GOLCONDA': [order3, order4, ...],
    'UNKNOWN': [order5, ...]
  }
  
  function: group_orders_by_zone(orders)

step 3.2 - vehicle assignment logic
  NEW APPROACH: vehicles are independent
  
  for each zone:
    get available vehicles from db (is_active = 1)
    for each trip generated in that zone:
      assign next available vehicle
      use that vehicle's capacity for the trip
  
  vehicle assignment can be:
    round-robin (V001, V002, V003, V001, ...)
    capacity-based (assign vehicle with appropriate capacity)
    random (for testing)
  
  for v1: use round-robin assignment

step 3.3 - run allocation per zone
  for each zone:
    get orders for that zone
    get available vehicles list
    
    for generating trips:
      assign vehicle to trip
      use vehicle.capacity_kg for that trip
      run allocation algorithm with that capacity
      generate trip with zone-based name
  
  trip naming:
    ATTAPUR trips -> ATTA1, ATTA2, ATTA3
    GOLCONDA trips -> GOLC1, GOLC2
    UNKNOWN trips -> UNKN1, UNKN2
  
  trip data includes:
    trip_name: ATTA1
    zone_name: ATTAPUR
    vehicle_id: 5 (assigned vehicle)
    vehicle_number: V005
    capacity_used: 1500 kg (from vehicle)
    orders: [...]
  
  use existing generate_trip_name() from config.py

step 3.3 - handle UNKNOWN zone
  orders without pincodes or unmapped pincodes go here
  treat as separate zone
  generate trips normally
  
  log warning for review:
    "X orders in UNKNOWN zone - missing/invalid pincodes"

step 3.4 - update output format
  current output: map visualization, csv
  
  add zone information to output:
    trip_name, zone_name, order_count, total_weight, orders
  
  output files:
    day_26_trips_by_zone.json
    day_26_trips_summary.txt
    day_26_map.html


PHASE 4: TESTING & VALIDATION
==============================

step 4.1 - test on day 26 data
  run: python generate_trips.py --day 26
  
  expected output:
    trips grouped by zones
    trip names like ATTA1, GOLC1, etc
    UNKNOWN zone should be minimal (11 orders missing pincodes)
  
  validate:
    compare with human allocations
    check if geographic clustering makes sense
    verify trip names are meaningful

step 4.2 - test on day 30 data
  run: python generate_trips.py --day 30
  
  watch for:
    new pincodes not in mapping -> go to UNKNOWN
    different order distribution
  
  log new pincodes for manual review

step 4.3 - compare with human allocations
  for day 26:
    human had 14 zones (vehicles)
    we have 10 zones + UNKNOWN
  
  check:
    are orders in same geographic clusters?
    do trip names make sense?
    is UNKNOWN zone reasonable size?

step 4.4 - review and iterate
  check output files
  review UNKNOWN zone orders
  adjust pincode mapping if needed
  update vehicle capacities if needed


PHASE 5: DOCUMENTATION & CLEANUP
=================================

step 5.1 - document the flow
  update DETAILED_FLOW.md with zone-based logic
  document database schema
  add examples

step 5.2 - create usage guide
  how to run the script
  how to interpret output
  how to handle UNKNOWN zone
  how to add new pincodes

step 5.3 - cleanup code
  remove old area_name logic
  add proper error handling
  add logging
  add comments


IMPLEMENTATION ORDER
====================

priority 1 (database setup):
  1. populate_zones.py
  2. populate_pincodes.py
  3. create_dummy_vehicles.py (independent vehicles, NOT linked to zones)

priority 2 (core logic):
  4. update order_fetcher.py (pincode extraction + zone lookup)
  5. add vehicle_manager.py (get available vehicles, assign to trips)
  6. update trip_generator.py (group by zone + vehicle assignment + zone-based naming)

priority 3 (testing):
  7. test on day 26
  8. test on day 30
  9. compare with human allocations

priority 4 (polish):
  10. update output format
  11. documentation
  12. cleanup


EDGE CASES TO HANDLE
====================

1. orders with missing pincodes
   solution: put in UNKNOWN zone

2. orders with invalid pincodes (not 6 digits)
   solution: put in UNKNOWN zone

3. orders with pincodes not in mapping (new areas)
   solution: put in UNKNOWN zone, log for review

4. zone with no orders for a day
   solution: skip that zone, dont generate empty trips

5. zone with too many orders (exceeds vehicle capacity)
   solution: algorithm will create multiple trips (ATTA1, ATTA2, etc)

6. conflicted pincodes (500008 issue)
   solution: already handled, assigned to dominant zone

7. orders with coordinates but no pincode
   solution: UNKNOWN zone (cant use coordinates for zone lookup yet)


METRICS TO TRACK
================

for each run, track:
  - total orders processed
  - orders per zone
  - orders in UNKNOWN zone (%)
  - trips generated per zone
  - average orders per trip
  - average weight per trip
  - pincodes not in mapping (new pincodes)


OUTPUT FOR REVIEW
=================

generate these files for manual review:

1. day_X_trips_by_zone.json
   {
     "ATTAPUR": {
       "trips": [
         {
           "trip_name": "ATTA1", 
           "vehicle_id": 5,
           "vehicle_number": "V005",
           "capacity_kg": 1500,
           "orders": [...], 
           "weight": 1200,
           "utilization": "80%"
         },
         {
           "trip_name": "ATTA2",
           "vehicle_id": 7, 
           "vehicle_number": "V007",
           "capacity_kg": 2000,
           "orders": [...],
           "weight": 1800,
           "utilization": "90%"
         }
       ],
       "total_orders": 25,
       "total_trips": 2
     },
     ...
   }

2. day_X_summary.txt
   Zone-wise summary:
   ATTAPUR: 12 orders, 2 trips
   GOLCONDA: 12 orders, 1 trip
   UNKNOWN: 5 orders, 1 trip
   
   New pincodes found: 500123, 500456
   Missing pincodes: 11 orders

3. day_X_map.html
   interactive map with color-coded zones

4. day_X_unknown_orders.csv
   list of orders in UNKNOWN zone for manual review


QUESTIONS TO RESOLVE
=====================

Q1: should we create GUDIMALKAPUR zone even though it had 0 clean pincodes?
    (all its orders went to other zones due to conflicts)
    
    answer: yes, create it. might get orders in future

Q2: vehicle capacity - use 1500kg for all or different capacities?
    
    answer: vehicles are independent with their own capacities
            each trip uses the capacity of its assigned vehicle
            create mix of vehicles: some 1500kg, some 2000kg, some 1200kg

Q3: should we store trip results in database or keep local only?
    
    answer: local only for v1 (as per your requirement)

Q4: how to handle day 30 new pincodes?
    
    answer: UNKNOWN zone, then manually review and update mapping


ESTIMATED EFFORT
================

phase 1 (db setup): 2 hours
  - write 3 scripts (zones, pincodes, vehicles)
  - test database inserts
  - verify data

phase 2 (order fetcher): 1-2 hours
  - pincode extraction
  - zone lookup
  - testing

phase 3 (trip generator): 3-4 hours
  - group by zone logic
  - vehicle assignment logic (NEW)
  - zone-based naming
  - capacity handling per vehicle
  - output formatting

phase 4 (testing): 2-3 hours
  - run on both days
  - compare results
  - iterate

phase 5 (docs): 1 hour

total: 8-12 hours


NEXT IMMEDIATE STEPS
====================

1. create populate_zones.py script
2. run it to insert 11 zones into trip_cards (vehicle_id = null)
3. create populate_pincodes.py script
4. run it to insert 35 pincode mappings
5. create create_dummy_vehicles.py script
6. run it to create 10-15 independent vehicles with varying capacities
7. verify database has correct data

then move to order_fetcher and vehicle_manager updates

KEY CHANGE: vehicles are independent, NOT pre-linked to zones
            trips get assigned vehicles dynamically during generation
