# distance.py
import json
import math
import requests # Still needed for potential future expansion or if Haversine logic needs external data

async def distance(
    location1: dict,
    location2: dict
) -> dict:
    """
    Calculates the great-circle distance between two geographical points (latitude, longitude)
    using the Haversine formula and returns the distance in miles, rounded to the nearest mile.

    This tool expects location coordinates to be provided as dictionaries with 'latitude'
    and 'longitude' keys. These coordinates are typically obtained from a geolocation tool
    or inferred by the model itself.

    Args:
        location1 (dict): A dictionary representing the first location.
                          Expected format: `{'latitude': float, 'longitude': float}`.
                          Example: `{'latitude': 34.0522, 'longitude': -118.2437}` (Los Angeles).
        location2 (dict): A dictionary representing the second location.
                          Expected format: `{'latitude': float, 'longitude': float}`.
                          Example: `{'latitude': 40.7128, 'longitude': -74.0060}` (New York).

    Returns:
        dict: A dictionary representing the JSON response.
              The structure will always contain a 'status' key.

              On **success**, the JSON will have the following structure:
              ```json
              {
                "status": "success",
                "data": {
                  "distance_miles": 1234
                }
              }
              ```
              where `distance_miles` is an integer representing the distance
              between the two locations, rounded to the nearest mile.

              On **failure** (e.g., invalid input coordinates, missing lat/lon keys,
              non-numeric values), the JSON will have the following structure:
              ```json
              {
                "status": "error",
                "message": "A descriptive error message indicating what went wrong."
              }
              ```
    """
    try:
        # Extract and validate coordinates
        lat1 = float(location1.get('latitude'))
        lon1 = float(location1.get('longitude'))
        lat2 = float(location2.get('latitude'))
        lon2 = float(location2.get('longitude'))

        # Earth radius in miles
        R = 3958.8

        # Convert latitude and longitude to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance_miles = R * c

        # Round to the nearest mile
        rounded_distance = round(distance_miles)

        return {
            "status": "success",
            "data": {
                "distance_miles": rounded_distance
            }
        }
    except (TypeError, ValueError) as e:
        return {
            "status": "error",
            "message": f"Invalid input format for locations. Ensure latitude and longitude are valid numbers. Error: {e}"
        }
    except Exception as e:
        # Catch any other unexpected errors during calculation
        return {
            "status": "error",
            "message": f"An unexpected error occurred during distance calculation: {e}"
        }

async def distance_tool(location1: dict, location2: dict) -> str:
    """
    Primary dispatcher for the distance tool to ensure JSON string output.
    
    Args:
        location1 (dict): First coordinate set {'latitude': float, 'longitude': float}.
        location2 (dict): Second coordinate set {'latitude': float, 'longitude': float}.
        
    Returns:
        str: JSON string containing the distance result or error.
    """
    result = await distance(location1, location2)
    return json.dumps(result, indent=2)
