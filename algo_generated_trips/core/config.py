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

# Area name to short code mapping (4 letters)
AREA_CODE_MAPPING = {
    "ATTAPUR": "ATTA",
    "GOLCONDA": "GOLC",
    "ASIF NAGAR": "ASIF",
    "GUDIMALKAPUR": "GUDI",
    "NARSINGI": "NARS",
    "BEGUMPET": "BEGU",
    "HAKIMPET": "HAKI",
    "MANIKONDA": "MANI",
    "HAFEEZPET": "HAFE",
    "BADANGPET": "BADA",
    "YOUSUFGUDA": "YOUS",
    "BORABANDA": "BORA"
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

# Pincode to Area Mapping (Generated from Day 26 human allocations)
PINCODE_TO_AREA = {
    "500001": "YOUSUFGUDA",
    "500003": "BEGUMPET",
    "500004": "YOUSUFGUDA",
    "500005": "BADANGPET",
    "500006": "ASIF NAGAR",
    "500008": "GOLCONDA",
    "500016": "BEGUMPET",
    "500018": "BORABANDA",
    "500020": "BEGUMPET",
    "500028": "ASIF NAGAR",
    "500030": "ATTAPUR",
    "500032": "HAFEEZPET",
    "500034": "YOUSUFGUDA",
    "500045": "BORABANDA",
    "500048": "ATTAPUR",
    "500049": "HAFEEZPET",
    "500052": "ATTAPUR",
    "500053": "BADANGPET",
    "500057": "ASIF NAGAR",
    "500058": "BADANGPET",
    "500059": "BADANGPET",
    "500061": "BEGUMPET",
    "500064": "ATTAPUR",
    "500073": "YOUSUFGUDA",
    "500075": "NARSINGI",
    "500077": "ATTAPUR",
    "500084": "HAFEEZPET",
    "500086": "NARSINGI",
    "500089": "NARSINGI",
    "500091": "NARSINGI",
    "500096": "MANIKONDA",
    "500097": "BADANGPET",
    "500114": "BORABANDA",
    "500264": "ATTAPUR",
    "501359": "BADANGPET",
}

def get_area_from_pincode(pincode: str) -> str:
    """
    Get area name from pincode using the mapping
    
    Args:
        pincode: Pincode string (e.g., "500048")
    
    Returns:
        Area name (e.g., "ATTAPUR") or "UNKNOWN" if not found
    """
    if not pincode:
        return "UNKNOWN"
    
    # Clean pincode (remove spaces, convert to string)
    pincode = str(pincode).strip()
    
    return PINCODE_TO_AREA.get(pincode, "UNKNOWN")
