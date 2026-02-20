#!/usr/bin/env python3
"""
Allocation Engine Test Runner

Run this script to execute the comprehensive test suite for the
Capacitated Spatial Clustering allocation algorithm.

Usage:
    python run_allocation_tests.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.allocation.test_allocation import run_all_tests

if __name__ == "__main__":
    run_all_tests()
