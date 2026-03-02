# Problem: Area Names in Database are Useless

## The Issue

Right now we're trying to use `area_name` from the database to name our trips (like ATTA1, GOLC1, etc.). But there's a problem - the database has garbage data. Every order just says "AMt" or some other dummy value in the area_name field. So our trip names end up being meaningless.

We need actual area names based on geography. The human-made trips from Dec 26th already have this figured out - they assigned orders to vehicles like "ATTAPUR 1", "GOLCONDA 1", etc. Those humans knew which pincodes belong to which areas.

## What We Need to Do

We need to reverse-engineer the area-to-pincode mapping from the human allocations. Here's the logic:

1. The human trip file (vy37r1dlj4_UserSheet.txt) shows which orders went to which vehicle
2. Each vehicle name represents an area (ATTAPUR 1, GOLCONDA 1, etc.)
3. Each order has a pincode in the database
4. So we can figure out: "These pincodes = ATTAPUR, those pincodes = GOLCONDA"

Once we have that mapping, we can use pincodes to determine areas instead of relying on the broken area_name field.

## The Fix - Step by Step

### Step 1: Extract Human Trip Assignments

Read the Day 26 user sheet and build a map:
- Order 244541 → ATTAPUR 1
- Order 244538 → ATTAPUR 1
- Order 244524 → GOLCONDA 1
- etc.

Parse the vehicle name to get the area:
- "ATTAPUR 1" → area = "ATTAPUR"
- "GOLCONDA 1" → area = "GOLCONDA"

### Step 2: Get Pincodes for Each Order

Query the database for all orders in the user sheet:
```sql
SELECT order_id, delivery_info 
FROM orders 
WHERE order_id IN (244541, 244538, ...)
```

Parse the delivery_info JSON to extract pincodes. Some orders might have pincode in the JSON, others might have it in the address string. We'll need to handle both.

### Step 3: Build Pincode → Area Mapping

Group orders by their human-assigned area, then collect all pincodes for that area:

```
ATTAPUR orders: 244541, 244538, 244587, ...
  → Pincodes: 500048, 500048, 500048, ...
  
GOLCONDA orders: 244524, 244527, 244489, ...
  → Pincodes: 500008, 500008, 500008, ...
```

Create a mapping:
```
500048 → ATTAPUR
500008 → GOLCONDA
500028 → ASIF NAGAR
...
```

### Step 4: Handle Edge Cases

Some pincodes might appear in multiple areas (border cases). For these:
- Count which area has more orders with that pincode
- Assign to the dominant area
- Log conflicts for manual review

Some orders might not have pincodes at all:
- Try to extract from address string using regex
- If still missing, mark as "UNKNOWN" area

### Step 5: Save the Mapping

Create a new config file or update existing config.py:

```python
PINCODE_TO_AREA = {
    "500048": "ATTAPUR",
    "500008": "GOLCONDA",
    "500028": "ASIF NAGAR",
    ...
}

AREA_TO_CODE = {
    "ATTAPUR": "ATTA",
    "GOLCONDA": "GOLC",
    "ASIF NAGAR": "ASIF",
    ...
}
```

### Step 6: Update order_fetcher.py

Change the logic from:
```python
area_name = row['area_name']  # This gives us "AMt" garbage
```

To:
```python
pincode = extract_pincode_from_order(row)
area_name = PINCODE_TO_AREA.get(pincode, "UNKNOWN")
```

### Step 7: Test It

Run the script again for Day 26:
```bash
python algo_generated_trips/generate_trips.py --day 26
```

Check if trip names now make sense:
- ATTA1, ATTA2 (Attapur trips)
- GOLC1, GOLC2 (Golconda trips)
- etc.

Compare with human allocations to see if we're grouping orders from the same geographic areas.

## Implementation Plan

### File 1: `build_pincode_mapping.py`
A one-time script to analyze Day 26 data and generate the mapping.

What it does:
1. Read vy37r1dlj4_UserSheet.txt
2. Parse vehicle names to get areas
3. Query database for pincodes
4. Build pincode → area dictionary
5. Handle conflicts and missing data
6. Output mapping to a JSON file or update config.py

### File 2: Update `config.py`
Add the pincode mapping dictionary.

### File 3: Update `order_fetcher.py`
Change area detection logic to use pincodes instead of area_name field.

Add helper function:
```python
def get_area_from_pincode(pincode):
    return PINCODE_TO_AREA.get(pincode, "UNKNOWN")
```

## Expected Results

Before fix:
- All trips named "AMT1", "AMT2", "AMT3" (useless)

After fix:
- Trips named "ATTA1", "GOLC1", "ASIF1" (meaningful)
- Geographic clustering makes sense
- Can actually compare with human allocations

## Why This Works

The humans who made the original allocations knew the geography. They assigned orders to vehicles based on areas. By reverse-engineering their decisions, we're essentially learning the pincode-to-area mapping from their domain knowledge.

Once we have that mapping, our algorithm can use the same geographic logic.

## Potential Issues

1. **Pincodes might be missing** - We'll need good fallback logic
2. **Pincodes might be wrong** - Database data quality issues
3. **Border areas** - Some pincodes might legitimately belong to multiple areas
4. **New pincodes** - Day 30 might have pincodes not in Day 26 data

For issues 3 and 4, we might need to manually review and update the mapping after initial generation.

## Next Steps

1. Write `build_pincode_mapping.py` script
2. Run it on Day 26 data
3. Review the generated mapping
4. Manually fix any obvious errors
5. Update config.py with the mapping
6. Update order_fetcher.py to use pincodes
7. Test on both Day 26 and Day 30
8. Iterate if needed
