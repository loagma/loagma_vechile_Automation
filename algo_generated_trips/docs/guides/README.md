# Algorithm-Generated Trips

This module generates trip allocations using the allocation algorithm for historical days (Dec 26th and 30th) where human-made allocations already exist. This allows for manual comparison between algorithm performance and human decision-making.

## Purpose

- Fetch orders from specific historical days
- Run the allocation algorithm on those orders
- Generate trip names based on dominant areas (e.g., "ATTA1", "GOLC2")
- Visualize trips on interactive maps
- Export data in multiple formats for analysis

## Files

- `config.py` - Day configurations and area name mappings
- `order_fetcher.py` - Fetches orders from database for specific days
- `trip_generator.py` - Runs allocation algorithm and assigns trip names
- `map_visualizer.py` - Creates interactive HTML maps
- `data_exporter.py` - Exports data to JSON, CSV, and text formats
- `generate_trips.py` - Main script to orchestrate the process

## Usage

### Basic Usage

From the `loagma_VA` directory:

```bash
# Generate trips for Day 26
python algo_generated_trips/generate_trips.py --day 26

# Generate trips for Day 30
python algo_generated_trips/generate_trips.py --day 30

# Generate for both days
python algo_generated_trips/generate_trips.py --day all
```

### Advanced Usage

```bash
# Use custom vehicle capacity
python algo_generated_trips/generate_trips.py --day 26 --capacity 2000

# Get help
python algo_generated_trips/generate_trips.py --help
```

## Output Files

All outputs are saved in the `outputs/` directory, organized by day:

### Day 26 Outputs (`outputs/day_26/`)
- `algo_trips_day_26.html` - Interactive map visualization
- `algo_trips_day_26.json` - Structured trip data
- `algo_trips_day_26.csv` - Spreadsheet-friendly format
- `algo_trips_day_26_summary.txt` - Human-readable summary

### Day 30 Outputs (`outputs/day_30/`)
- `algo_trips_day_30.html` - Interactive map visualization
- `algo_trips_day_30.json` - Structured trip data
- `algo_trips_day_30.csv` - Spreadsheet-friendly format
- `algo_trips_day_30_summary.txt` - Human-readable summary

## Trip Naming Convention

Trips are named based on the dominant area (area with most orders in the trip):

- **ATTAPUR** → ATTA1, ATTA2, ATTA3, ...
- **GOLCONDA** → GOLC1, GOLC2, ...
- **BEGUMPET** → BEGU1, BEGU2, ...
- **NARSINGI** → NARS1, NARS2, ...
- And so on...

The number increments sequentially for each area.

## Workflow

1. **Read Order IDs**: Extracts order IDs from user sheet files
2. **Fetch Details**: Queries database for complete order information
3. **Run Algorithm**: Executes AllocationEngine to generate trips
4. **Assign Names**: Determines dominant area and assigns trip names
5. **Visualize**: Creates interactive map with color-coded trips
6. **Export**: Saves data in JSON, CSV, and text formats

## Manual Comparison Process

After generating algorithm trips, you can compare them with human allocations:

1. Open algorithm map: `outputs/day_26/algo_trips_day_26.html`
2. Open human map: `../human_made_trips_visualization/day_26_trips_map.html`
3. Compare side-by-side:
   - Number of trips
   - Orders per trip
   - Geographic clustering
   - Vehicle utilization
   - Trip efficiency
4. Review CSV/JSON for detailed analysis
5. Identify areas for algorithm improvement
6. Adjust algorithm parameters and re-run

## Configuration

### Adding New Days

Edit `config.py` to add new days:

```python
DAY_CONFIGS = {
    "26": {...},
    "30": {...},
    "31": {  # New day
        "user_sheet": "../path/to/usersheet.txt",
        "date": "2024-12-31",
        "vehicle_capacity": 1500.0,
        "description": "December 31st orders"
    }
}
```

### Adding New Areas

Edit `config.py` to add area code mappings:

```python
AREA_CODE_MAPPING = {
    "ATTAPUR": "ATTA",
    "NEW_AREA": "NEWA",  # Add new area
    ...
}
```

## Map Features

The generated maps include:

- **Color-coded trips**: Each trip has a unique color
- **Order markers**: Clickable markers showing order details
- **Trip labels**: Trip names displayed on markers
- **Route lines**: Lines connecting orders in the same trip
- **Interactive popups**: Click markers to see full order details
- **Legend**: Summary of all trips with statistics

## Data Formats

### JSON Format
Structured data with trips, assignments, and metrics. Useful for programmatic analysis.

### CSV Format
Flat format with one row per order. Easy to import into Excel or other tools.

### Text Summary
Human-readable summary with trip statistics and order lists.

## Dependencies

- `database.py` - Database connection (from parent directory)
- `alleocation.py` - AllocationEngine algorithm (from parent directory)
- `folium` - Map visualization library
- `sqlalchemy` - Database queries

## Troubleshooting

### "User sheet not found"
- Ensure user sheet files exist in `../human_made_trips_visualization/`
- Check file paths in `config.py`

### "No orders found"
- Verify database connection in `.env` file
- Check that order IDs in user sheet exist in database

### "Missing coordinates"
- Some orders may not have latitude/longitude in delivery_info
- These orders are skipped with a warning message

## Future Enhancements

- Add distance calculations for trips
- Include cost estimates
- Support for different algorithm variations
- Batch processing with parameter tuning
- Automated comparison metrics
