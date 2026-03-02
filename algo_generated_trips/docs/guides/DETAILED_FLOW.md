# Detailed System Flow - Algorithm Trip Generation

## Complete Data Flow Diagram

```
USER COMMAND
    ↓
[generate_trips.py]
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Configuration Loading                               │
│ Module: config.py                                           │
│ Input: day="26"                                             │
│ Output: {                                                   │
│   user_sheet: "path/to/ vy37r1dlj4_UserSheet.txt",         │
│   vehicle_capacity: 1500.0,                                │
│   date: "2024-12-26"                                       │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Order Fetching                                      │
│ Module: order_fetcher.py                                    │
│                                                             │
│ 2.1: Read User Sheet File                                  │
│      Input: vy37r1dlj4_UserSheet.txt                       │
│      Process: Parse tab-separated file                     │
│      Output: [244541, 244538, 244587, ...]                │
│                                                             │
│ 2.2: Query Database                                        │
│      Input: order_ids = [244541, 244538, ...]             │
│      SQL: SELECT order_id, delivery_info, order_total,     │
│                  area_name FROM orders                      │
│           WHERE order_id IN (244541, 244538, ...)          │
│      Output: Raw database rows                             │
│                                                             │
│ 2.3: Parse & Transform Data                                │
│      Input: Database rows                                   │
│      Process:                                               │
│        - Parse delivery_info JSON                          │
│        - Extract latitude, longitude                       │
│        - Calculate weight from order_total                 │
│        - Clean area names                                  │
│      Output: orders_data = {                               │
│        'orders': [                                         │
│          {                                                 │
│            'order_id': 244541,                            │
│            'latitude': 17.3850,                           │
│            'longitude': 78.4867,                          │
│            'area_name': 'ATTAPUR',                        │
│            'total_weight_kg': 79.72,                      │
│            'order_total': 7972.00,                        │
│            'address': '...',                              │
│            'name': 'Customer Name',                       │
│            'contactno': '9398691724'                      │
│          },                                                │
│          ...                                               │
│        ],                                                  │
│        'algo_orders': [                                    │
│          {                                                 │
│            'order_id': 244541,                            │
│            'latitude': 17.3850,                           │
│            'longitude': 78.4867,                          │
│            'pincode': 'N/A',                              │
│            'total_weight_kg': 79.72                       │
│          },                                                │
│          ...                                               │
│        ],                                                  │
│        'order_details': {                                  │
│          244541: {full order object},                     │
│          244538: {full order object},                     │
│          ...                                               │
│        }                                                   │
│      }                                                     │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Trip Generation                                     │
│ Module: trip_generator.py                                   │
│                                                             │
│ 3.1: Run Allocation Algorithm                              │
│      Module Called: alleocation.py (AllocationEngine)      │
│      Input: algo_orders (simplified format)                │
│      Process:                                               │
│        - Preprocess orders (validate weights)              │
│        - Cluster orders by geographic proximity            │
│        - Respect vehicle capacity (1500 kg)                │
│        - Calculate route distances                         │
│      Output: algo_result = {                               │
│        'trips': [                                          │
│          {                                                 │
│            'trip_id': 1,                                   │
│            'orders': [244541, 244538, 244587, ...],       │
│            'total_weight': 1450.5,                        │
│            'route_distance_km': 12.3                      │
│          },                                                │
│          {                                                 │
│            'trip_id': 2,                                   │
│            'orders': [244524, 244527, ...],               │
│            'total_weight': 1380.2,                        │
│            'route_distance_km': 10.8                      │
│          },                                                │
│          ...                                               │
│        ],                                                  │
│        'metrics': {                                        │
│          'number_of_trips': 15,                           │
│          'average_utilization_percent': 87.3,             │
│          'total_distance_km': 156.7,                      │
│          'runtime_seconds': 0.234                         │
│        }                                                   │
│      }                                                     │
│                                                             │
│ 3.2: Assign Trip Names                                     │
│      Input: algo_result + order_details                    │
│      Process:                                               │
│        For each trip:                                      │
│          - Count orders per area in trip                   │
│          - Find dominant area (most orders)                │
│          - Convert area to 4-letter code                   │
│            (ATTAPUR → ATTA, GOLCONDA → GOLC)              │
│          - Number trips per area sequentially              │
│            (ATTA1, ATTA2, GOLC1, GOLC2, ...)              │
│          - Calculate utilization %                         │
│      Output: trip_data = {                                 │
│        'trips': [                                          │
│          {                                                 │
│            'trip_id': 1,                                   │
│            'trip_name': 'ATTA1',                          │
│            'area': 'ATTAPUR',                             │
│            'orders': [244541, 244538, 244587, ...],       │
│            'order_count': 12,                             │
│            'total_weight': 1450.5,                        │
│            'utilization_percent': 96.7                    │
│          },                                                │
│          {                                                 │
│            'trip_id': 2,                                   │
│            'trip_name': 'GOLC1',                          │
│            'area': 'GOLCONDA',                            │
│            'orders': [244524, 244527, ...],               │
│            'order_count': 10,                             │
│            'total_weight': 1380.2,                        │
│            'utilization_percent': 92.0                    │
│          },                                                │
│          ...                                               │
│        ],                                                  │
│        'assignments': {                                    │
│          244541: 'ATTA1',                                 │
│          244538: 'ATTA1',                                 │
│          244587: 'ATTA1',                                 │
│          244524: 'GOLC1',                                 │
│          ...                                               │
│        },                                                  │
│        'metrics': {same as algo_result},                  │
│        'order_details': {full order info}                 │
│      }                                                     │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Map Visualization                                   │
│ Module: map_visualizer.py                                   │
│                                                             │
│ Input: trip_data (from step 3)                             │
│                                                             │
│ Process:                                                    │
│   4.1: Calculate Map Center                                │
│        - Average all latitudes                             │
│        - Average all longitudes                            │
│        - Center = (avg_lat, avg_lon)                       │
│                                                             │
│   4.2: Create Base Map                                     │
│        - Use folium library                                │
│        - Center at calculated point                        │
│        - Zoom level: 12                                    │
│                                                             │
│   4.3: Assign Colors                                       │
│        - Generate unique color per trip                    │
│        - Colors: ['red', 'blue', 'green', ...]            │
│        - Trip 1 → red, Trip 2 → blue, etc.                │
│                                                             │
│   4.4: Plot Each Trip                                      │
│        For each trip:                                      │
│          For each order in trip:                           │
│            - Add CircleMarker at (lat, lon)               │
│            - Color = trip color                           │
│            - Popup = order details HTML                   │
│            - Label = trip name (e.g., "ATTA1")            │
│          - Draw PolyLine connecting all orders            │
│            (route line in trip color)                     │
│                                                             │
│   4.5: Add Legend                                          │
│        - List all trips with colors                        │
│        - Show order count, weight, utilization            │
│        - Display overall metrics                          │
│                                                             │
│ Output: HTML file saved to                                 │
│         outputs/day_26/algo_trips_day_26.html              │
│                                                             │
│ Map Features:                                               │
│   - Interactive (zoom, pan, click)                         │
│   - Color-coded trips                                      │
│   - Clickable markers with popups                         │
│   - Route lines                                            │
│   - Legend with statistics                                │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Data Export                                         │
│ Module: data_exporter.py                                    │
│                                                             │
│ Input: trip_data (from step 3)                             │
│                                                             │
│ 5.1: Export to JSON                                        │
│      Output File: outputs/day_26/algo_trips_day_26.json    │
│      Structure: {                                          │
│        "day": "26",                                        │
│        "date": "2024-12-26",                              │
│        "vehicle_capacity": 1500,                          │
│        "total_orders": 123,                               │
│        "total_trips": 15,                                 │
│        "metrics": {...},                                  │
│        "trips": [...],                                    │
│        "order_assignments": {...}                         │
│      }                                                     │
│      Use Case: Programmatic analysis, APIs                │
│                                                             │
│ 5.2: Export to CSV                                         │
│      Output File: outputs/day_26/algo_trips_day_26.csv     │
│      Columns:                                              │
│        order_id, trip_name, area, weight_kg,              │
│        order_total, latitude, longitude,                  │
│        customer_name, contact, address                    │
│      Rows: One row per order                              │
│      Use Case: Excel analysis, filtering, sorting         │
│                                                             │
│ 5.3: Export to Text Summary                                │
│      Output File: outputs/day_26/algo_trips_day_26_       │
│                   summary.txt                              │
│      Content:                                              │
│        - Header with date, capacity, totals               │
│        - Trip-by-trip breakdown                           │
│        - Order IDs per trip                               │
│      Use Case: Quick reading, reports                     │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Console Output                                      │
│ Module: generate_trips.py (print_summary)                  │
│                                                             │
│ Displays:                                                   │
│   ======================================================    │
│   TRIP GENERATION SUMMARY - DAY 26                         │
│   ======================================================    │
│                                                             │
│   📊 Overall Statistics:                                   │
│      Total Orders: 123                                     │
│      Total Trips: 15                                       │
│      Average Orders/Trip: 8.2                              │
│      Average Utilization: 87.3%                            │
│      Total Distance: 156.7 km                              │
│                                                             │
│   🚚 Trip Breakdown:                                       │
│      Trip Name    Area       Orders  Weight    Util%       │
│      ------------------------------------------------       │
│      ATTA1        ATTAPUR    12      1450.5    96.7       │
│      GOLC1        GOLCONDA   10      1380.2    92.0       │
│      ASIF1        ASIF NAGAR 8       1120.8    74.7       │
│      ...                                                   │
│                                                             │
│   ✅ Day 26 processing complete!                           │
│                                                             │
│   📁 Output files:                                         │
│      Map: outputs/day_26/algo_trips_day_26.html            │
│      JSON: outputs/day_26/algo_trips_day_26.json           │
│      CSV: outputs/day_26/algo_trips_day_26.csv             │
│      Summary: outputs/day_26/algo_trips_day_26_summary.txt │
└─────────────────────────────────────────────────────────────┘
```

---

## Module-by-Module Breakdown

### 1. config.py - Configuration Store

**Purpose:** Central configuration for days and area mappings

**Data Stored:**
```python
DAY_CONFIGS = {
    "26": {
        "user_sheet": "../human_made_trips_visualization/vy37r1dlj4_UserSheet.txt",
        "date": "2024-12-26",
        "vehicle_capacity": 1500.0,
        "description": "December 26th orders"
    },
    "30": {...}
}

AREA_CODE_MAPPING = {
    "ATTAPUR": "ATTA",
    "GOLCONDA": "GOLC",
    "ASIF NAGAR": "ASIF",
    ...
}
```

**Functions:**
- `generate_trip_name(area, number)` → "ATTA1"
- `get_area_code(area)` → "ATTA"

**Used By:** All modules for configuration

---

### 2. order_fetcher.py - Data Extraction

**Purpose:** Fetch orders from user sheet and database

**Input Sources:**
1. User Sheet File (vy37r1dlj4_UserSheet.txt)
2. MySQL Database (orders table)

**Functions:**

#### `read_order_ids_from_sheet(file_path)`
- **Input:** Path to user sheet
- **Process:** 
  - Skip line 1 (title)
  - Parse line 2 (headers)
  - Read lines 3+ (data)
  - Extract OrderId column
- **Output:** `[244541, 244538, 244587, ...]`

#### `fetch_orders_from_db(order_ids)`
- **Input:** List of order IDs
- **SQL Query:**
  ```sql
  SELECT order_id, delivery_info, order_total, area_name
  FROM orders
  WHERE order_id IN (244541, 244538, ...)
  ```
- **Process:**
  - Parse delivery_info JSON
  - Extract lat/lon
  - Calculate weight
  - Clean area names
- **Output:** List of order dictionaries

#### `prepare_orders_for_algorithm(orders)`
- **Input:** Full order list
- **Process:** Simplify to algorithm format
- **Output:** Minimal order list for algorithm

#### `fetch_orders_for_day(user_sheet_path)` - MAIN FUNCTION
- **Orchestrates:** All above functions
- **Output:**
  ```python
  {
      'orders': [full order objects],
      'algo_orders': [simplified for algorithm],
      'order_details': {order_id: full_object}
  }
  ```

---

### 3. trip_generator.py - Algorithm Execution

**Purpose:** Run algorithm and assign trip names

**Functions:**

#### `run_allocation_algorithm(orders, capacity)`
- **Input:** Simplified orders, vehicle capacity
- **Calls:** `AllocationEngine` from alleocation.py
- **Algorithm Process:**
  1. Validate orders (weight > 0, weight ≤ capacity)
  2. Select seed order (highest neighbor density)
  3. Build trip by adding nearest orders
  4. Stop when capacity reached
  5. Repeat for remaining orders
  6. Calculate distances
- **Output:**
  ```python
  {
      'trips': [
          {
              'trip_id': 1,
              'orders': [order_ids],
              'total_weight': 1450.5,
              'route_distance_km': 12.3
          },
          ...
      ],
      'metrics': {
          'number_of_trips': 15,
          'average_utilization_percent': 87.3,
          'total_distance_km': 156.7
      }
  }
  ```

#### `get_dominant_area(trip_orders, order_details)`
- **Input:** Order IDs in trip, order details
- **Process:** Count orders per area, return most common
- **Output:** "ATTAPUR" or "GOLCONDA" etc.

#### `assign_trip_names(algo_result, order_details, capacity)`
- **Input:** Algorithm output, order details, capacity
- **Process:**
  1. For each trip:
     - Find dominant area
     - Get area code (ATTAPUR → ATTA)
     - Increment counter for that area
     - Generate name (ATTA1, ATTA2, etc.)
     - Calculate utilization %
  2. Create assignments map (order_id → trip_name)
- **Output:**
  ```python
  {
      'trips': [
          {
              'trip_id': 1,
              'trip_name': 'ATTA1',
              'area': 'ATTAPUR',
              'orders': [order_ids],
              'order_count': 12,
              'total_weight': 1450.5,
              'utilization_percent': 96.7
          },
          ...
      ],
      'assignments': {
          244541: 'ATTA1',
          244538: 'ATTA1',
          ...
      },
      'metrics': {...},
      'order_details': {...}
  }
  ```

#### `generate_trips_for_day(orders_data, capacity)` - MAIN FUNCTION
- **Orchestrates:** Algorithm run + name assignment
- **Output:** Complete trip data with names

---

### 4. map_visualizer.py - Visual Output

**Purpose:** Create interactive HTML map

**Functions:**

#### `generate_color_palette(num_trips)`
- **Input:** Number of trips
- **Output:** List of colors ['red', 'blue', 'green', ...]

#### `create_order_popup(order, trip_name, color)`
- **Input:** Order details, trip name, color
- **Output:** HTML string for popup
  ```html
  <div>
      <h4>Trip: ATTA1</h4>
      <b>Order ID:</b> 244541<br>
      <b>Customer:</b> John Doe<br>
      <b>Area:</b> ATTAPUR<br>
      ...
  </div>
  ```

#### `create_trip_map(trip_data, day, output_dir)` - MAIN FUNCTION
- **Input:** Trip data, day, output directory
- **Process:**
  1. Calculate center point (average lat/lon)
  2. Create folium map
  3. Assign colors to trips
  4. For each trip:
     - For each order:
       - Add CircleMarker (colored dot)
       - Add popup with details
       - Add label with trip name
     - Draw PolyLine (route)
  5. Add legend with statistics
  6. Save as HTML
- **Output:** HTML file path

**Map Elements:**
- Base map (OpenStreetMap tiles)
- Circle markers (orders)
- Labels (trip names)
- Polylines (routes)
- Popups (order details)
- Legend (trip summary)

---

### 5. data_exporter.py - Data Persistence

**Purpose:** Save data in multiple formats

**Functions:**

#### `export_to_json(trip_data, day, capacity, output_dir)`
- **Creates:** Structured JSON file
- **Use Case:** Programmatic analysis

#### `export_to_csv(trip_data, day, output_dir)`
- **Creates:** Flat CSV file (one row per order)
- **Use Case:** Excel analysis

#### `export_summary_text(trip_data, day, capacity, output_dir)`
- **Creates:** Human-readable text summary
- **Use Case:** Quick reading, reports

#### `export_all_formats(...)` - MAIN FUNCTION
- **Calls:** All three export functions
- **Output:** Dictionary with all file paths

---

### 6. generate_trips.py - Main Orchestrator

**Purpose:** Command-line interface and workflow coordination

**Functions:**

#### `print_banner()`
- Displays welcome message

#### `print_summary(trip_data, day)`
- Displays formatted console output

#### `generate_for_day(day, custom_capacity)` - CORE WORKFLOW
- **Steps:**
  1. Load config
  2. Fetch orders (order_fetcher)
  3. Generate trips (trip_generator)
  4. Print summary
  5. Create map (map_visualizer)
  6. Export data (data_exporter)
  7. Show file locations

#### `main()` - ENTRY POINT
- Parses command-line arguments
- Calls generate_for_day()
- Handles "all" option (both days)

---

## Data Transformation Journey

### Stage 1: Raw User Sheet
```
prepareOrderNotify
PhoneNumber    OrderId    VehicleNumber    BillNo    BillAmount
9398691724     244541     ATTAPUR 1        999       7972.00
```

### Stage 2: Order IDs List
```python
[244541, 244538, 244587, ...]
```

### Stage 3: Database Records
```python
{
    'order_id': 244541,
    'delivery_info': '{"latitude": 17.3850, "longitude": 78.4867, ...}',
    'order_total': 7972.00,
    'area_name': 'ATTAPUR'
}
```

### Stage 4: Parsed Orders
```python
{
    'order_id': 244541,
    'latitude': 17.3850,
    'longitude': 78.4867,
    'area_name': 'ATTAPUR',
    'total_weight_kg': 79.72,
    'order_total': 7972.00,
    'address': '...',
    'name': 'Customer Name',
    'contactno': '9398691724'
}
```

### Stage 5: Algorithm Input
```python
{
    'order_id': 244541,
    'latitude': 17.3850,
    'longitude': 78.4867,
    'pincode': 'N/A',
    'total_weight_kg': 79.72
}
```

### Stage 6: Algorithm Output
```python
{
    'trip_id': 1,
    'orders': [244541, 244538, 244587],
    'total_weight': 1450.5,
    'route_distance_km': 12.3
}
```

### Stage 7: Named Trips
```python
{
    'trip_id': 1,
    'trip_name': 'ATTA1',
    'area': 'ATTAPUR',
    'orders': [244541, 244538, 244587],
    'order_count': 3,
    'total_weight': 1450.5,
    'utilization_percent': 96.7
}
```

### Stage 8: Final Outputs
- **HTML Map:** Interactive visualization
- **JSON:** Structured data
- **CSV:** Spreadsheet format
- **Text:** Human-readable summary

---

## Error Handling Flow

```
User runs command
    ↓
Validate day parameter
    ↓ (invalid)
    └─→ Print error, exit
    ↓ (valid)
Check user sheet exists
    ↓ (not found)
    └─→ Print error, exit
    ↓ (found)
Read order IDs
    ↓ (empty)
    └─→ Print warning, exit
    ↓ (success)
Query database
    ↓ (connection error)
    └─→ Print error, exit
    ↓ (success)
Parse orders
    ↓ (missing coordinates)
    └─→ Skip order, continue
    ↓ (success)
Run algorithm
    ↓ (no valid orders)
    └─→ Print error, exit
    ↓ (success)
Generate outputs
    ↓
Success! ✅
```

---

## Performance Considerations

**Order Fetching:**
- Single SQL query for all orders (efficient)
- JSON parsing per order (moderate)

**Algorithm:**
- O(n²) for distance calculations
- Optimized with sampling for large datasets
- Typical runtime: 0.2-0.5 seconds for 100-150 orders

**Map Generation:**
- Linear with number of orders
- Folium rendering: ~1 second

**Data Export:**
- Linear with number of orders
- File I/O: negligible

**Total Runtime:** ~2-5 seconds for typical day

---

## File Dependencies

```
generate_trips.py
    ├─→ config.py
    ├─→ order_fetcher.py
    │       ├─→ database.py (parent dir)
    │       └─→ config.py
    ├─→ trip_generator.py
    │       ├─→ alleocation.py (parent dir)
    │       └─→ config.py
    ├─→ map_visualizer.py
    │       └─→ folium (external library)
    └─→ data_exporter.py
            └─→ json, csv (standard library)
```

---

## Summary

This system is a **data pipeline** that:
1. **Extracts** orders from files and database
2. **Transforms** them through an allocation algorithm
3. **Enriches** with trip names and metadata
4. **Visualizes** on interactive maps
5. **Exports** in multiple formats

Each module has a single, clear responsibility, making the system modular, maintainable, and easy to understand.
