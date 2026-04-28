# convert.py
import json

async def convert(
    value: float,
    from_unit: str,
    to_unit: str
) -> dict:
    """
    Calculates the conversion of a given value from one unit to another,
    supporting distance, weight, and volume conversions between metric and imperial systems.

    Args:
        value (float): The numeric quantity to be converted.
                       Example: 100
        from_unit (str): The unit of the input value.
                         Supported distance units: 'mm', 'cm', 'm', 'km', 'in', 'ft', 'yd', 'mi'
                         Supported weight units: 'mg', 'g', 'kg', 'oz', 'lb'
                         Supported volume units: 'ml', 'l', 'floz', 'cup', 'pt', 'qt', 'gal'
                         Examples: "km", "lb", "gallons"
        to_unit (str): The desired unit for the converted value.
                       Must be in the same category as `from_unit`.
                       Examples: "miles", "kg", "liters"

    Returns:
        dict: A dictionary representing the JSON response.
              The structure will always contain a 'status' key.

              On **success**, the JSON will have the following structure:
              ```json
              {
                "status": "success",
                "data": {
                  "original_value": 10.0,
                  "from_unit": "km",
                  "converted_value": 6.21371,
                  "to_unit": "mi"
                }
              }
              ```
              `converted_value` will be a float.

              On **failure** (e.g., invalid input types, unsupported units,
              unit category mismatch), the JSON will have the following structure:
              ```json
              {
                "status": "error",
                "message": "A descriptive error message indicating what went wrong."
              }
              ```
    """
    # Define conversion factors relative to a common base unit (e.g., meter, gram, liter)
    # Unit: Factor to convert TO the base unit
    # Unit: Factor to convert FROM the base unit
    units = {
        "distance": {
            "mm": 0.001,    # mm to m
            "cm": 0.01,     # cm to m
            "m": 1.0,       # meter to m
            "km": 1000.0,   # km to m
            "in": 0.0254,   # inch to m
            "ft": 0.3048,   # foot to m
            "yd": 0.9144,   # yard to m
            "mi": 1609.34,  # mile to m
        },
        "weight": {
            "mg": 0.001,    # mg to g
            "g": 1.0,       # gram to g
            "kg": 1000.0,   # kg to g
            "oz": 28.3495,  # ounce to g
            "lb": 453.592,  # pound to g
        },
        "volume": {
            "ml": 0.001,    # ml to l
            "l": 1.0,       # liter to l
            "floz": 0.0295735, # US fluid ounce to l
            "cup": 0.236588,   # US cup to l
            "pt": 0.473176,    # US pint to l
            "qt": 0.946353,    # US quart to l
            "gal": 3.78541,    # US gallon to l
        }
    }

    try:
        value = float(value)
        from_unit = from_unit.lower().strip()
        to_unit = to_unit.lower().strip()

        # Find the category for from_unit and to_unit
        from_category = None
        to_category = None

        for category, category_units in units.items():
            if from_unit in category_units:
                from_category = category
            if to_unit in category_units:
                to_category = category

        if from_category is None:
            return {"status": "error", "message": f"Unsupported 'from_unit': {from_unit}"}
        if to_category is None:
            return {"status": "error", "message": f"Unsupported 'to_unit': {to_unit}"}

        if from_category != to_category:
            return {"status": "error", "message": f"Unit category mismatch: Cannot convert {from_unit} (a {from_category} unit) to {to_unit} (a {to_category} unit)."}

        # Perform the conversion
        # 1. Convert from_unit to base unit of its category
        value_in_base_unit = value * units[from_category][from_unit]
        
        # 2. Convert from base unit to to_unit
        # Division by zero check in case of a factor being 0 (though not expected with current factors)
        if units[to_category][to_unit] == 0:
             return {"status": "error", "message": f"Conversion factor for '{to_unit}' is zero, which is not supported."}
        
        converted_value = value_in_base_unit / units[to_category][to_unit]

        return {
            "status": "success",
            "data": {
                "original_value": value,
                "from_unit": from_unit,
                "converted_value": converted_value,
                "to_unit": to_unit
            }
        }

    except (TypeError, ValueError) as e:
        return {
            "status": "error",
            "message": f"Invalid input value or unit format. Ensure 'value' is a number and units are strings. Error: {e}"
        }
    except Exception as e:
        # Catch any other unexpected errors during calculation
        return {
            "status": "error",
            "message": f"An unexpected error occurred during conversion: {e}"
        }
