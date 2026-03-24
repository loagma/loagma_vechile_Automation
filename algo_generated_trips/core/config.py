"""
Configuration module for algorithm-based trip generation
Contains day-specific settings and area name mappings
"""

import os

# Day configurations
DAY_CONFIGS = {
    "26": {
        "user_sheet": os.path.join("..", "human_made_trips_visualization", "vy37r1dlj4_UserSheet.txt"),
        "date": "2024-12-26",
        "vehicle_capacity": 1500.0,
        "description": "December 26th orders"
    },
    "30": {
        "user_sheet": os.path.join("..", "human_made_trips_visualization", "yocm27jhm8_UserSheet.txt"),
        "date": "2024-12-30",
        "vehicle_capacity": 1500.0,
        "description": "December 30th orders"
    }
}

# Area name to short code mapping (4 letters) - Smart zones based on delivery logic
AREA_CODE_MAPPING = {
    "ATTAPUR": "ATTA",
    "BANJARA HILLS": "BANJ",
    "BEGUMPET": "BEGU", 
    "SECUNDERABAD": "SECU",
    "KUKATPALLY": "KUKA",
    "GACHIBOWLI": "GACH",
    "UPPAL": "UPPA",
    "DILSUKHNAGAR": "DILS",
    "MEHDIPATNAM": "MEHD",
    "AMEERPET": "AMER",
    "OLD CITY": "OLDC",
    "NARSINGI": "NARS",
    "BORABANDA": "BORA",
    "OUTER AREAS": "OUTE",
    "OTHER AREAS": "OTHE"
}

def generate_trip_name(area_name: str, trip_number: int) -> str:
    """
    Convert area name to short code + number
    
    Args:
        area_name: Full area name (e.g., "ATTAPUR")
        trip_number: Sequential number for this area (1, 2, 3, ...)
    
    Returns:
        Trip name like "ATTA1", "GOLC2", etc.
    
    Example:
        >>> generate_trip_name("ATTAPUR", 1)
        'ATTA1'
        >>> generate_trip_name("GOLCONDA", 2)
        'GOLC2'
    """
    # Clean up area name (remove extra spaces, convert to uppercase)
    area_name = area_name.strip().upper()
    
    # Get short code from mapping
    short_code = AREA_CODE_MAPPING.get(area_name, area_name[:4])
    
    return f"{short_code}{trip_number}"

def get_area_code(area_name: str) -> str:
    """
    Get short code for an area name
    
    Args:
        area_name: Full area name
    
    Returns:
        4-letter area code
    """
    area_name = area_name.strip().upper()
    return AREA_CODE_MAPPING.get(area_name, area_name[:4])

# Pincode to Area mapping is now handled by the database
# See trip_cards and trip_card_pincode tables for current mappings
# Use get_zone_from_pincode() function in order_fetcher.py to query zones

def get_area_from_pincode(pincode: str) -> str:
    """
    Get area name from pincode using the database mapping
    This function is deprecated - use get_zone_from_pincode() in order_fetcher.py instead
    
    Args:
        pincode: Pincode string (e.g., "500048")
    
    Returns:
        Area name or "UNKNOWN" if not found
    """
    print("⚠️  get_area_from_pincode() is deprecated. Use get_zone_from_pincode() from order_fetcher.py")
    return "UNKNOWN"
