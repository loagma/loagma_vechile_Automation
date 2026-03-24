"""
Map visualizer module - Creates interactive maps for algorithm-generated trips
"""

import folium
from folium import plugins

def generate_color_palette(num_trips: int) -> list:
    """
    Generate distinct colors for trips
    
    Args:
        num_trips: Number of trips to generate colors for
    
    Returns:
        List of color names
    """
    colors = [
        'red', 'blue', 'green', 'purple', 'orange', 'darkred', 
        'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
        'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 
        'black', 'lightgray', 'crimson', 'indigo', 'teal', 'olive',
        'maroon', 'navy', 'lime', 'cyan', 'magenta', 'gold'
    ]
    
    # Repeat colors if we have more trips than colors
    while len(colors) < num_trips:
        colors.extend(colors)
    
    return colors[:num_trips]

def create_order_popup(order: dict, trip_name: str, color: str) -> str:
    """
    Generate HTML popup content for order marker
    
    Args:
        order: Order details dictionary
        trip_name: Name of the trip (e.g., "ATTA1")
        color: Color of the trip
    
    Returns:
        HTML string for popup
    """
    popup_html = f"""
    <div style="font-family: Arial; width: 280px;">
        <h4 style="margin: 0; color: {color};">Trip: {trip_name}</h4>
        <hr style="margin: 5px 0;">
        <b>Order ID:</b> {order['order_id']}<br>
        <b>Customer:</b> {order['name']}<br>
        <b>Contact:</b> {order['contactno']}<br>
        <b>Zone:</b> {order.get('zone_name', 'N/A')}<br>
        <b>Pincode:</b> {order.get('pincode', 'N/A')}<br>
        <b>Weight:</b> {order['total_weight_kg']} kg<br>
        <b>Order Total:</b> ₹{order['order_total']:.2f}<br>
        <b>Address:</b> {order['address'][:100]}...<br>
        <b>Coordinates:</b> {order['latitude']:.6f}, {order['longitude']:.6f}
    </div>
    """
    return popup_html

def create_trip_map(trip_data: dict, day: str, output_dir: str = "outputs") -> str:
    """
    Create interactive map with all trips
    
    Args:
        trip_data: Output from trip_generator
        day: Day identifier ("26" or "30")
        output_dir: Directory to save output
    
    Returns:
        Filename of saved map
    """
    print(f"\n🗺️  Creating interactive map...")
    
    trips = trip_data['trips']
    order_details = trip_data['order_details']
    metrics = trip_data['metrics']
    
    if not trips:
        print("❌ No trips to visualize!")
        return None
    
    # Calculate center point
    all_lats = [order['latitude'] for order in order_details.values()]
    all_lons = [order['longitude'] for order in order_details.values()]
    center_lat = sum(all_lats) / len(all_lats)
    center_lon = sum(all_lons) / len(all_lons)
    
    # Create map
    map_obj = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Generate colors
    colors = generate_color_palette(len(trips))
    
    # Plot each trip
    for idx, trip in enumerate(trips):
        trip_name = trip['trip_name']
        color = colors[idx]
        order_ids = trip['orders']
        trip_coords = []
        
        for order_id in order_ids:
            if order_id not in order_details:
                continue
            
            order = order_details[order_id]
            lat = order['latitude']
            lon = order['longitude']
            trip_coords.append([lat, lon])
            
            # Create popup
            popup_html = create_order_popup(order, trip_name, color)
            
            # Add small circle marker (like in the reference image)
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,  # Smaller radius for precise pinpointing
                popup=folium.Popup(popup_html, max_width=320),
                color='white',  # White border
                fill=True,
                fillColor=color,
                fillOpacity=0.9,
                weight=2  # Thinner border
            ).add_to(map_obj)
        
        # Draw route line (thinner for better visibility)
        if len(trip_coords) > 1:
            folium.PolyLine(
                locations=trip_coords,
                color=color,
                weight=2.5,  # Thinner line
                opacity=0.7,
                popup=f"{trip_name} - {trip['order_count']} orders - {trip['total_weight']} kg"
            ).add_to(map_obj)
    
    # Create legend
    legend_items = ''.join([
        f'<div style="margin: 3px 0;"><span style="display: inline-block; width: 15px; height: 15px; background-color: {colors[idx]}; border: 1px solid #333; margin-right: 5px;"></span>{trip["trip_name"]} - {trip["zone"]} ({trip["order_count"]} orders, {trip["total_weight"]} kg, {trip["utilization_percent"]}%)</div>'
        for idx, trip in enumerate(trips)
    ])
    
    legend_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 350px; max-height: 80vh; overflow-y: auto;
                background-color: white; z-index:9999; font-size:13px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
        <h4 style="margin-top:0;">Day {day} - Algorithm Generated Trips</h4>
        <p><b>Total Trips:</b> {metrics['number_of_trips']}</p>
        <p><b>Total Orders:</b> {len(order_details)}</p>
        <p><b>Avg Utilization:</b> {metrics['average_utilization_percent']}%</p>
        <p><b>Total Distance:</b> {metrics['total_distance_km']} km</p>
        <hr>
        <div style="font-size: 11px;">
            <b>Trip Legend:</b><br>
            {legend_items}
        </div>
    </div>
    '''
    map_obj.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    import os
    os.makedirs(os.path.join(output_dir, f"day_{day}"), exist_ok=True)
    map_filename = os.path.join(output_dir, f"day_{day}", f"algo_trips_day_{day}.html")
    map_obj.save(map_filename)
    
    print(f"✅ Map saved: {map_filename}")
    
    return map_filename
