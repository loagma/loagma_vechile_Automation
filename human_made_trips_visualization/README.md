# Human Made Trips Visualization

This folder contains scripts to visualize trip data from user sheets.

## Files

- `day_26_orders.py` - Visualizes trips from Day 26 (vy37r1dlj4_UserSheet.txt)
- `day_30_orders.py` - Visualizes trips from Day 30 (yocm27jhm8_UserSheet.txt)
- `vy37r1dlj4_UserSheet.txt` - Day 26 order data
- `yocm27jhm8_UserSheet.txt` - Day 30 order data

## How to Run

From the `loagma_VA` directory:

```bash
# For Day 26 visualization
python human_made_trips_visualization/day_26_orders.py

# For Day 30 visualization
python human_made_trips_visualization/day_30_orders.py
```

## Output

Each script generates an HTML map file:
- `day_26_trips_map.html` - Interactive map for Day 26 trips
- `day_30_trips_map.html` - Interactive map for Day 30 trips

## Features

- Each trip is shown in a different color
- Click markers to see order details (customer, contact, address, amount)
- Route lines connect orders in the same trip
- Legend shows trip summary with order counts and total amounts
- Uses accurate latitude/longitude coordinates from database
