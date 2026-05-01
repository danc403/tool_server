import urllib.request
import urllib.parse
import json
import asyncio

async def weather(
    location: str,
    units: str = "auto",  # 'auto', 'us', 'metric', 'metric_wind_ms'
    lang: str = "en",
    json_format_code: str = "j1" # Currently, only 'j1' is described by wttr.in for basic JSON output
) -> dict:
    """
    Fetches weather information for a single specified location in JSON format using wttr.in.

    This tool is designed to provide structured weather data that is easy to parse
    and integrate into other systems.

    Args:
        location (str): The geographical location (city name, airport code, special location
                        prefixed with '~', IP address, or domain prefixed with '@')
                        for which to retrieve weather. Examples: "London", "muc",
                        "~Eiffel+Tower", "@github.com", "станция+Восток".
                        This parameter accepts only one location per call.
        units (str, optional): The unit system for temperature and wind speed.
                               'auto': Automatically determined by IP.
                               'us': USCS units (Fahrenheit, miles/hour).
                               'metric': SI units (Celsius, km/hour).
                               'metric_wind_ms': SI units with wind speed in meters/second.
                               Defaults to 'auto'.
        lang (str, optional): The language for the output (e.g., "en", "fr", "de", "nl", "uk").
                              Defaults to "en".
        json_format_code (str, optional): The specific JSON output format code from wttr.in.
                                          Currently, 'j1' is the described basic JSON format.
                                          Defaults to 'j1'.

    Returns:
        dict: A dictionary representing the JSON response.
              The structure will always contain a 'status' key.

              On **success**, the JSON will have the following structure:
              ```json
              {
                "status": "success",
                "data": {
                  "current_condition": [
                    {
                      "FeelsLikeC": "...",
                      "FeelsLikeF": "...",
                      "temp_C": "...",
                      "temp_F": "...",
                      "weatherDesc": [{ "value": "..." }],
                      "windspeedKmph": "..."
                    }
                  ],
                  "nearest_area": [...],
                  "request": [...],
                  "weather": [...]
                }
              }
              ```

              On **failure** (e.g., network error, invalid location),
              the JSON will have the following structure:
              ```json
              {
                "status": "error",
                "message": "A descriptive error message indicating what went wrong."
              }
              ```
    """
    base_url = f"https://wttr.in/{urllib.parse.quote(location)}"
    
    # Build query parameters
    params = {"format": json_format_code}
    
    # Handle units according to wttr.in internal flags
    if units == "us":
        params["u"] = ""
    elif units == "metric":
        params["m"] = ""
    elif units == "metric_wind_ms":
        params["M"] = ""

    # Handle language
    if lang != "en":
        params["lang"] = lang

    # Construct full URL with parameters
    query_string = urllib.parse.urlencode(params)
    full_url = f"{base_url}?{query_string}"

    try:
        # Wrapping the blocking urllib call in a thread to maintain async compatibility
        def fetch_data():
            with urllib.request.urlopen(full_url, timeout=10.0) as response:
                return response.read().decode('utf-8')

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, fetch_data)
        
        # Load the original data
        raw_json = json.loads(data)
        
        # Pruning logic: We explicitly rebuild the lists to exclude nested bloat 
        # while keeping only the top-level identity keys from the raw API.
        
        # 1. Strip current_condition to the specific 6 keys requested
        current = raw_json.get("current_condition", [{}])[0]
        pruned_current = {
            "FeelsLikeC": current.get("FeelsLikeC"),
            "FeelsLikeF": current.get("FeelsLikeF"),
            "temp_C": current.get("temp_C"),
            "temp_F": current.get("temp_F"),
            "weatherDesc": [{"value": current.get("weatherDesc", [{}])[0].get("value")}],
            "windspeedKmph": current.get("windspeedKmph")
        }

        # 2. Reconstruct the output to ensure NO unrequested keys leak through
        structured_data = {
            "current_condition": [pruned_current],
            "nearest_area": raw_json.get("nearest_area", [])[:1], # Keep identity, drop extra area objects
            "request": raw_json.get("request", []),
            "weather": [] # Strip all multi-day/hourly forecast objects to clear bloat
        }
        
        return {
            "status": "success", 
            "data": structured_data
        }
            
    except urllib.error.HTTPError as e:
        return {
            "status": "error", 
            "message": f"Weather service returned an error: {e.code} for {location}"
        }
    except urllib.error.URLError as e:
        return {
            "status": "error", 
            "message": f"Network error while retrieving weather data: {e.reason}"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"An unexpected error occurred: {str(e)}"
        }
