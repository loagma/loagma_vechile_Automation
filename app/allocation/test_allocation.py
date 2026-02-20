"""
Comprehensive Test Harness for Allocation Engine

Tests various scenarios including:
1. Small cluster (10 orders close together)
2. Tight capacity fragmentation
3. Perfect fit (sum weight == capacity)
4. Sparse distribution (orders far apart)
5. Dense distribution
6. Single heavy order (> capacity)
7. 100 random coordinates
"""
import random
import json
from typing import List, Dict
from app.allocation.allocation_engine import AllocationEngine


def generate_test_data() -> Dict[str, List[Dict]]:
    """
    Generate test datasets for various scenarios.
    
    Returns:
        Dictionary mapping test names to order lists
    """
    test_datasets = {}
    
    # ========================================================================
    # Test 1: Small Cluster (10 orders close together)
    # ========================================================================
    test_datasets["small_cluster"] = [
        {
            "order_id": i,
            "latitude": 13.0827 + random.uniform(-0.01, 0.01),  # Bangalore area
            "longitude": 80.2707 + random.uniform(-0.01, 0.01),  # Chennai area
            "pincode": "600001",
            "total_weight_kg": random.uniform(5, 20)
        }
        for i in range(1, 11)
    ]
    
    # ========================================================================
    # Test 2: Tight Capacity Fragmentation
    # ========================================================================
    # Orders with weights that fragment capacity (e.g., capacity=100, weights=60,60,60)
    test_datasets["tight_capacity"] = [
        {"order_id": 1, "latitude": 12.9716, "longitude": 77.5946, "pincode": "560001", "total_weight_kg": 60},
        {"order_id": 2, "latitude": 12.9720, "longitude": 77.5950, "pincode": "560001", "total_weight_kg": 60},
        {"order_id": 3, "latitude": 12.9725, "longitude": 77.5955, "pincode": "560001", "total_weight_kg": 60},
        {"order_id": 4, "latitude": 12.9730, "longitude": 77.5960, "pincode": "560001", "total_weight_kg": 35},
        {"order_id": 5, "latitude": 12.9735, "longitude": 77.5965, "pincode": "560001", "total_weight_kg": 35},
    ]
    
    # ========================================================================
    # Test 3: Perfect Fit (sum weight == capacity)
    # ========================================================================
    # Capacity = 100, orders = [25, 25, 25, 25]
    test_datasets["perfect_fit"] = [
        {"order_id": 1, "latitude": 19.0760, "longitude": 72.8777, "pincode": "400001", "total_weight_kg": 25},
        {"order_id": 2, "latitude": 19.0765, "longitude": 72.8780, "pincode": "400001", "total_weight_kg": 25},
        {"order_id": 3, "latitude": 19.0770, "longitude": 72.8785, "pincode": "400001", "total_weight_kg": 25},
        {"order_id": 4, "latitude": 19.0775, "longitude": 72.8790, "pincode": "400001", "total_weight_kg": 25},
    ]
    
    # ========================================================================
    # Test 4: Sparse Distribution (orders far apart)
    # ========================================================================
    test_datasets["sparse_distribution"] = [
        {"order_id": 1, "latitude": 28.7041, "longitude": 77.1025, "pincode": "110001", "total_weight_kg": 15},  # Delhi
        {"order_id": 2, "latitude": 19.0760, "longitude": 72.8777, "pincode": "400001", "total_weight_kg": 20},  # Mumbai
        {"order_id": 3, "latitude": 12.9716, "longitude": 77.5946, "pincode": "560001", "total_weight_kg": 18},  # Bangalore
        {"order_id": 4, "latitude": 22.5726, "longitude": 88.3639, "pincode": "700001", "total_weight_kg": 22},  # Kolkata
        {"order_id": 5, "latitude": 13.0827, "longitude": 80.2707, "pincode": "600001", "total_weight_kg": 17},  # Chennai
    ]
    
    # ========================================================================
    # Test 5: Dense Distribution
    # ========================================================================
    # 20 orders in a very small area
    base_lat = 12.9716
    base_lon = 77.5946
    test_datasets["dense_distribution"] = [
        {
            "order_id": i,
            "latitude": base_lat + random.uniform(-0.005, 0.005),
            "longitude": base_lon + random.uniform(-0.005, 0.005),
            "pincode": "560001",
            "total_weight_kg": random.uniform(3, 15)
        }
        for i in range(1, 21)
    ]
    
    # ========================================================================
    # Test 6: Single Heavy Order (> capacity)
    # ========================================================================
    test_datasets["heavy_order"] = [
        {"order_id": 1, "latitude": 12.9716, "longitude": 77.5946, "pincode": "560001", "total_weight_kg": 150},  # Exceeds capacity
        {"order_id": 2, "latitude": 12.9720, "longitude": 77.5950, "pincode": "560001", "total_weight_kg": 20},
        {"order_id": 3, "latitude": 12.9725, "longitude": 77.5955, "pincode": "560001", "total_weight_kg": 30},
        {"order_id": 4, "latitude": 12.9730, "longitude": 77.5960, "pincode": "560001", "total_weight_kg": 25},
    ]
    
    # ========================================================================
    # Test 7: 100 Random Coordinates
    # ========================================================================
    # Random orders across India
    test_datasets["random_100"] = [
        {
            "order_id": i,
            "latitude": random.uniform(8.0, 35.0),  # India latitude range
            "longitude": random.uniform(68.0, 97.0),  # India longitude range
            "pincode": f"{random.randint(100000, 999999)}",
            "total_weight_kg": random.uniform(1, 50)
        }
        for i in range(1, 101)
    ]
    
    # ========================================================================
    # Test 8: Edge Cases
    # ========================================================================
    test_datasets["edge_cases"] = [
        {"order_id": 1, "latitude": 12.9716, "longitude": 77.5946, "pincode": "560001", "total_weight_kg": 0},  # Zero weight
        {"order_id": 2, "latitude": 12.9720, "longitude": 77.5950, "pincode": "560001", "total_weight_kg": -5},  # Negative weight
        {"order_id": 3, "latitude": 12.9725, "longitude": 77.5955, "pincode": "560001", "total_weight_kg": 100},  # Exact capacity
        {"order_id": 4, "latitude": 12.9730, "longitude": 77.5960, "pincode": "560001", "total_weight_kg": 0.5},  # Very small
    ]
    
    return test_datasets


def print_test_results(test_name: str, result: Dict, vehicle_capacity: float):
    """
    Print formatted test results.
    
    Args:
        test_name: Name of the test
        result: Result dictionary from allocation engine
        vehicle_capacity: Vehicle capacity used
    """
    print(f"\n{'='*70}")
    print(f"TEST: {test_name.upper()}")
    print(f"{'='*70}")
    print(f"Vehicle Capacity: {vehicle_capacity} kg")
    print(f"\nRESULTS:")
    print(f"  Number of Trips: {result['metrics']['number_of_trips']}")
    print(f"  Average Utilization: {result['metrics']['average_utilization_percent']}%")
    print(f"  Total Distance: {result['metrics']['total_distance_km']} km")
    print(f"  Runtime: {result['metrics']['runtime_seconds']} seconds")
    
    if result['unallocatable_orders']:
        print(f"\n  Unallocatable Orders: {result['unallocatable_orders']}")
    
    print(f"\nTRIP DETAILS:")
    for trip in result['trips']:
        utilization = (trip['total_weight'] / vehicle_capacity) * 100
        print(f"  Trip {trip['trip_id']}: "
              f"{len(trip['orders'])} orders, "
              f"{trip['total_weight']} kg ({utilization:.1f}% full), "
              f"{trip['route_distance_km']} km")
        print(f"    Orders: {trip['orders']}")


def run_all_tests():
    """
    Run all test scenarios and print results.
    """
    print("\n" + "="*70)
    print("ALLOCATION ENGINE - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    # Generate test data
    test_datasets = generate_test_data()
    
    # Vehicle capacity for tests
    vehicle_capacity = 100.0  # kg
    
    # Run each test
    for test_name, orders in test_datasets.items():
        engine = AllocationEngine(vehicle_capacity_kg=vehicle_capacity)
        result = engine.run(orders)
        print_test_results(test_name, result, vehicle_capacity)
    
    # ========================================================================
    # Performance Test: 1000 Random Orders
    # ========================================================================
    print(f"\n{'='*70}")
    print("PERFORMANCE TEST: 1000 RANDOM ORDERS")
    print(f"{'='*70}")
    
    large_dataset = [
        {
            "order_id": i,
            "latitude": random.uniform(8.0, 35.0),
            "longitude": random.uniform(68.0, 97.0),
            "pincode": f"{random.randint(100000, 999999)}",
            "total_weight_kg": random.uniform(1, 50)
        }
        for i in range(1, 1001)
    ]
    
    engine = AllocationEngine(vehicle_capacity_kg=vehicle_capacity)
    result = engine.run(large_dataset)
    
    print(f"Vehicle Capacity: {vehicle_capacity} kg")
    print(f"Total Orders: 1000")
    print(f"\nRESULTS:")
    print(f"  Number of Trips: {result['metrics']['number_of_trips']}")
    print(f"  Average Utilization: {result['metrics']['average_utilization_percent']}%")
    print(f"  Total Distance: {result['metrics']['total_distance_km']} km")
    print(f"  Runtime: {result['metrics']['runtime_seconds']} seconds")
    print(f"  Performance: {'✓ PASS' if result['metrics']['runtime_seconds'] < 5.0 else '✗ FAIL'} (< 5s required)")
    
    if result['unallocatable_orders']:
        print(f"  Unallocatable Orders: {len(result['unallocatable_orders'])}")
    
    # ========================================================================
    # Summary
    # ========================================================================
    print(f"\n{'='*70}")
    print("TEST SUITE COMPLETE")
    print(f"{'='*70}\n")


def run_single_test(test_name: str, vehicle_capacity: float = 100.0):
    """
    Run a single test by name.
    
    Args:
        test_name: Name of the test to run
        vehicle_capacity: Vehicle capacity in kg
    """
    test_datasets = generate_test_data()
    
    if test_name not in test_datasets:
        print(f"Error: Test '{test_name}' not found.")
        print(f"Available tests: {', '.join(test_datasets.keys())}")
        return
    
    orders = test_datasets[test_name]
    engine = AllocationEngine(vehicle_capacity_kg=vehicle_capacity)
    result = engine.run(orders)
    
    print_test_results(test_name, result, vehicle_capacity)
    
    # Print detailed JSON output
    print(f"\nJSON OUTPUT:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    # Run all tests
    run_all_tests()
    
    # Optionally run a specific test
    # run_single_test("small_cluster")
