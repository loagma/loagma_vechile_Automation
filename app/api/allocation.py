"""
Allocation API endpoints with map visualization
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
import pymysql
import json
import random

from app.allocation.allocation_engine import AllocationEngine
from app.config.settings import settings

router = APIRouter(prefix="/api/allocation", tags=["allocation"])


class OrderInput(BaseModel):
    order_id: int
    latitude: float
    longitude: float
    pincode: str
    total_weight_kg: float


class AllocationRequest(BaseModel):
    orders: Optional[List[OrderInput]] = None
    vehicle_capacity_kg: float = 100.0
    fetch_from_db: bool = True
    days: int = 60


@router.post("/allocate")
async def allocate_orders(request: AllocationRequest):
    """
    Allocate orders to delivery trips.
    
    - If fetch_from_db=True: Fetches real orders from database
    - If fetch_from_db=False: Uses provided orders list
    """
    try:
        if request.fetch_from_db:
            # Fetch from database
            orders = fetch_orders_from_db(limit=1000, days=request.days)
            if not orders:
                raise HTTPException(status_code=404, detail="No orders found in database")
        else:
            # Use provided orders
            if not request.orders:
                raise HTTPException(status_code=400, detail="No orders provided")
            orders = [order.dict() for order in request.orders]
        
        # Run allocation
        engine = AllocationEngine(vehicle_capacity_kg=request.vehicle_capacity_kg)
        result = engine.run(orders)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/map", response_class=HTMLResponse)
async def show_allocation_map(
    vehicle_capacity: float = 100.0,
    days: int = 60,
    limit: int = 500
):
    """
    Display allocation results on an interactive map.
    
    Query parameters:
    - vehicle_capacity: Vehicle capacity in kg (default: 100)
    - days: Number of days to look back (default: 60)
    - limit: Maximum number of orders (default: 500)
    """
    try:
        # Fetch orders
        orders = fetch_orders_from_db(limit=limit, days=days)
        
        if not orders:
            return "<html><body><h1>No orders found</h1></body></html>"
        
        # Run allocation
        engine = AllocationEngine(vehicle_capacity_kg=vehicle_capacity)
        result = engine.run(orders)
        
        # Generate HTML with map
        html = generate_map_html(result, orders, vehicle_capacity)
        
        return html
        
    except Exception as e:
        return f"<html><body><h1>Error: {str(e)}</h1></body></html>"


def fetch_orders_from_db(limit: int = 500, days: int = 60) -> List[dict]:
    """Fetch orders from database."""
    import time
    
    conn = pymysql.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        ssl={'ssl': True}
    )
    
    cursor = conn.cursor()
    
    days_ago_timestamp = int(time.time()) - (days * 24 * 60 * 60)
    
    query = """
        SELECT 
            order_id,
            delivery_info,
            area_name,
            start_time
        FROM orders
        WHERE delivery_info IS NOT NULL
        AND delivery_info != ''
        AND start_time >= %s
        ORDER BY start_time DESC
        LIMIT %s
    """
    
    cursor.execute(query, (days_ago_timestamp, limit))
    rows = cursor.fetchall()
    
    orders = []
    for row in rows:
        try:
            info = json.loads(row[1])
            latitude = info.get('latitude')
            longitude = info.get('longitude')
            
            if latitude and longitude:
                orders.append({
                    'order_id': row[0],
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'pincode': row[2][:6] if row[2] else '500001',
                    'total_weight_kg': round(random.uniform(1.0, 50.0), 2)
                })
        except:
            continue
    
    conn.close()
    return orders


def generate_map_html(result: dict, orders: List[dict], vehicle_capacity: float) -> str:
    """Generate HTML with Leaflet map showing allocation results."""
    
    # Create order lookup
    order_lookup = {o['order_id']: o for o in orders}
    
    # Generate colors for trips
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
        '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B739', '#52B788',
        '#E63946', '#A8DADC', '#457B9D', '#F1FAEE', '#E76F51'
    ]
    
    # Prepare trip data for JavaScript
    trips_data = []
    for trip in result['trips']:
        color = colors[trip['trip_id'] % len(colors)]
        trip_orders = []
        
        for order_id in trip['orders']:
            if order_id in order_lookup:
                order = order_lookup[order_id]
                trip_orders.append({
                    'order_id': order_id,
                    'lat': order['latitude'],
                    'lng': order['longitude'],
                    'pincode': order['pincode'],
                    'weight': order['total_weight_kg']
                })
        
        if trip_orders:
            trips_data.append({
                'trip_id': trip['trip_id'],
                'orders': trip_orders,
                'total_weight': trip['total_weight'],
                'distance': trip['route_distance_km'],
                'color': color
            })
    
    # Calculate center of map
    all_lats = [o['latitude'] for o in orders]
    all_lngs = [o['longitude'] for o in orders]
    center_lat = sum(all_lats) / len(all_lats)
    center_lng = sum(all_lngs) / len(all_lngs)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Delivery Trip Allocation Map</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
            }}
            #map {{
                position: absolute;
                top: 0;
                bottom: 0;
                width: 100%;
            }}
            .info-panel {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                z-index: 1000;
                max-width: 300px;
            }}
            .info-panel h3 {{
                margin: 0 0 10px 0;
                font-size: 18px;
            }}
            .stat {{
                margin: 5px 0;
                font-size: 14px;
            }}
            .stat strong {{
                color: #333;
            }}
            .legend {{
                position: absolute;
                bottom: 30px;
                right: 10px;
                background: white;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                z-index: 1000;
                max-height: 400px;
                overflow-y: auto;
            }}
            .legend h4 {{
                margin: 0 0 10px 0;
                font-size: 14px;
            }}
            .legend-item {{
                margin: 5px 0;
                font-size: 12px;
                display: flex;
                align-items: center;
            }}
            .legend-color {{
                width: 20px;
                height: 20px;
                border-radius: 50%;
                margin-right: 8px;
                border: 2px solid #333;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        
        <div class="info-panel">
            <h3>📊 Allocation Summary</h3>
            <div class="stat"><strong>Total Orders:</strong> {len(orders)}</div>
            <div class="stat"><strong>Total Trips:</strong> {result['metrics']['number_of_trips']}</div>
            <div class="stat"><strong>Vehicle Capacity:</strong> {vehicle_capacity} kg</div>
            <div class="stat"><strong>Avg Utilization:</strong> {result['metrics']['average_utilization_percent']}%</div>
            <div class="stat"><strong>Total Distance:</strong> {result['metrics']['total_distance_km']:.2f} km</div>
            <div class="stat"><strong>Runtime:</strong> {result['metrics']['runtime_seconds']:.3f}s</div>
        </div>
        
        <div class="legend">
            <h4>🚚 Trips (showing first 15)</h4>
            {generate_legend_html(trips_data[:15], vehicle_capacity)}
        </div>
        
        <script>
            // Initialize map
            var map = L.map('map').setView([{center_lat}, {center_lng}], 12);
            
            // Add OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }}).addTo(map);
            
            // Trip data
            var trips = {json.dumps(trips_data)};
            
            // Add trips to map
            trips.forEach(function(trip) {{
                var coordinates = trip.orders.map(o => [o.lat, o.lng]);
                
                // Draw polyline for trip route
                var polyline = L.polyline(coordinates, {{
                    color: trip.color,
                    weight: 3,
                    opacity: 0.7
                }}).addTo(map);
                
                // Add markers for each order
                trip.orders.forEach(function(order, index) {{
                    var marker = L.circleMarker([order.lat, order.lng], {{
                        radius: 8,
                        fillColor: trip.color,
                        color: '#fff',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.8
                    }}).addTo(map);
                    
                    // Popup with order details
                    marker.bindPopup(`
                        <b>Trip ${{trip.trip_id}} - Order ${{index + 1}}</b><br>
                        Order ID: ${{order.order_id}}<br>
                        Pincode: ${{order.pincode}}<br>
                        Weight: ${{order.weight}} kg<br>
                        <hr>
                        <b>Trip Total:</b> ${{trip.total_weight}} kg<br>
                        <b>Distance:</b> ${{trip.distance.toFixed(2)}} km
                    `);
                }});
                
                // Add trip label at first order
                if (trip.orders.length > 0) {{
                    var firstOrder = trip.orders[0];
                    L.marker([firstOrder.lat, firstOrder.lng], {{
                        icon: L.divIcon({{
                            className: 'trip-label',
                            html: `<div style="background: ${{trip.color}}; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 12px;">T${{trip.trip_id}}</div>`,
                            iconSize: [30, 20]
                        }})
                    }}).addTo(map);
                }}
            }});
            
            // Fit map to show all markers
            if (trips.length > 0) {{
                var allCoords = trips.flatMap(t => t.orders.map(o => [o.lat, o.lng]));
                map.fitBounds(allCoords);
            }}
        </script>
    </body>
    </html>
    """
    
    return html


def generate_legend_html(trips: List[dict], vehicle_capacity: float) -> str:
    """Generate HTML for trip legend."""
    html = ""
    for trip in trips:
        utilization = (trip['total_weight'] / vehicle_capacity) * 100
        html += f"""
        <div class="legend-item">
            <div class="legend-color" style="background-color: {trip['color']};"></div>
            <div>
                <strong>Trip {trip['trip_id']}</strong>: {len(trip['orders'])} orders, 
                {trip['total_weight']:.1f}kg ({utilization:.0f}%)
            </div>
        </div>
        """
    return html
