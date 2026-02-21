# Map Visualization Guide

## Overview

The allocation system now includes an interactive map visualization that shows delivery trips with color-coded routes and markers.

## Features

✅ **Interactive Map** - Pan, zoom, and click on markers  
✅ **Color-Coded Trips** - Each trip has a unique color  
✅ **Route Lines** - Visual routes connecting orders in each trip  
✅ **Order Details** - Click markers to see order information  
✅ **Real-time Stats** - Summary panel with allocation metrics  
✅ **Trip Legend** - List of all trips with utilization  

## Access the Map

### Option 1: Web Browser

1. **Start the server** (if not running):
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. **Open in browser**:
   ```
   http://localhost:8000/api/allocation/map
   ```

### Option 2: With Parameters

Customize the visualization with query parameters:

```
http://localhost:8000/api/allocation/map?vehicle_capacity=150&days=60&limit=500
```

**Parameters:**
- `vehicle_capacity` - Vehicle capacity in kg (default: 100)
- `days` - Number of days to look back (default: 60)
- `limit` - Maximum number of orders (default: 500)

**Examples:**
```
# 200kg vehicles, last 30 days, max 1000 orders
http://localhost:8000/api/allocation/map?vehicle_capacity=200&days=30&limit=1000

# 150kg vehicles, last 7 days, max 200 orders
http://localhost:8000/api/allocation/map?vehicle_capacity=150&days=7&limit=200
```

## API Endpoints

### 1. Get Allocation Map (HTML)
```
GET /api/allocation/map
```

Returns interactive HTML map with allocation visualization.

### 2. Get Allocation Data (JSON)
```
POST /api/allocation/allocate
```

**Request Body:**
```json
{
  "vehicle_capacity_kg": 100,
  "fetch_from_db": true,
  "days": 60
}
```

**Response:**
```json
{
  "trips": [
    {
      "trip_id": 1,
      "orders": [123, 456, 789],
      "total_weight": 85.5,
      "route_distance_km": 12.34
    }
  ],
  "unallocatable_orders": [],
  "metrics": {
    "number_of_trips": 299,
    "average_utilization_percent": 83.4,
    "total_distance_km": 648.79,
    "runtime_seconds": 2.432
  }
}
```

## Map Features

### Visual Elements

1. **Colored Markers** - Each order is a circle marker
   - Color matches the trip it belongs to
   - Click to see order details

2. **Route Lines** - Polylines connecting orders
   - Shows the delivery sequence
   - Color-coded by trip

3. **Trip Labels** - "T1", "T2", etc.
   - Positioned at the first order of each trip
   - Easy trip identification

4. **Info Panel** (Top Right)
   - Total orders
   - Number of trips
   - Vehicle capacity
   - Average utilization
   - Total distance
   - Runtime

5. **Trip Legend** (Bottom Right)
   - List of trips with colors
   - Order count per trip
   - Weight and utilization

### Interactions

- **Pan** - Click and drag to move the map
- **Zoom** - Scroll wheel or +/- buttons
- **Click Marker** - View order details in popup
- **Auto-fit** - Map automatically fits all markers

## Use Cases

### 1. Daily Operations Review
```
http://localhost:8000/api/allocation/map?days=1
```
View today's orders and how they're allocated.

### 2. Capacity Planning
```
http://localhost:8000/api/allocation/map?vehicle_capacity=200
```
See how different vehicle sizes affect trip count.

### 3. Route Optimization
Click on trips to see the delivery sequence and identify optimization opportunities.

### 4. Performance Analysis
Compare utilization rates across different time periods and capacities.

## Integration Examples

### Embed in Dashboard

```html
<iframe 
  src="http://localhost:8000/api/allocation/map?vehicle_capacity=100" 
  width="100%" 
  height="600px"
  frameborder="0">
</iframe>
```

### Fetch Data for Custom Visualization

```javascript
// Fetch allocation data
fetch('http://localhost:8000/api/allocation/allocate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    vehicle_capacity_kg: 100,
    fetch_from_db: true,
    days: 60
  })
})
.then(response => response.json())
.then(data => {
  console.log('Trips:', data.trips);
  console.log('Metrics:', data.metrics);
  // Use data for custom visualization
});
```

### Python Integration

```python
import requests

# Get allocation data
response = requests.post('http://localhost:8000/api/allocation/allocate', json={
    'vehicle_capacity_kg': 100,
    'fetch_from_db': True,
    'days': 60
})

result = response.json()
print(f"Generated {result['metrics']['number_of_trips']} trips")
print(f"Utilization: {result['metrics']['average_utilization_percent']}%")
```

## Customization

### Change Map Style

Edit `app/api/allocation.py` and modify the tile layer:

```javascript
// Current: OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {...})

// Alternative: CartoDB
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {...})

// Alternative: Satellite
L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {...})
```

### Adjust Colors

Modify the `colors` array in `generate_map_html()`:

```python
colors = [
    '#FF6B6B',  # Red
    '#4ECDC4',  # Teal
    '#45B7D1',  # Blue
    # Add more colors...
]
```

### Change Marker Style

Edit the `circleMarker` options:

```javascript
var marker = L.circleMarker([order.lat, order.lng], {
    radius: 10,        // Larger markers
    fillColor: trip.color,
    color: '#000',     // Black border
    weight: 3,         // Thicker border
    opacity: 1,
    fillOpacity: 0.9   // More opaque
})
```

## Troubleshooting

### Map Not Loading

1. **Check server is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check browser console** for JavaScript errors

3. **Verify database connection**:
   ```bash
   python check_db_config.py
   ```

### No Orders Showing

1. **Check date range** - Increase `days` parameter
2. **Check order count** - Increase `limit` parameter
3. **Verify orders have coordinates** in database

### Slow Performance

1. **Reduce order limit**:
   ```
   ?limit=100
   ```

2. **Reduce date range**:
   ```
   ?days=7
   ```

3. **Use smaller vehicle capacity** (fewer trips):
   ```
   ?vehicle_capacity=300
   ```

## Screenshots

### Main Map View
- Interactive map with color-coded trips
- Info panel with metrics
- Trip legend

### Order Popup
- Order ID and details
- Trip information
- Weight and distance

### Legend
- All trips listed
- Color indicators
- Utilization percentages

## Next Steps

1. **Add Real-time Updates** - WebSocket for live tracking
2. **Driver Assignment** - Show which driver is assigned to each trip
3. **Route Optimization** - Integrate Google Maps Directions API
4. **Historical Comparison** - Compare different allocation runs
5. **Export Features** - Download map as image or PDF

## Support

For issues or questions:
1. Check server logs: `docker-compose logs` or process output
2. Verify API is accessible: `curl http://localhost:8000/docs`
3. Test allocation endpoint: `curl -X POST http://localhost:8000/api/allocation/allocate`

---

**Version**: 1.0  
**Last Updated**: 2026-02-21  
**Status**: Production Ready  
**Map Library**: Leaflet.js (Open Source)
