import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from sqlalchemy import text
from dotenv import load_dotenv
import json
import folium
import csv

load_dotenv()

# Path to your user sheet file (Day 26)
USER_SHEET_PATH = os.path.join(os.path.dirname(__file__), "vy37r1dlj4_UserSheet.txt")

db = SessionLocal()

try:
    print("=== Reading Day 26 User Sheet ===\n")
    
    # Read order IDs from the user sheet
    order_ids = []
    with open(USER_SHEET_PATH, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        # Skip first line (prepareOrderNotify) and use second line as header
        if len(lines) < 2:
            print("File is too short!")
            exit()
        
        # Find the header line
        header_line = lines[1].strip().split('\t')
        
        # Find OrderId column index
        try:
            order_id_index = header_line.index('OrderId')
        except ValueError:
            print("OrderId column not found in header!")
            print(f"Available columns: {header_line}")
            exit()
        
        # Read data rows (starting from line 3, index 2)
        for line in lines[2:]:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            
            columns = line.split('\t')
            if len(columns) > order_id_index:
                try:
                    order_id = int(columns[order_id_index].strip())
                    order_ids.append(order_id)
                except ValueError:
                    continue
    
    print(f"Found {len(order_ids)} order IDs in Day 26 user sheet\n")
    
    if len(order_ids) == 0:
        print("No valid order IDs found!")
        exit()
    
    # Fetch orders with trip_id from database
    print("=== Fetching Orders from Database ===\n")
    
    order_ids_str = ','.join(map(str, order_ids))
    
    result = db.execute(text(f"""
        SELECT 
            order_id,
            trip_id,
            delivery_info,
            order_total,
            area_name
        FROM `orders` 
        WHERE order_id IN ({order_ids_str})
    """))
    
    orders_by_trip = {}
    all_coords = []
    
    for row in result:
        order_id = row[0]
        trip_id = row[1]
        delivery_info_json = row[2]
        order_total = float(row[3]) if row[3] else 0
        area_name = row[4] or 'Unknown Area'
        
        try:
            delivery_info = json.loads(delivery_info_json)
            
            latitude = delivery_info.get('latitude')
            longitude = delivery_info.get('longitude')
            address = delivery_info.get('address', 'N/A')
            name = delivery_info.get('name', 'N/A')
            contactno = delivery_info.get('contactno', 'N/A')
            
            if not latitude or not longitude:
                print(f"⚠️  Order {order_id} missing coordinates, skipping...")
                continue
            
            lat = float(latitude)
            lon = float(longitude)
            
            if trip_id not in orders_by_trip:
                orders_by_trip[trip_id] = []
            
            orders_by_trip[trip_id].append({
                'order_id': order_id,
                'latitude': lat,
                'longitude': lon,
                'name': name,
                'address': address,
                'contactno': contactno,
                'order_total': order_total,
                'area_name': area_name
            })
            
            all_coords.append([lat, lon])
            
        except Exception as e:
            print(f"⚠️  Error processing order {order_id}: {e}")
            continue
    
    print(f"Loaded {sum(len(orders) for orders in orders_by_trip.values())} orders across {len(orders_by_trip)} trips\n")
    
    if len(all_coords) == 0:
        print("No valid orders with coordinates found!")
        exit()
    
    # Create map centered on average location
    center_lat = sum(coord[0] for coord in all_coords) / len(all_coords)
    center_lon = sum(coord[1] for coord in all_coords) / len(all_coords)
    
    map_obj = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Color palette for different trips
    colors = [
        'red', 'blue', 'green', 'purple', 'orange', 'darkred', 
        'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
        'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 
        'black', 'lightgray', 'crimson', 'indigo', 'teal', 'olive',
        'maroon', 'navy', 'lime', 'cyan', 'magenta', 'gold'
    ]
    
    print("=== Creating Day 26 Map ===\n")
    
    trip_summary = []
    
    # Plot each trip with a different color
    for trip_id, orders in sorted(orders_by_trip.items()):
        color = colors[trip_id % len(colors)] if trip_id else 'gray'
        trip_coords = []
        
        print(f"Trip {trip_id if trip_id else 'Unassigned'}: {len(orders)} orders - Color: {color}")
        
        for order in orders:
            lat = order['latitude']
            lon = order['longitude']
            trip_coords.append([lat, lon])
            
            # Create popup with order details
            popup_html = f"""
            <div style="font-family: Arial; width: 280px;">
                <h4 style="margin: 0; color: {color};">Trip #{trip_id if trip_id else 'Unassigned'}</h4>
                <hr style="margin: 5px 0;">
                <b>Order ID:</b> {order['order_id']}<br>
                <b>Customer:</b> {order['name']}<br>
                <b>Contact:</b> {order['contactno']}<br>
                <b>Area:</b> {order['area_name']}<br>
                <b>Order Total:</b> ₹{order['order_total']:.2f}<br>
                <b>Address:</b> {order['address'][:100]}...<br>
                <b>Coordinates:</b> {lat:.6f}, {lon:.6f}
            </div>
            """
            
            # Add circle marker for each order
            folium.CircleMarker(
                location=[lat, lon],
                radius=10,
                popup=folium.Popup(popup_html, max_width=320),
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                weight=3
            ).add_to(map_obj)
            
            # Add order ID label
            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(html=f'''
                    <div style="font-size: 9px; color: white; background-color: {color}; 
                                padding: 2px 5px; border-radius: 3px; font-weight: bold;
                                border: 1px solid white;">
                        {order['order_id']}
                    </div>
                ''')
            ).add_to(map_obj)
        
        # Draw route line connecting orders in the same trip
        if len(trip_coords) > 1:
            folium.PolyLine(
                locations=trip_coords,
                color=color,
                weight=4,
                opacity=0.8,
                popup=f"Trip #{trip_id if trip_id else 'Unassigned'} - {len(orders)} orders"
            ).add_to(map_obj)
        
        trip_summary.append({
            'trip_id': trip_id,
            'order_count': len(orders),
            'color': color,
            'total_amount': sum(o['order_total'] for o in orders)
        })
    
    # Add legend
    legend_items = ''.join([
        f'<div style="margin: 3px 0;"><span style="display: inline-block; width: 15px; height: 15px; background-color: {trip["color"]}; border: 1px solid #333; margin-right: 5px;"></span>Trip {trip["trip_id"] if trip["trip_id"] else "Unassigned"} ({trip["order_count"]} orders, ₹{trip["total_amount"]:.2f})</div>'
        for trip in trip_summary
    ])
    
    legend_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 300px; max-height: 80vh; overflow-y: auto;
                background-color: white; z-index:9999; font-size:13px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
        <h4 style="margin-top:0;">Day 26 Trip Summary</h4>
        <p><b>Total Trips:</b> {len(orders_by_trip)}</p>
        <p><b>Total Orders:</b> {sum(len(orders) for orders in orders_by_trip.values())}</p>
        <p><b>Total Amount:</b> ₹{sum(trip["total_amount"] for trip in trip_summary):.2f}</p>
        <hr>
        <div style="font-size: 11px;">
            <b>Trip Legend:</b><br>
            {legend_items}
        </div>
    </div>
    '''
    map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    map_filename = 'day_26_trips_map.html'
    map_obj.save(map_filename)
    
    print(f"\n{'='*80}")
    print(f"✅ Map saved as '{map_filename}'")
    print(f"{'='*80}\n")
    
    print("Day 26 Trip Details:")
    print("="*80)
    for trip in trip_summary:
        print(f"Trip {trip['trip_id'] if trip['trip_id'] else 'Unassigned'}: {trip['order_count']} orders | ₹{trip['total_amount']:.2f} | Color: {trip['color']}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
