import sqlite3
import json
import os
import unicodedata

def normalize_to_ascii(text: str) -> str:
    """
    Converts Unicode characters to their closest ASCII equivalents 
    (e.g., 'Î' becomes 'I') and removes non-printable characters.
    """
    if not text:
        return ""
    # Decompose unicode characters (NFD)
    # This separates 'Î' into 'I' and the circumflex accent
    normalized = unicodedata.normalize('NFD', text)
    # Filter out non-spacing mark characters and keep only printable ASCII
    result = "".join(
        c for c in normalized 
        if unicodedata.category(c) != 'Mn' 
        and (32 <= ord(c) <= 126)
    )
    return result

async def geo(query: str) -> str:
    """
    Standardized geographic lookup tool for global cities, towns, and major landmarks.
    
    This tool resolves location names into precise coordinates and metadata. It handles 
    both populated places and significant physical features (Dams, Canyons, Monuments, 
    Mountains). It supports disambiguation via comma-separated context (State or Country).
    
    Usage Examples:
    - Landmarks: 'Hoover Dam', 'Eiffel Tower', 'Grand Canyon'
    - Ambiguous Cities: 'Paris, TX' or 'Paris, France'
    - General Search: 'Austin', 'Tokyo', 'Mount Everest'
    
    Args:
        query (str): The name of the city or landmark. Optional: append a comma and 
                     region/country code for better accuracy.
                     
    Returns:
        str: A JSON-encoded string containing 'status' and 'data'.
             The 'data' object includes latitude, longitude, city, state, country, 
             population, elevation (meters), timezone, and feature type.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "geo", "geo.db")

    if not os.path.exists(db_path):
        db_path = "geo/geo.db"

    if not os.path.exists(db_path):
        return json.dumps({
            "tool": "geo",
            "result": json.dumps({"status": "error", "message": "Database missing"})
        })

    raw_input = query.strip()
    if "," in raw_input:
        parts = raw_input.split(",")
        name_term = parts[0].strip().lower()
        suffix_term = parts[1].strip().upper()
    else:
        name_term = raw_input.lower()
        suffix_term = None

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        sql = """
        SELECT 
            p.name, 
            COALESCE(r.region_name, 'N/A') as state, 
            COALESCE(ct.country_name, 'N/A') as country,
            p.latitude, 
            p.longitude, 
            p.population,
            CASE 
                WHEN p.elevation IS NULL OR p.elevation = '' OR p.elevation <= -999 THEN 0 
                ELSE p.elevation 
            END as elev,
            p.timezone,
            COALESCE(f.feature_name, 'City-Area') as f_name,
            (
                CASE 
                    WHEN LOWER(p.name) = ? THEN 1500 
                    WHEN LOWER(p.name) LIKE ? THEN 800
                    ELSE 0 
                END +
                CASE 
                    WHEN ? IS NOT NULL AND (p.admin1_code = ? OR p.country_code = ?) THEN 5000
                    ELSE 0 
                END +
                CASE 
                    WHEN p.feature_class IN ('P', 'T') THEN 200
                    ELSE 0
                END +
                ((LENGTH(p.alternatenames) - LENGTH(REPLACE(p.alternatenames, ',', '')) + 1) * 10) +
                (CAST(p.population AS INTEGER) / 5000)
            ) AS rank
        FROM places p
        LEFT JOIN regions r ON (p.country_code || '.' || p.admin1_code) = r.concat_code
        LEFT JOIN countries ct ON p.country_code = ct.iso_alpha2
        LEFT JOIN feature_dict f ON p.feature_code = f.feature_code
        WHERE (LOWER(p.name) LIKE ? OR LOWER(p.alternatenames) LIKE ?)
        ORDER BY rank DESC
        LIMIT 1;
        """
        
        params = (name_term, f"{name_term}%", suffix_term, suffix_term, suffix_term, f"%{name_term}%", f"%{name_term}%")
        cursor.execute(sql, params)
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Helper for safe numeric conversion
            def safe_num(val, default=0):
                if val is None or str(val).strip() == "": return default
                try: return type(default)(float(val))
                except: return default

            # Apply ASCII normalization to all text fields
            data = {
                "latitude": safe_num(row[3], 0.0),
                "longitude": safe_num(row[4], 0.0),
                "city": normalize_to_ascii(row[0]),
                "state": normalize_to_ascii(row[1]),
                "country": normalize_to_ascii(row[2]),
                "population": safe_num(row[5], 0),
                "elevation": safe_num(row[6], 0),
                "timezone": normalize_to_ascii(row[7]) if row[7] else "UTC",
                "type": normalize_to_ascii(row[8]).replace("/", "-")
            }
            
            # ensure_ascii=True is the default for json.dumps, 
            # but our normalization makes it physically impossible to have non-ASCII anyway.
            return json.dumps({
                "tool": "geo",
                "result": json.dumps({"status": "success", "data": data})
            })
        else:
            return json.dumps({"tool": "geo", "result": json.dumps({"status": "error", "message": "No match"})})

    except Exception as e:
        return json.dumps({"tool": "geo", "result": json.dumps({"status": "error", "message": str(e)})})

if __name__ == "__main__":
    print(geo("Eiffel Tower"))
    print(geo("Paris, TX"))
    print(geo("St Louis, MO"))
