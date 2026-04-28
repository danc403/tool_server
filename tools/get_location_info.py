#pip install aiohttp geopy

# geolocation.py
import aiohttp
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import re
import os
import asyncio
import json

# --- Configuration ---
NOMINATIM_USER_AGENT = "NymphChatGeolocationTool/1.0 (contact@example.com)"
GEOCODING_TIMEOUT = 10 # seconds
NOMINATIM_DELAY = 1.1 # seconds, per Nominatim usage policy for free tier

# IP Geolocation service (still using ip-api.com's free tier)
IP_GEOLOCATION_API_URL = "http://ip-api.com/json/"

# --- Helper Functions for Geocoding and IP ---

def _is_lat_lon(query: str):
    """Checks if the query string looks like a latitude,longitude pair."""
    match = re.match(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$", query)
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
        except ValueError:
            pass
    return None

def _is_zip_code(query: str):
    """Checks if the query string looks like a US ZIP code."""
    match = re.match(r"^\d{5}$", query)
    if match:
        return query
    return None

def _is_ip_address(query: str):
    """Checks if the query string looks like an IPv4 address."""
    match = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", query)
    if match:
        if all(0 <= int(part) <= 255 for part in match.groups()):
            return query
    return None

async def _get_coords_from_ip_async(session: aiohttp.ClientSession, ip_address: str = None):
    """
    Gets latitude and longitude and other basic IP geo data from an IP address using ip-api.com.
    Returns a dictionary or None.
    """
    print(f"DEBUG: Entering _get_coords_from_ip_async for IP: {ip_address}")
    url = IP_GEOLOCATION_API_URL
    if ip_address:
        url += ip_address

    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            data = await response.json()
            if data.get('status') == 'success':
                print(f"DEBUG: IP Geolocation successful for {ip_address if ip_address else 'local machine IP'}: {data}")
                return {
                    "latitude": data.get('lat'),
                    "longitude": data.get('lon'),
                    "city": data.get('city'),
                    "state": data.get('regionName'),
                    "country": data.get('country'),
                    "postcode": data.get('zip'),
                    "resolved_ip": data.get('query') # The IP that was queried
                }
            print(f"DEBUG: IP Geolocation failed for {ip_address if ip_address else 'local machine IP'}: {data.get('message', data.get('status', 'Unknown error'))}")
    except aiohttp.ClientError as e:
        print(f"DEBUG: Error during IP geolocation request for {ip_address if ip_address else 'local machine IP'}: {e}")
    except Exception as e:
        print(f"DEBUG: An unexpected error occurred during IP geolocation for {ip_address if ip_address else 'local machine IP'}: {e}")
    return None

async def _resolve_location_details(session: aiohttp.ClientSession, query: str = None, client_ip: str = None):
    """
    Attempts to resolve location details (coords and address components)
    from various input types.
    """
    print(f"DEBUG: Entering _resolve_location_details with query='{query}' and client_ip='{client_ip}'")

    geolocator = Nominatim(user_agent=NOMINATIM_USER_AGENT)
    
    # Initialize all potential output fields to None/default
    resolved_info = {
        "latitude": None,
        "longitude": None,
        "city": None,
        "state": None,
        "country": None,
        "postcode": None,
        "address": None,
        "resolved_type": "unknown", # Default, gets updated
        "resolved_ip": None,
        "is_approximate": True # Default, gets updated (true for IP-based, false for precise address lookup)
    }

    # 1. Try if it's already lat/lon from query
    if query:
        coords = _is_lat_lon(query)
        if coords:
            resolved_info["latitude"], resolved_info["longitude"] = coords
            resolved_info["resolved_type"] = "lat_lon"
            resolved_info["is_approximate"] = False # Direct coords are precise
            print(f"DEBUG: Resolved as direct lat/lon: {resolved_info}")
            return resolved_info # Return early as this is the most precise query type

    # 2. Try Nominatim for ZIP code or general address (if a query string was provided)
    # This is now prioritized over IP fallbacks to fix satellite ISP issues.
    if query and not _is_ip_address(query):
        nom_query = query
        resolved_type_nominatim = "general_address"
        zip_code = _is_zip_code(query)
        if zip_code:
            nom_query = f"{zip_code}, USA" # Hint Nominatim for US ZIPs
            resolved_type_nominatim = "zip_code"
            print(f"DEBUG: Attempting Nominatim geocoding for ZIP code: {nom_query}")
        else:
            print(f"DEBUG: Attempting Nominatim geocoding for general location: {nom_query}")

        try:
            await asyncio.sleep(NOMINATIM_DELAY) # Respect Nominatim rate limit
            location = await asyncio.to_thread(geolocator.geocode, nom_query, timeout=GEOCODING_TIMEOUT, addressdetails=True)
            if location:
                resolved_info["latitude"] = location.latitude
                resolved_info["longitude"] = location.longitude
                resolved_info["address"] = location.address
                resolved_info["resolved_type"] = resolved_type_nominatim
                resolved_info["is_approximate"] = False # Nominatim address lookup is generally precise
                
                # Extract components from raw address details
                raw_address = location.raw.get('address', {})
                resolved_info["city"] = raw_address.get('city') or raw_address.get('town') or raw_address.get('village')
                resolved_info["state"] = raw_address.get('state')
                resolved_info["country"] = raw_address.get('country')
                resolved_info["postcode"] = raw_address.get('postcode')
                print(f"DEBUG: Nominatim geocoding successful: {resolved_info}")
                return resolved_info # Return early
            else:
                print(f"DEBUG: Nominatim could not geocode query: {nom_query}")
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"DEBUG: Nominatim geocoding failed (timeout/service error): {e}")
        except Exception as e:
            print(f"DEBUG: An unexpected error occurred during Nominatim geocoding: {e}")

    # 3. Try query as explicit IP address
    if query:
        ip_addr = _is_ip_address(query)
        if ip_addr:
            print(f"DEBUG: Detected explicit IP address in query: {ip_addr}")
            ip_data = await _get_coords_from_ip_async(session, ip_addr)
            if ip_data and ip_data.get('latitude') is not None:
                resolved_info.update(ip_data)
                resolved_info["resolved_type"] = "query_ip"
                resolved_info["is_approximate"] = True # IP geo is approximate
                print(f"DEBUG: Resolved as query_ip: {resolved_info}")
                return resolved_info # Return early

    # 4. Try client_ip (if query failed or was missing)
    if client_ip and _is_ip_address(client_ip):
        print(f"DEBUG: Attempting IP geolocation for client IP: {client_ip}")
        ip_data = await _get_coords_from_ip_async(session, client_ip)
        if ip_data and ip_data.get('latitude') is not None:
            resolved_info.update(ip_data)
            resolved_info["resolved_type"] = "client_ip"
            resolved_info["is_approximate"] = True # IP geo is approximate
            print(f"DEBUG: Resolved as client_ip: {resolved_info}")
            return resolved_info # Return early

    # 5. Final fallback: Use the server's public IP
    print("DEBUG: No location resolved yet from query/client_ip. Falling back to server's public IP...")
    ip_data = await _get_coords_from_ip_async(session)
    if ip_data and ip_data.get('latitude') is not None:
        resolved_info.update(ip_data)
        resolved_info["resolved_type"] = "server_ip"
        resolved_info["is_approximate"] = True # IP geo is approximate
        print(f"DEBUG: Server IP fallback successful: {resolved_info}")
        return resolved_info
    else:
        print("DEBUG: Failed to get coordinates from any source, including server's IP.")
        # If all attempts fail, return the initialized resolved_info with None values

    return resolved_info

async def get_location_info(query: str = None, client_ip: str = None):
    """
    Retrieves detailed geolocation information for a given query or IP address.

    This tool does not require any API keys. It leverages Nominatim (OpenStreetMap)
    for address-based lookups and ip-api.com for IP-based lookups.

    Args:
        query (str, optional): The location query (e.g., "London, UK", "90210", "34.05, -118.25", or an IP address).
                                If None, the tool will attempt to use the client_ip or the server's public IP.
        client_ip (str, optional): The IP address of the client making the request, provided by the calling server.
                                   Used as a fallback for location if explicit query is not provided.
    Returns:
        str: A JSON string containing detailed geolocation information. All possible keys
             are always included, with `null` for unpopulated fields.

             Example Success Output (all keys present):
             ```json
             {
               "status": "success",
               "query_input": "London, UK",
               "latitude": 51.5073219,
               "longitude": -0.1276474,
               "city": "London",
               "state": "England",
               "country": "United Kingdom",
               "postcode": "SW1A 0AA",
               "address": "London, Greater London, England, SW1A 0AA, United Kingdom",
               "resolved_type": "general_address",
               "resolved_ip": null,
               "is_approximate": false
             }
             ```

             Example Partial Success (from IP, with some address details, others null):
             ```json
             {
               "status": "success",
               "query_input": null,
               "latitude": 37.7749,
               "longitude": -122.4194,
               "city": "San Francisco",
               "state": "California",
               "country": "United States",
               "postcode": "94103",
               "address": null,
               "resolved_type": "server_ip",
               "resolved_ip": "1.2.3.4",
               "is_approximate": true
             }
             ```

             Example Error Output (all keys present, most are null):
             ```json
             {
               "status": "error",
               "query_input": "invalid location abc",
               "latitude": null,
               "longitude": null,
               "city": null,
               "state": null,
               "country": null,
               "postcode": null,
               "address": null,
               "resolved_type": "unknown",
               "resolved_ip": null,
               "is_approximate": true,
               "message": "Could not resolve location information for 'invalid location abc'."
             }
             ```
    """
    async with aiohttp.ClientSession() as session:
        print(f"DEBUG: get_location_info tool called with query='{query}', client_ip='{client_ip}'")

        resolved_details = await _resolve_location_details(session, query, client_ip)

        # Initialize the payload with all possible keys, defaulting to None/null
        response_payload = {
            "status": "error", # Default status
            "query_input": query,
            "latitude": resolved_details["latitude"],
            "longitude": resolved_details["longitude"],
            "city": resolved_details["city"],
            "state": resolved_details["state"],
            "country": resolved_details["country"],
            "postcode": resolved_details["postcode"],
            "address": resolved_details["address"],
            "resolved_type": resolved_details["resolved_type"],
            "resolved_ip": resolved_details["resolved_ip"],
            "is_approximate": resolved_details["is_approximate"],
            "message": "Could not resolve location information." # Default error message
        }

        # If latitude/longitude are present, it means a resolution occurred
        if response_payload["latitude"] is not None and response_payload["longitude"] is not None:
            response_payload["status"] = "success"
            # Remove the default error message on success
            if "message" in response_payload:
                del response_payload["message"]
        elif not query and not client_ip:
             response_payload["message"] = "No location query or client IP provided, and server IP fallback failed."
        # If resolution failed, the 'error' status and default message will remain,
        # and all geo fields will be None/null as initialized from resolved_details.

        final_json_output = json.dumps(response_payload, indent=2)
        print(f"DEBUG: Final JSON output: {final_json_output}")
        return final_json_output

# --- Example Usage for Testing (if run directly) ---
if __name__ == "__main__":
    async def main_test():
        print("--- Async Geolocation Tool Test ---")

        queries_to_test = [
            "London, UK",
            "New York, NY",
            "90210",                  # Beverly Hills, CA
            "40.7128, -74.0060",      # New York City (lat,lon)
            "192.168.1.1",            # Example private IP (will fail IP lookup as it's not public)
            "8.8.8.8",                # Google DNS (will geolocate to Google's data center location)
            None,                     # No query, will fallback to server's public IP
            "Springfield, Missouri",  # Your location
            "invalid location abc",    # Example of a failed lookup
            "Tokyo, Japan",
            "Paris, France",
            "Sydney, Australia",
            "37.215, -93.303" # More specific Springfield, MO coords
        ]

        for q in queries_to_test:
            print(f"\n--- Testing Query: '{q}' ---")
            result = await get_location_info(query=q)
            print(result)
            print("-" * 60)

        print("\n--- Testing with client_ip parameter explicitly ---")
        client_test_ip = "203.0.113.45" # Example public IP
        result_client_ip = await get_location_info(query="Chicago", client_ip=client_test_ip)
        print(f"\nQuerying geolocation for 'Chicago' but with client_ip '{client_test_ip}':")
        print(result_client_ip)
        print("-" * 60)

        result_only_client_ip = await get_location_info(query=None, client_ip=client_test_ip)
        print(f"\nQuerying geolocation with only client_ip '{client_test_ip}':")
        print(result_only_client_ip)
        print("-" * 60)

        print("\n--- Testing query that should resolve to current location (Springfield, MO) ---")
        result_springfield = await get_location_info(query="Springfield, MO")
        print(result_springfield)
        print("-" * 60)

        print("\n--- Testing with no inputs (should fallback to server IP) ---")
        result_no_inputs = await get_location_info()
        print(result_no_inputs)
        print("-" * 60)


    async def run_main():
        await main_test()

    asyncio.run(run_main())
