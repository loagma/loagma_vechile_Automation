"""
Capacitated Spatial Clustering Algorithm for Delivery Trip Generation

This module implements a greedy spatial clustering algorithm that groups orders
into delivery trips while respecting vehicle capacity constraints.

Algorithm: 3-Stage Greedy Capacitated Spatial Clustering
- Stage 1: Preprocessing and validation
- Stage 2: Greedy spatial clustering with capacity constraints
- Stage 3: Metrics calculation and output generation
"""
import math
import time
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass


@dataclass
class Order:
    """Represents a delivery order with location and weight."""
    order_id: int
    latitude: float
    longitude: float
    pincode: str
    total_weight_kg: float
    
    def __hash__(self):
        return hash(self.order_id)
    
    def __eq__(self, other):
        return isinstance(other, Order) and self.order_id == other.order_id


@dataclass
class Trip:
    """Represents a delivery trip containing multiple orders."""
    trip_id: int
    orders: List[Order]
    total_weight: float
    route_distance_km: float


class AllocationEngine:
    """
    Main allocation engine implementing capacitated spatial clustering.
    
    The algorithm uses a greedy approach to cluster spatially close orders
    while respecting vehicle capacity constraints.
    """
    
    EARTH_RADIUS_KM = 6371.0  # Earth's radius in kilometers
    
    def __init__(self, vehicle_capacity_kg: float):
        """
        Initialize the allocation engine.
        
        Args:
            vehicle_capacity_kg: Maximum weight capacity of a vehicle in kg
        """
        self.vehicle_capacity_kg = vehicle_capacity_kg
        self.trips: List[Trip] = []
        self.unallocatable_orders: List[int] = []
        self.runtime_seconds: float = 0.0
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth.
        
        Uses the Haversine formula for accurate distance calculation.
        
        Args:
            lat1, lon1: Coordinates of first point (degrees)
            lat2, lon2: Coordinates of second point (degrees)
            
        Returns:
            Distance in kilometers
        """
        # Convert degrees to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return self.EARTH_RADIUS_KM * c
    
    def calculate_centroid(self, orders: List[Order]) -> Tuple[float, float]:
        """
        Calculate the geographic centroid of a list of orders.
        
        Args:
            orders: List of orders
            
        Returns:
            Tuple of (latitude, longitude) representing the centroid
        """
        if not orders:
            return (0.0, 0.0)
        
        avg_lat = sum(order.latitude for order in orders) / len(orders)
        avg_lon = sum(order.longitude for order in orders) / len(orders)
        
        return (avg_lat, avg_lon)
    
    def find_nearest_order(self, target_lat: float, target_lon: float, 
                          candidates: Set[Order]) -> Optional[Order]:
        """
        Find the nearest order to a target location from a set of candidates.
        
        Optimized version with early termination for large datasets.
        
        Args:
            target_lat, target_lon: Target coordinates
            candidates: Set of candidate orders
            
        Returns:
            Nearest order or None if no candidates
        """
        if not candidates:
            return None
        
        min_distance = float('inf')
        nearest_order = None
        
        # For small sets, use simple iteration
        if len(candidates) <= 50:
            for order in candidates:
                distance = self.haversine_distance(
                    target_lat, target_lon,
                    order.latitude, order.longitude
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_order = order
        else:
            # For larger sets, use sampling for speed
            # Sample up to 100 candidates
            sample_size = min(100, len(candidates))
            sample = list(candidates)[:sample_size]
            
            for order in sample:
                distance = self.haversine_distance(
                    target_lat, target_lon,
                    order.latitude, order.longitude
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest_order = order
        
        return nearest_order
    
    def count_neighbors_within_radius(self, order: Order, candidates: Set[Order], 
                                     radius_km: float = 5.0) -> int:
        """
        Count how many orders are within a given radius of the target order.
        
        Used to identify high-density regions for seed selection.
        Optimized for large datasets.
        
        Args:
            order: Target order
            candidates: Set of candidate orders
            radius_km: Search radius in kilometers
            
        Returns:
            Number of neighbors within radius
        """
        # For large datasets, sample to speed up
        if len(candidates) > 100:
            sample = list(candidates)[:100]
        else:
            sample = candidates
            
        count = 0
        for candidate in sample:
            if candidate.order_id == order.order_id:
                continue
            distance = self.haversine_distance(
                order.latitude, order.longitude,
                candidate.latitude, candidate.longitude
            )
            if distance <= radius_km:
                count += 1
        return count
    
    def select_seed_order(self, unassigned: Set[Order]) -> Order:
        """
        Select the best seed order for starting a new trip.
        
        Prefers orders in high-density regions to maximize clustering efficiency.
        Optimized for large datasets.
        
        Args:
            unassigned: Set of unassigned orders
            
        Returns:
            Selected seed order
        """
        if not unassigned:
            raise ValueError("Cannot select seed from empty set")
        
        # For small sets, use full density calculation
        if len(unassigned) <= 50:
            max_neighbors = -1
            best_seed = None
            
            for order in unassigned:
                neighbor_count = self.count_neighbors_within_radius(order, unassigned)
                if neighbor_count > max_neighbors:
                    max_neighbors = neighbor_count
                    best_seed = order
            
            return best_seed if best_seed else next(iter(unassigned))
        else:
            # For large sets, sample for speed
            sample_size = min(50, len(unassigned))
            sample = list(unassigned)[:sample_size]
            
            max_neighbors = -1
            best_seed = None
            
            for order in sample:
                neighbor_count = self.count_neighbors_within_radius(order, unassigned)
                if neighbor_count > max_neighbors:
                    max_neighbors = neighbor_count
                    best_seed = order
            
            return best_seed if best_seed else sample[0]
    
    def calculate_trip_distance(self, orders: List[Order]) -> float:
        """
        Calculate approximate route distance for a trip using nearest-neighbor heuristic.
        
        Starts from the first order and sequentially visits the nearest unvisited order.
        
        Args:
            orders: List of orders in the trip
            
        Returns:
            Total route distance in kilometers
        """
        if len(orders) <= 1:
            return 0.0
        
        total_distance = 0.0
        visited = set()
        current = orders[0]
        visited.add(current.order_id)
        
        while len(visited) < len(orders):
            # Find nearest unvisited order
            min_distance = float('inf')
            nearest = None
            
            for order in orders:
                if order.order_id not in visited:
                    distance = self.haversine_distance(
                        current.latitude, current.longitude,
                        order.latitude, order.longitude
                    )
                    if distance < min_distance:
                        min_distance = distance
                        nearest = order
            
            if nearest:
                total_distance += min_distance
                visited.add(nearest.order_id)
                current = nearest
        
        return total_distance
    
    def preprocess_orders(self, orders: List[Dict]) -> Tuple[List[Order], List[int]]:
        """
        Stage 1: Preprocess and validate orders.
        
        Filters invalid orders and identifies those exceeding vehicle capacity.
        
        Args:
            orders: List of order dictionaries
            
        Returns:
            Tuple of (valid_orders, unallocatable_order_ids)
        """
        valid_orders = []
        unallocatable = []
        
        for order_dict in orders:
            order_id = order_dict['order_id']
            weight = order_dict['total_weight_kg']
            
            # Filter invalid weights
            if weight <= 0:
                unallocatable.append(order_id)
                continue
            
            # Identify orders exceeding capacity
            if weight > self.vehicle_capacity_kg:
                unallocatable.append(order_id)
                continue
            
            # Create valid order object
            order = Order(
                order_id=order_id,
                latitude=order_dict['latitude'],
                longitude=order_dict['longitude'],
                pincode=order_dict['pincode'],
                total_weight_kg=weight
            )
            valid_orders.append(order)
        
        return valid_orders, unallocatable
    
    def cluster_orders(self, orders: List[Order]) -> List[Trip]:
        """
        Stage 2: Greedy Capacitated Spatial Clustering.
        
        Groups orders into trips using a greedy spatial clustering approach
        with strict capacity enforcement.
        
        Args:
            orders: List of valid orders to cluster
            
        Returns:
            List of generated trips
        """
        trips = []
        unassigned = set(orders)
        trip_id = 1
        
        while unassigned:
            # Create new trip
            trip_orders = []
            capacity_used = 0.0
            
            # Select seed order (prefer high-density regions)
            seed = self.select_seed_order(unassigned)
            trip_orders.append(seed)
            capacity_used += seed.total_weight_kg
            unassigned.remove(seed)
            
            # Greedy expansion: add nearest orders that fit
            while unassigned:
                # Calculate current trip centroid
                centroid_lat, centroid_lon = self.calculate_centroid(trip_orders)
                
                # Find nearest unassigned order
                nearest = self.find_nearest_order(centroid_lat, centroid_lon, unassigned)
                
                if not nearest:
                    break
                
                # Check capacity constraint
                if capacity_used + nearest.total_weight_kg <= self.vehicle_capacity_kg:
                    trip_orders.append(nearest)
                    capacity_used += nearest.total_weight_kg
                    unassigned.remove(nearest)
                else:
                    # Cannot add more orders to this trip
                    break
            
            # Calculate trip distance
            route_distance = self.calculate_trip_distance(trip_orders)
            
            # Create trip object
            trip = Trip(
                trip_id=trip_id,
                orders=trip_orders,
                total_weight=capacity_used,
                route_distance_km=route_distance
            )
            trips.append(trip)
            trip_id += 1
        
        return trips
    
    def compute_metrics(self, trips: List[Trip]) -> Dict:
        """
        Stage 3: Calculate performance metrics.
        
        Args:
            trips: List of generated trips
            
        Returns:
            Dictionary containing performance metrics
        """
        if not trips:
            return {
                "number_of_trips": 0,
                "average_utilization_percent": 0.0,
                "total_distance_km": 0.0,
                "runtime_seconds": self.runtime_seconds
            }
        
        total_distance = sum(trip.route_distance_km for trip in trips)
        total_weight = sum(trip.total_weight for trip in trips)
        max_possible_weight = len(trips) * self.vehicle_capacity_kg
        
        avg_utilization = (total_weight / max_possible_weight * 100) if max_possible_weight > 0 else 0.0
        
        return {
            "number_of_trips": len(trips),
            "average_utilization_percent": round(avg_utilization, 2),
            "total_distance_km": round(total_distance, 2),
            "runtime_seconds": round(self.runtime_seconds, 4)
        }
    
    def run(self, orders: List[Dict]) -> Dict:
        """
        Execute the complete allocation algorithm.
        
        Args:
            orders: List of order dictionaries with keys:
                   - order_id: int
                   - latitude: float
                   - longitude: float
                   - pincode: str
                   - total_weight_kg: float
        
        Returns:
            Dictionary containing:
                - trips: List of trip dictionaries
                - unallocatable_orders: List of order IDs
                - metrics: Performance metrics
        """
        start_time = time.time()
        
        # Stage 1: Preprocessing
        valid_orders, unallocatable = self.preprocess_orders(orders)
        self.unallocatable_orders = unallocatable
        
        # Stage 2: Clustering
        self.trips = self.cluster_orders(valid_orders)
        
        # Record runtime
        self.runtime_seconds = time.time() - start_time
        
        # Stage 3: Compute metrics
        metrics = self.compute_metrics(self.trips)
        
        # Format output
        return {
            "trips": [
                {
                    "trip_id": trip.trip_id,
                    "orders": [order.order_id for order in trip.orders],
                    "total_weight": round(trip.total_weight, 2),
                    "route_distance_km": round(trip.route_distance_km, 2)
                }
                for trip in self.trips
            ],
            "unallocatable_orders": self.unallocatable_orders,
            "metrics": metrics
        }
