# Complete Plan: Area-Based Trip Generation

## What We're Changing

Right now, the algorithm treats all orders as one big pool and creates trips randomly across the city. This doesn't match how humans work - they group orders by area first, then make trips within each area.

We need to change the flow to:
1. Figure out which pincode = which area
2. Group orders by area
3. Run the algorithm separately for each area
4. Name trips properly (ATTA1, ATTA2 for Attapur orders)

## The New Flow

### Current Flow (Wrong)
```
All 123 orders → Algorithm → 15 random trips
```

### New Flow (Correct)
```
All 123 orders
    ↓
Group by area (using pincodes)
    ↓
ATTAPUR: 20 orders → Algorithm → ATTA1, ATTA2
GOLCONDA: 15 orders → Algorithm → GOLC1, GOLC2
ASIF NAGAR: 12 orders → Algorithm → ASIF1
BEGUMPET: 18 orders → Algorithm → BEGU1, BEGU2
...
```

## Example Scenario

Let's say ATTAPUR has 20 orders and vehicle capacity allows max 10 orders per trip:

```
ATTAPUR area (20 orders)
    ↓
Run algorithm with capacity constraint
    ↓
Trip 1: 10 orders, 1450 kg → ATTA1
Trip 2: 10 orders, 1380 kg → ATTA2
```

If ASIF NAGAR only has 8 orders:
```
ASIF NAGAR area (8 orders)
    ↓
Run algorithm
    ↓
Trip 1: 8 orders, 1120 kg → ASIF1
```

## Implementation Plan

### Phase 1: Build Pincode-to-Area Mapping

**File: `build_pincode_mapping.py`**

What it does:
1. Read Day 26 user sheet (vy37r1dlj4_UserSheet.txt)
2. Parse vehicle names to extract areas:
   - "ATTAPUR 1" → "ATTAPUR"
   - "GOLCONDA 1" → "GOLCONDA"
3. For each order, get its pincode from database
4. Build mapping: `{pincode: area}`
5. Handle conflicts (pincode appears in multiple areas)
6. Save to `pincode_area_mapping.json`

Output example:
```json
{
  "500048": "ATTAPUR",
  "500049": "ATTAPUR",
  "500008": "GOLCONDA",
  "500028": "ASIF NAGAR",
  ...
}
```

### Phase 2: Update Configuration

**File: `config.py`**

Add:
```python
# Load pincode mapping from JSON file
import json
with open('pincode_area_mapping.json') as f:
    PINCODE_TO_AREA = json.load(f)

# Area code mapping (already exists, keep it)
AREA_CODE_MAPPING = {
    "ATTAPUR": "ATTA",
    "GOLCONDA": "GOLC",
    ...
}
```

Add helper function:
```python
def get_area_from_pincode(pincode):
    """Get area name from pincode"""
    return PINCODE_TO_AREA.get(str(pincode), "UNKNOWN")
```

### Phase 3: Update Order Fetcher

**File: `order_fetcher.py`**

Change how we determine area:

Old way:
```python
area_name = row['area_name']  # Returns "AMt" garbage
```

New way:
```python
# Extract pincode from delivery_info or address
pincode = extract_pincode(delivery_info)
# Use pincode to get real area
area_name = get_area_from_pincode(pincode)
```

Add new function:
```python
def extract_pincode(delivery_info):
    """
    Extract pincode from delivery_info JSON or address string
    Returns pincode as string or None
    """
    # Try to get from JSON field
    if 'pincode' in delivery_info:
        return str(delivery_info['pincode'])
    
    # Try to extract from address using regex
    address = delivery_info.get('address', '')
    match = re.search(r'\b(\d{6})\b', address)
    if match:
        return match.group(1)
    
    return None
```

### Phase 4: Group Orders by Area

**File: `trip_generator.py`**

Add new function:
```python
def group_orders_by_area(orders, order_details):
    """
    Group orders by their area
    
    Returns:
    {
        'ATTAPUR': [order1, order2, ...],
        'GOLCONDA': [order3, order4, ...],
        ...
    }
    """
    area_groups = {}
    
    for order in orders:
        order_id = order['order_id']
        area = order_details[order_id]['area_name']
        
        if area not in area_groups:
            area_groups[area] = []
        
        area_groups[area].append(order)
    
    return area_groups
```

### Phase 5: Run Algorithm Per Area

**File: `trip_generator.py`**

Change the main function:

Old way:
```python
def generate_trips_for_day(orders_data, vehicle_capacity):
    algo_orders = orders_data['algo_orders']
    
    # Run algorithm on ALL orders at once
    algo_result = run_allocation_algorithm(algo_orders, vehicle_capacity)
    
    # Assign names after
    result = assign_trip_names(algo_result, order_details, vehicle_capacity)
    return result
```

New way:
```python
def generate_trips_for_day(orders_data, vehicle_capacity):
    algo_orders = orders_data['algo_orders']
    order_details = orders_data['order_details']
    
    # Group orders by area FIRST
    area_groups = group_orders_by_area(algo_orders, order_details)
    
    all_trips = []
    all_assignments = {}
    trip_counter = 1
    
    # Process each area separately
    for area_name, area_orders in area_groups.items():
        print(f"\n📍 Processing {area_name} ({len(area_orders)} orders)...")
        
        # Run algorithm for THIS AREA ONLY
        algo_result = run_allocation_algorithm(area_orders, vehicle_capacity)
        
        # Get area code (ATTAPUR → ATTA)
        area_code = get_area_code(area_name)
        
        # Number trips for this area
        for idx, trip in enumerate(algo_result['trips'], 1):
            trip_name = f"{area_code}{idx}"
            
            trip_data = {
                'trip_id': trip_counter,
                'trip_name': trip_name,
                'area': area_name,
                'orders': trip['orders'],
                'order_count': len(trip['orders']),
                'total_weight': trip['total_weight'],
                'utilization_percent': round((trip['total_weight'] / vehicle_capacity) * 100, 1)
            }
            
            all_trips.append(trip_data)
            
            # Map orders to trip names
            for order_id in trip['orders']:
                all_assignments[order_id] = trip_name
            
            trip_counter += 1
            print(f"   {trip_name}: {len(trip['orders'])} orders, {trip['total_weight']} kg")
    
    return {
        'trips': all_trips,
        'assignments': all_assignments,
        'order_details': order_details,
        'metrics': calculate_overall_metrics(all_trips, vehicle_capacity)
    }
```

### Phase 6: Calculate Overall Metrics

**File: `trip_generator.py`**

Add function to calculate metrics across all areas:
```python
def calculate_overall_metrics(all_trips, vehicle_capacity):
    """Calculate metrics for all trips combined"""
    total_trips = len(all_trips)
    total_weight = sum(trip['total_weight'] for trip in all_trips)
    max_possible = total_trips * vehicle_capacity
    avg_utilization = (total_weight / max_possible * 100) if max_possible > 0 else 0
    
    return {
        'number_of_trips': total_trips,
        'average_utilization_percent': round(avg_utilization, 2),
        'total_distance_km': 0,  # Can calculate if needed
        'runtime_seconds': 0
    }
```

## The Complete New Flow

```
User runs: python generate_trips.py --day 26
    ↓
[1] Load config (pincode mapping)
    ↓
[2] Fetch orders from database
    ↓
[3] For each order:
    - Extract pincode
    - Look up area from pincode
    - Assign area_name
    ↓
[4] Group orders by area:
    ATTAPUR: 20 orders
    GOLCONDA: 15 orders
    ASIF NAGAR: 12 orders
    BEGUMPET: 18 orders
    ...
    ↓
[5] For each area:
    ↓
    [5a] Run algorithm on area orders only
         ATTAPUR (20 orders) → 2 trips
    ↓
    [5b] Name trips sequentially
         Trip 1 → ATTA1
         Trip 2 → ATTA2
    ↓
    [5c] Move to next area
         GOLCONDA (15 orders) → 2 trips
         Trip 1 → GOLC1
         Trip 2 → GOLC2
    ↓
[6] Combine all area trips
    ↓
[7] Create map (color by area)
    ↓
[8] Export data
    ↓
Done!
```

## Expected Output Changes

### Before (Current System)
```
Trip 1: 8 orders from random areas → AMT1
Trip 2: 9 orders from random areas → AMT2
Trip 3: 7 orders from random areas → AMT3
...
```

### After (New System)
```
ATTAPUR Area:
  ATTA1: 10 orders (all from Attapur)
  ATTA2: 10 orders (all from Attapur)

GOLCONDA Area:
  GOLC1: 10 orders (all from Golconda)
  GOLC2: 5 orders (all from Golconda)

ASIF NAGAR Area:
  ASIF1: 8 orders (all from Asif Nagar)
...
```

## Benefits

1. **Geographic clustering** - Orders in same trip are actually near each other
2. **Meaningful names** - ATTA1 tells you it's Attapur area, trip 1
3. **Matches human logic** - Humans group by area first
4. **Better comparison** - Can compare our ATTA1 vs human ATTA1
5. **Realistic routes** - Drivers don't zigzag across the city

## Testing Plan

### Test 1: Run on Day 26
```bash
python generate_trips.py --day 26
```

Check:
- Are orders grouped by area?
- Do trip names make sense? (ATTA1, GOLC1, etc.)
- Are all orders from ATTA1 actually in Attapur area?

### Test 2: Compare with Human Allocations
Open both maps side by side:
- Human: `human_made_trips_visualization/day_26_trips_map.html`
- Algo: `algo_generated_trips/outputs/day_26/algo_trips_day_26.html`

Check:
- Do we have similar number of trips per area?
- Are the geographic clusters similar?

### Test 3: Check Edge Cases
- Orders with missing pincodes → Should go to "UNKNOWN" area
- Orders with wrong pincodes → Might be in wrong area (acceptable for now)
- Areas with only 1-2 orders → Should still create trips

## Implementation Order

1. **First:** Write `build_pincode_mapping.py` and run it
2. **Second:** Update `config.py` with the mapping
3. **Third:** Update `order_fetcher.py` to use pincodes
4. **Fourth:** Update `trip_generator.py` to group by area
5. **Fifth:** Test on Day 26
6. **Sixth:** Fix any issues
7. **Seventh:** Test on Day 30
8. **Done!**

## Files to Create/Modify

### New Files:
1. `build_pincode_mapping.py` - One-time script to generate mapping
2. `pincode_area_mapping.json` - The mapping data

### Modified Files:
1. `config.py` - Load and expose pincode mapping
2. `order_fetcher.py` - Use pincodes to determine areas
3. `trip_generator.py` - Group by area, run algorithm per area
4. `map_visualizer.py` - Maybe color by area instead of random colors

## What Stays the Same

- Command-line interface (same commands)
- Output formats (HTML, JSON, CSV, text)
- Map visualization (just better organized)
- Data export logic

## Summary

We're changing from "throw all orders at algorithm" to "group by area first, then run algorithm per area". This matches how humans think and makes the output actually comparable to human allocations.

The key insight: Pincodes tell us geography, and geography determines areas. Once we know pincode → area mapping, everything else falls into place.
