# time_utils.py
import json
import asyncio
from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

async def get_current_time(timezone: str = "local") -> dict:
    """
    Retrieves the current date and time in a specified timezone using native Python zoneinfo.

    Args:
        timezone (str, optional): The IANA timezone string (e.g., "America/New_York", "Europe/London", "UTC").
                                  Defaults to "local", which uses the system's local timezone.

    Returns:
        dict: A dictionary representing the JSON response.

        On **success**:
        ```json
        {
          "status": "success",
          "data": {
            "current_time": "2025-06-11T19:47:56.123456-05:00",
            "timezone": "America/Chicago"
          }
        }
        ```

        On **failure**:
        ```json
        {
          "status": "error",
          "message": "A descriptive error message."
        }
        ```
    """
    try:
        await asyncio.sleep(0.01)

        if timezone.lower() == "local":
            # Native way to get system local time with full tzinfo
            dt_now = datetime.now().astimezone()
            tz_name = str(dt_now.tzinfo)
        else:
            try:
                tz = ZoneInfo(timezone)
                dt_now = datetime.now(tz)
                tz_name = timezone
            except ZoneInfoNotFoundError:
                return {
                    "status": "error", 
                    "message": f"Unknown timezone: '{timezone}'. Use IANA names like 'America/Chicago'."
                }

        return {
            "status": "success",
            "data": {
                "current_time": dt_now.isoformat(timespec='microseconds'),
                "timezone": tz_name
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Error getting current time: {e}"}

async def convert_timezone(datetime_str: str, from_tz: str, to_tz: str) -> dict:
    """
    Converts a datetime string from one timezone to another using native zoneinfo.

    Args:
        datetime_str (str): The datetime string to convert (ISO format recommended).
        from_tz (str): The IANA timezone string for the input (e.g., "America/New_York").
        to_tz (str): The IANA timezone string for the output (e.g., "Europe/Berlin").

    Returns:
        dict: A dictionary representing the JSON response.
    """
    try:
        await asyncio.sleep(0.01)

        source_tz = ZoneInfo(from_tz)
        target_tz = ZoneInfo(to_tz)

        try:
            # Parse the string
            dt_obj = datetime.fromisoformat(datetime_str)
            
            # If naive (no TZ info), attach the source_tz
            if dt_obj.tzinfo is None:
                dt_obj = dt_obj.replace(tzinfo=source_tz)
            else:
                # If already aware, ensure it's normalized to the source_tz
                dt_obj = dt_obj.astimezone(source_tz)
                
        except ValueError:
            return {
                "status": "error", 
                "message": f"Could not parse datetime: '{datetime_str}'. Use 'YYYY-MM-DD HH:MM:SS'."
            }

        converted_dt = dt_obj.astimezone(target_tz)

        return {
            "status": "success",
            "data": {
                "original_datetime": datetime_str,
                "original_timezone": from_tz,
                "converted_datetime": converted_dt.isoformat(timespec='microseconds'),
                "converted_timezone": to_tz
            }
        }
    except ZoneInfoNotFoundError as e:
        return {"status": "error", "message": f"Unknown timezone provided: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Conversion error: {e}"}

async def calculate_date_difference(date1_str: str, date2_str: str, unit: str = "days") -> dict:
    """
    Calculates the difference between two dates in specified units.

    Args:
        date1_str (str): The first date string.
        date2_str (str): The second date string.
        unit (str, optional): "days", "hours", "minutes", or "seconds". Defaults to "days".

    Returns:
        dict: A dictionary with the calculated difference.
    """
    try:
        await asyncio.sleep(0.01)

        dt1 = datetime.fromisoformat(date1_str)
        dt2 = datetime.fromisoformat(date2_str)

        # Handle naive vs aware comparison safely
        if dt1.tzinfo != dt2.tzinfo:
            if dt1.tzinfo is None: dt1 = dt1.replace(tzinfo=dt_timezone.utc)
            if dt2.tzinfo is None: dt2 = dt2.replace(tzinfo=dt_timezone.utc)

        delta = abs(dt1 - dt2)

        if unit == "days":
            # Use total_seconds to get fractional days if time is included
            difference = delta.total_seconds() / 86400
        elif unit == "hours":
            difference = delta.total_seconds() / 3600
        elif unit == "minutes":
            difference = delta.total_seconds() / 60
        elif unit == "seconds":
            difference = delta.total_seconds()
        else:
            return {"status": "error", "message": f"Unsupported unit: '{unit}'"}

        return {
            "status": "success",
            "data": {
                "date1": date1_str,
                "date2": date2_str,
                "difference": round(difference, 4),
                "unit": unit
            }
        }
    except ValueError as e:
        return {"status": "error", "message": f"Parse error: {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Calculation error: {e}"}

async def time_utils(action: str, timezone: str = "local", datetime_str: str = "", from_tz: str = "UTC", to_tz: str = "UTC", date1: str = "", date2: str = "", unit: str = "days") -> str:
    """
    Dispatcher tool for time-related operations including current time, conversion, and differences.

    Args:
        action (str): The operation to perform ('get_time', 'convert', 'difference').
        timezone (str): IANA timezone for 'get_time'.
        datetime_str (str): ISO date string for 'convert'.
        from_tz (str): Source IANA timezone for 'convert'.
        to_tz (str): Target IANA timezone for 'convert'.
        date1 (str): First ISO date string for 'difference'.
        date2 (str): Second ISO date string for 'difference'.
        unit (str): Unit of measurement for 'difference' ('days', 'hours', etc.).

    Returns:
        str: A JSON string containing the result of the time operation.
    """
    result = {"status": "error", "message": "Invalid time action specified."}

    if action == "get_time":
        result = await get_current_time(timezone)
    elif action == "convert":
        result = await convert_timezone(datetime_str, from_tz, to_tz)
    elif action == "difference":
        result = await calculate_date_difference(date1, date2, unit)

    return json.dumps(result, indent=2)
