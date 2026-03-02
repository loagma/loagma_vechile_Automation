"""
Smart Allocation Engine - Creates trips considering weight and geographic clustering
Uses k-means clustering for geographic grouping and bin packing for weight optimization
"""

import math
from typing import List, Dict
from collections import defaultdict

class AllocationEngine:
    """
    Smart trip allocation engine that considers:
    1. Geographic proximity (clustering nearby orders)
    2. Weight constraints (vehicle capacity)
    3. Trip optimization (minimize number of trips)
    """
    
    def __init__(self, vehicle_capacity_kg: float):
        self.vehicle_capacity_kg = vehicle_capacity_kg
        self.trips = []
        self.metrics = {}
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate haversine distance between two points in km
        """
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def calculate_centroid(self, orders: List[Dict]) -> tuple:
        """
        Calculate geographic centroid of orders
        """
        if not orders:
            return (0, 0)
        
        avg_lat = sum(o['latitude'] for o in orders) / len(orders)
        avg_lon = sum(o['longitude'] for o in orders) / len(orders)
        
        return (avg_lat, avg_lon)
    
    def cluster_orders_by_proximity(self, orders: List[Dict], num_clusters: int) -> List[List[Dict]]:
        """
        Simple k-means clustering to group nearby orders
        """
        if len(orders) <= num_clusters:
            return [[o] for o in orders]
        
        # Initialize centroids randomly from orders
        import random
        centroids = random.sample(orders, num_clusters)
        centroid_coords = [(c['latitude'], c['longitude']) for c in centroids]
        
        # Run k-means for a few iterations
        for _ in range(10):
            # Assign orders to nearest centroid
            clusters = [[] for _ in range(num_clusters)]
            
            for order in orders:
                distances = [
                    self.calculate_distance(order['latitude'], order['longitude'], c[0], c[1])
                    for c in centroid_coords
                ]
                nearest_cluster = distances.index(min(distances))
                clusters[nearest_cluster].append(order)
            
            # Update centroids
            centroid_coords = [
                self.calculate_centroid(cluster) if cluster else centroid_coords[i]
                for i, cluster in enumerate(clusters)
            ]
        
        # Remove empty clusters
        return [c for c in clusters if c]
    
    def pack_orders_into_trip(self, orders: List[Dict]) -> List[Dict]:
        """
        Pack orders into trips respecting weight capacity
        Uses first-fit decreasing bin packing
        """
        # Sort orders by weight (descending) for better packing
        sorted_orders = sorted(orders, key=lambda x: x['total_weight_kg'], reverse=True)
        
        trips = []
        current_trip = []
        current_weight = 0
        
        for order in sorted_orders:
            order_weight = order['total_weight_kg']
            
            if current_weight + order_weight <= self.vehicle_capacity_kg:
                # Add to current trip
                current_trip.append(order)
                current_weight += order_weight
            else:
                # Start new trip
                if current_trip:
                    trips.append({
                        'orders': current_trip,
                        'total_weight': round(current_weight, 2)
                    })
                current_trip = [order]
                current_weight = order_weight
        
        # Add last trip
        if current_trip:
            trips.append({
                'orders': current_trip,
                'total_weight': round(current_weight, 2)
            })
        
        return trips
    
    def estimate_num_clusters(self, orders: List[Dict]) -> int:
        """
        Estimate optimal number of clusters based on total weight and capacity
        """
        total_weight = sum(o['total_weight_kg'] for o in orders)
        min_trips = math.ceil(total_weight / self.vehicle_capacity_kg)
        
        # Add 20% buffer for geographic optimization
        estimated_clusters = max(1, int(min_trips * 1.2))
        
        # Cap at number of orders
        return min(estimated_clusters, len(orders))
    
    def run(self, orders: List[Dict]) -> Dict:
        """
        Main allocation algorithm
        
        Args:
            orders: List of order dicts with order_id, latitude, longitude, total_weight_kg
        
        Returns:
            Dictionary with trips and metrics
        """
        if not orders:
            return {
                'trips': [],
                'metrics': {
                    'number_of_trips': 0,
                    'total_distance_km': 0,
                    'average_utilization_percent': 0
                }
            }
        
        print(f"\n🧠 Running smart allocation engine...")
        print(f"   Orders: {len(orders)}")
        print(f"   Vehicle capacity: {self.vehicle_capacity_kg} kg")
        
        # Step 1: Estimate number of clusters needed
        num_clusters = self.estimate_num_clusters(orders)
        print(f"   Estimated clusters: {num_clusters}")
        
        # Step 2: Cluster orders by geographic proximity
        if num_clusters > 1:
            clusters = self.cluster_orders_by_proximity(orders, num_clusters)
            print(f"   Created {len(clusters)} geographic clusters")
        else:
            clusters = [orders]
        
        # Step 3: Pack each cluster into trips respecting weight capacity
        all_trips = []
        trip_id = 1
        
        for cluster_idx, cluster in enumerate(clusters):
            cluster_trips = self.pack_orders_into_trip(cluster)
            
            for trip in cluster_trips:
                all_trips.append({
                    'trip_id': trip_id,
                    'orders': [o['order_id'] for o in trip['orders']],
                    'total_weight': trip['total_weight'],
                    'order_details': trip['orders']
                })
                trip_id += 1
        
        # Step 4: Calculate metrics
        total_weight = sum(t['total_weight'] for t in all_trips)
        total_capacity = len(all_trips) * self.vehicle_capacity_kg
        avg_utilization = round((total_weight / total_capacity * 100), 1) if total_capacity > 0 else 0
        
        # Calculate total distance (sum of distances within each trip)
        total_distance = 0
        for trip in all_trips:
            trip_orders = trip['order_details']
            if len(trip_orders) > 1:
                for i in range(len(trip_orders) - 1):
                    dist = self.calculate_distance(
                        trip_orders[i]['latitude'],
                        trip_orders[i]['longitude'],
                        trip_orders[i+1]['latitude'],
                        trip_orders[i+1]['longitude']
                    )
                    total_distance += dist
        
        metrics = {
            'number_of_trips': len(all_trips),
            'total_distance_km': round(total_distance, 2),
            'average_utilization_percent': avg_utilization,
            'total_weight_kg': round(total_weight, 2),
            'total_capacity_kg': round(total_capacity, 2)
        }
        
        print(f"\n✅ Allocation complete!")
        print(f"   Trips created: {metrics['number_of_trips']}")
        print(f"   Avg utilization: {metrics['average_utilization_percent']}%")
        print(f"   Total distance: {metrics['total_distance_km']} km")
        
        return {
            'trips': all_trips,
            'metrics': metrics
        }
