"""
Geographic utility functions for distance calculations and coordinate handling.
"""
import math
from datetime import date
from typing import Tuple, Optional
from app.models.profile import Profile


def string_to_coordinates_tuple(coord_str: Optional[str]) -> Optional[Tuple[float, float]]:
    """
    Parse a coordinate string in format "lat,lng" into a tuple of floats.
    
    Args:
        coord_str: String in format "lat,lng" (e.g. "-1.2921,36.8219")
        
    Returns:
        Tuple of (latitude, longitude) as floats, or None if invalid/empty
    """
    if not coord_str or not coord_str.strip():
        return None
    
    try:
        parts = coord_str.strip().split(',')
        if len(parts) != 2:
            return None
        
        lat = float(parts[0].strip())
        lng = float(parts[1].strip())
        
        # Basic validation: latitude should be between -90 and 90, longitude between -180 and 180
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return None
        
        return (lat, lng)
    except (ValueError, AttributeError):
        return None


def haversine(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate the great circle distance between two points on Earth using the Haversine formula.
    
    Args:
        coord1: Tuple of (latitude, longitude) for first point
        coord2: Tuple of (latitude, longitude) for second point
        
    Returns:
        Distance in kilometers between the two points
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    distance = R * c
    return distance


def calc_profile_age(profile: Profile) -> int:
    """
    Calculate the age of a profile based on date_of_birth.
    
    Args:
        profile: Profile model instance with date_of_birth
        
    Returns:
        Age in years
    """
    if not profile.date_of_birth:
        return 0
    
    today = date.today()
    age = today.year - profile.date_of_birth.year
    
    # Adjust if birthday hasn't occurred this year
    if (today.month, today.day) < (profile.date_of_birth.month, profile.date_of_birth.day):
        age -= 1
    
    return age


def filter_out_profiles_outside_range(
    current_profile: Profile,
    map_profiles: list,
    preferences: Optional[dict]
) -> list:
    """
    Filter profiles based on distance and age preferences.
    
    Args:
        current_profile: The profile of the current user
        map_profiles: List of User objects with profiles to filter
        preferences: Dictionary with keys: min_age, max_age, distance (in km)
        
    Returns:
        Filtered list of User objects that match the preferences
    """
    if not preferences:
        # Default preferences if not set
        preferences = {
            "min_age": 18,
            "max_age": 99,
            "distance": 50.0  # 50 km default radius
        }
    
    min_age = preferences.get("min_age", 18)
    max_age = preferences.get("max_age", 99)
    radius = preferences.get("distance", 50.0)
    
    # Get current profile coordinates
    profile_coords = string_to_coordinates_tuple(current_profile.current_coordinates)
    if not profile_coords:
        # If current profile has no coordinates, return empty list
        return []
    
    result = []
    for user in map_profiles:
        if not user.profile or not user.profile.current_coordinates:
            continue
        
        # Get profile coordinates
        user_coords = string_to_coordinates_tuple(user.profile.current_coordinates)
        if not user_coords:
            continue
        
        # Calculate distance
        distance = haversine(profile_coords, user_coords)
        
        # Calculate age
        age = calc_profile_age(user.profile)
        
        # Check if within range
        if distance <= radius and min_age <= age <= max_age:
            result.append(user)
    
    return result
