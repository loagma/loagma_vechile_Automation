# Quick Start Guide

## Installation

No additional installation needed. The module uses existing dependencies from the main project.

## Running the Script

### Step 1: Navigate to the project directory

```bash
cd C:\Users\ishan\Downloads\LOAGMA\VA\loagma_VA
```

### Step 2: Activate virtual environment (if using one)

```bash
venv\Scripts\activate
```

### Step 3: Run the script

```bash
# For Day 26
python algo_generated_trips\generate_trips.py --day 26

# For Day 30
python algo_generated_trips\generate_trips.py --day 30

# For both days
python algo_generated_trips\generate_trips.py --day all
```

## Expected Output

The script will:

1. ✅ Read order IDs from user sheet
2. ✅ Fetch order details from database
3. ✅ Run allocation algorithm
4. ✅ Assign trip names based on areas
5. ✅ Generate interactive map
6. ✅ Export data to JSON, CSV, and text formats

### Console Output Example

```
======================================================================
  ALGORITHM-BASED TRIP GENERATION
  Generate trips using allocation algorithm for historical days
======================================================================

🗓️  Processing Day 26 (December 26th orders)
   Vehicle Capacity: 1500 kg

📋 Reading order IDs from: ../human_made_trips_visualization/vy37r1dlj4_UserSheet.txt
✅ Read 123 order IDs from user sheet

🔍 Fetching order details from database...
✅ Fetched 123 orders from database

⚙️  Preparing orders for algorithm...

🚚 Running allocation algorithm...
   Vehicle capacity: 1500 kg
   Total orders: 123
✅ Algorithm completed!
   Generated 15 trips
   Average utilization: 87.3%

🏷️  Assigning trip names based on areas...
   ATTA1 (ATTAPUR): 12 orders, 1450.5 kg
   GOLC1 (GOLCONDA): 10 orders, 1380.2 kg
   ASIF1 (ASIF NAGAR): 8 orders, 1120.8 kg
   ...

======================================================================
  TRIP GENERATION SUMMARY - DAY 26
======================================================================

📊 Overall Statistics:
   Total Orders: 123
   Total Trips: 15
   Average Orders/Trip: 8.2
   Average Utilization: 87.3%
   Total Distance: 45.6 km

🚚 Trip Breakdown:
   Trip Name    Area            Orders   Weight       Util%   
   ------------------------------------------------------------
   ATTA1        ATTAPUR         12       1450.5       96.7    
   GOLC1        GOLCONDA        10       1380.2       92.0    
   ...

======================================================================

🗺️  Creating interactive map...
✅ Map saved: outputs/day_26/algo_trips_day_26.html

💾 Exporting data in multiple formats...
✅ JSON saved: outputs/day_26/algo_trips_day_26.json
✅ CSV saved: outputs/day_26/algo_trips_day_26.csv
✅ Summary saved: outputs/day_26/algo_trips_day_26_summary.txt

✅ Day 26 processing complete!

📁 Output files:
   Map: outputs/day_26/algo_trips_day_26.html
   JSON: outputs/day_26/algo_trips_day_26.json
   CSV: outputs/day_26/algo_trips_day_26.csv
   Summary: outputs/day_26/algo_trips_day_26_summary.txt
```

## Viewing Results

### Interactive Map

Open the HTML file in your browser:

```bash
# Windows
start algo_generated_trips\outputs\day_26\algo_trips_day_26.html

# Or just double-click the file in File Explorer
```

The map shows:
- Each trip in a different color
- Order markers with trip names
- Route lines connecting orders
- Interactive popups with order details
- Legend with trip statistics

### CSV Data

Open in Excel or any spreadsheet application:

```bash
start algo_generated_trips\outputs\day_26\algo_trips_day_26.csv
```

### JSON Data

View in any text editor or JSON viewer:

```bash
notepad algo_generated_trips\outputs\day_26\algo_trips_day_26.json
```

### Text Summary

View in any text editor:

```bash
notepad algo_generated_trips\outputs\day_26\algo_trips_day_26_summary.txt
```

## Comparing with Human Allocations

1. Open algorithm map: `algo_generated_trips/outputs/day_26/algo_trips_day_26.html`
2. Open human map: `human_made_trips_visualization/day_26_trips_map.html`
3. Place browser windows side-by-side
4. Compare:
   - Number of trips
   - Geographic clustering
   - Orders per trip
   - Vehicle utilization

## Customizing Vehicle Capacity

```bash
# Use 2000 kg capacity instead of default 1500 kg
python algo_generated_trips\generate_trips.py --day 26 --capacity 2000
```

## Troubleshooting

### Error: "User sheet not found"

**Solution**: Ensure the user sheet files exist in the correct location:
- `human_made_trips_visualization/vy37r1dlj4_UserSheet.txt` (Day 26)
- `human_made_trips_visualization/yocm27jhm8_UserSheet.txt` (Day 30)

### Error: "No orders found"

**Solution**: 
1. Check database connection in `.env` file
2. Verify order IDs exist in the database
3. Ensure database is accessible

### Error: "Module not found"

**Solution**: Make sure you're running from the `loagma_VA` directory, not from inside `algo_generated_trips`

### Warning: "Order missing coordinates"

**Info**: Some orders don't have latitude/longitude in the database. These are automatically skipped.

## Tips

- Run for both days to see consistency across different datasets
- Try different vehicle capacities to see impact on trip count
- Export CSV for detailed analysis in Excel
- Use JSON for programmatic analysis or further processing
- Keep the HTML maps for visual presentations

## Next Steps

After generating algorithm trips:

1. Review the maps and data
2. Compare with human allocations
3. Identify patterns and differences
4. Note areas where algorithm performs well/poorly
5. Adjust algorithm parameters if needed
6. Re-run and compare improvements
