import sqlite3
import zipfile
import os
import requests
import sys
import unicodedata

# File Configuration
DB_FILE = "geo.db"
CITIES_ZIP = "cities5000.zip"
ALL_ZIP = "allCountries.zip"
CITIES_TXT = "cities5000.txt"
ALL_TXT = "allCountries.txt"
REGIONS_TXT = "admin1CodesASCII.txt"
COUNTRIES_TXT = "countryInfo.txt"

# Download URLs
URLS = {
    CITIES_ZIP: "https://download.geonames.org/export/dump/cities5000.zip",
    ALL_ZIP: "https://download.geonames.org/export/dump/allCountries.zip",
    REGIONS_TXT: "https://download.geonames.org/export/dump/admin1CodesASCII.txt",
    COUNTRIES_TXT: "https://download.geonames.org/export/dump/countryInfo.txt"
}

# SLIDING SCALE FILTERS
TIER_1 = {'OPRA', 'PAL', 'AMTH', 'STDM', 'MUS', 'UNIV', 'THTR', 'CH', 'TMPL', 'MSTY', 'ZOO'}
T1_THRESH = 5
# UPDATED: Added DAM to TIER_2 and confirmed T2_THRESH is inclusive
TIER_2 = {'AIRP', 'PRT', 'BDG', 'TNL', 'AIRB', 'RSTN', 'DAM'}
T2_THRESH = 1
TIER_3 = {'BLDG', 'TOWR', 'MNMT', 'WALL', 'FT', 'CSTL'}
T3_THRESH = 20
TIER_4 = {'MTS', 'CNYN', 'SEA', 'LKC', 'VLC', 'ISL'}
T4_THRESH = 15

# THE DEFINITIVE GEONAMES FEATURE DICTIONARY
FEATURE_DICTIONARY = {
    'ADMF': 'Administrative Facility',
    'AGRF': 'Agricultural Facility',
    'AIRB': 'Airbase',
    'AIRP': 'Airport',
    'AMTH': 'Amphitheater',
    'ANS': 'Ancient Site',
    'AQW': 'Aqueduct',
    'ARCH': 'Arch',
    'ASTR': 'Astronomical Station',
    'ASYL': 'Asylum',
    'ATHF': 'Athletic Field',
    'ATM': 'Automatic Teller Machine',
    'BCN': 'Beacon',
    'BDG': 'Bridge',
    'BLDG': 'Building',
    'BOA': 'Boat Ramp',
    'BP': 'Boundary Marker',
    'BRKS': 'Barracks',
    'BRKW': 'Breakwater',
    'BST': 'Bust (Statue)',
    'BSR': 'Boarding House',
    'CMPT': 'Campsite',
    'CH': 'Church',
    'CHNL': 'Channel Marker',
    'CHTX': 'Customs House',
    'CSTL': 'Castle',
    'CTH': 'Courthouse',
    'CTRS': 'Cultural Center',
    'DAM': 'Dam',
    'DYKE': 'Dyke',
    'FCL': 'Facility',
    'FIGE': 'Figurine',
    'FISH': 'Fish Farm',
    'FT': 'Fort',
    'FY': 'Ferry Terminal',
    'GATE': 'Gate',
    'GULF': 'Golf Course',
    'HSE': 'House',
    'HSEC': 'Country House',
    'HSHD': 'Household',
    'HSP': 'Hospital',
    'HSPC': 'Clinic',
    'HSPD': 'Dispensary',
    'HSPL': 'Leper Colony',
    'HSTS': 'Historical Site',
    'HTL': 'Hotel',
    'INSM': 'Military Installation',
    'ITTR': 'Research Station',
    'LIBR': 'Library',
    'LTHS': 'Lighthouse',
    'MEML': 'Memorial',
    'ML': 'Mill',
    'MLM': 'Military Mint',
    'MLSW': 'Sawmill',
    'MNMT': 'Monument',
    'MOLE': 'Mole',
    'MOSQ': 'Mosque',
    'MSTY': 'Monastery',
    'MUS': 'Museum',
    'NOV': 'Novitiate',
    'OBLI': 'Obelisk',
    'OBS': 'Observatory',
    'OILR': 'Oil Refinery',
    'OPRA': 'Opera House',
    'PAL': 'Palace',
    'PAG': 'Pagoda',
    'PGW': 'Pilgrim Way',
    'PO': 'Post Office',
    'PP': 'Police Station',
    'PPQ': 'Quarantine Station',
    'PRN': 'Prison',
    'PRNK': 'Reformatory',
    'PRT': 'Port',
    'PS': 'Power Station',
    'PSH': 'Hydroelectric Station',
    'PSTP': 'Post Stop',
    'PYR': 'Pyramid',
    'PYRS': 'Pyramids',
    'QNCRY': 'Quarry',
    'RCNF': 'Recreation Facility',
    'RECG': 'Radio-Television Gaon',
    'RECO': 'Radio-Television Office',
    'RECR': 'Radio-Television Receiver',
    'RECS': 'Radio-Television Station',
    'RECT': 'Radio-Television Tower',
    'RGN': 'Religious Site',
    'RLG': 'Religious Center',
    'RLGR': 'Retreat',
    'RSC': 'Research Center',
    'RSTN': 'Railroad Station',
    'RSTP': 'Railroad Stop',
    'RUIN': 'Ruin',
    'SCH': 'School',
    'SCHC': 'College',
    'SCHL': 'Language School',
    'SCHM': 'Military School',
    'SCHN': 'Nursing School',
    'SCHT': 'Technical School',
    'SHRN': 'Shrine',
    'STDM': 'Stadium',
    'STG': 'Stele',
    'STNE': 'Stone',
    'STPS': 'Steps',
    'SWT': 'Sewage Treatment Plant',
    'SYN': 'Synagogue',
    'THTR': 'Theater',
    'TMPL': 'Temple',
    'TNL': 'Tunnel',
    'TNLN': 'Natural Tunnel',
    'TOWR': 'Tower',
    'TRB': 'Tribunal',
    'UNIV': 'University',
    'WALL': 'Wall',
    'WALLA': 'Ancient Wall',
    'WTRW': 'Water Works',
    'ZOO': 'Zoo',
    'CNYN': 'Canyon',
    'CAPE': 'Cape',
    'GEYS': 'Geyser',
    'ISL': 'Island',
    'ISLS': 'Islands',
    'LKC': 'Lake Center',
    'MTS': 'Mountains',
    'MT': 'Mountain',
    'PK': 'Peak',
    'VLC': 'Volcano',
    'WTRF': 'Waterfall',
    'PPL': 'Populated Place',
    'PPLA': 'Seat of Government',
    'PPLC': 'Capital',
    'PPLG': 'Seat of Government',
    'PPLX': 'Section of Populated Place'
}

def normalize_to_ascii(text: str) -> str:
    """
    Converts Unicode characters to their closest ASCII equivalents 
    (e.g., 'Î' becomes 'I') and removes non-printable characters.
    """
    if not text:
        return ""
    normalized = unicodedata.normalize('NFD', text)
    result = "".join(
        c for c in normalized 
        if unicodedata.category(c) != 'Mn' 
        and (32 <= ord(c) <= 126)
    )
    return result

def build_db():
    # --- STEP 1: DOWNLOADS ---
    print("STEP 1: Checking all source files...")
    for filename, url in URLS.items():
        if not os.path.exists(filename):
            print(f"Downloading {filename}...")
            r = requests.get(url, stream=True)
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=131072):
                    f.write(chunk)
        else:
            print(f"Found {filename}.")

    # --- STEP 2: EXTRACTIONS ---
    print("\nSTEP 2: Extracting zip files...")
    for z_file, t_file in [(CITIES_ZIP, CITIES_TXT), (ALL_ZIP, ALL_TXT)]:
        if not os.path.exists(t_file):
            print(f"Extracting {t_file}...")
            with zipfile.ZipFile(z_file, 'r') as z:
                z.extract(t_file)
        else:
            print(f"Verified {t_file} exists.")

    # --- STEP 3: CREATE TABLES ---
    print("\nSTEP 3: Creating database tables...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS places;
        DROP TABLE IF EXISTS regions;
        DROP TABLE IF EXISTS countries;
        DROP TABLE IF EXISTS feature_dict;

        CREATE TABLE countries (
            iso_alpha2 TEXT PRIMARY KEY,
            country_name TEXT
        );

        CREATE TABLE regions (
            concat_code TEXT PRIMARY KEY,
            region_name TEXT
        );

        CREATE TABLE feature_dict (
            feature_code TEXT PRIMARY KEY,
            feature_name TEXT
        );

        CREATE TABLE places (
            geonameid INTEGER PRIMARY KEY,
            name TEXT,
            asciiname TEXT COLLATE NOCASE,
            alternatenames TEXT,
            latitude REAL,
            longitude REAL,
            feature_class TEXT,
            feature_code TEXT,
            country_code TEXT,
            cc2 TEXT,
            admin1_code TEXT,
            admin2_code TEXT,
            admin3_code TEXT,
            admin4_code TEXT,
            population INTEGER,
            elevation INTEGER,
            dem INTEGER,
            timezone TEXT,
            modification_date TEXT,
            FOREIGN KEY (feature_code) REFERENCES feature_dict(feature_code)
        );
        CREATE INDEX idx_ascii ON places(asciiname);
        CREATE INDEX idx_fcode ON places(feature_code);
    """)

    # --- STEP 4: POPULATE LOOKUPS ---
    print("\nSTEP 4: Populating Lookup tables (Normalized)...")
    
    # Countries
    with open(COUNTRIES_TXT, 'r', encoding='utf-8') as f:
        c_batch = []
        for l in f:
            if not l.startswith('#') and l.strip():
                p = l.split('\t')
                c_batch.append((p[0], normalize_to_ascii(p[4])))
        cursor.executemany("INSERT INTO countries VALUES (?,?)", c_batch)

    # Regions
    with open(REGIONS_TXT, 'r', encoding='utf-8') as f:
        r_batch = []
        for l in f:
            if l.strip():
                p = l.split('\t')
                r_batch.append((p[0], normalize_to_ascii(p[1])))
        cursor.executemany("INSERT INTO regions VALUES (?,?)", r_batch)

    # Features
    f_batch = list(FEATURE_DICTIONARY.items())
    cursor.executemany("INSERT INTO feature_dict VALUES (?,?)", f_batch)
    
    conn.commit()

    # --- STEP 5: IMPORT CITIES 5000 ---
    print("\nSTEP 5: Importing Cities 5000 (Normalized)...")
    total_cities = 0
    batch = []
    with open(CITIES_TXT, 'r', encoding='utf-8') as f:
        for line in f:
            p = line.split('\t')
            if len(p) < 19: continue
            
            # Normalize Name (1), Asciiname (2), and Timezone (17)
            processed = [col.strip() for col in p]
            processed[1] = normalize_to_ascii(processed[1])
            processed[2] = normalize_to_ascii(processed[2])
            processed[17] = normalize_to_ascii(processed[17])
            
            batch.append(processed)
            if len(batch) >= 10000:
                cursor.executemany("INSERT OR IGNORE INTO places VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                conn.commit()
                total_cities += len(batch)
                print(f"Cities batch complete: {total_cities} total.")
                batch = []
        if batch:
            cursor.executemany("INSERT OR IGNORE INTO places VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
            conn.commit()
            total_cities += len(batch)

    # --- STEP 6: IMPORT LANDMARKS FROM ALL COUNTRIES ---
    print("\nSTEP 6: Importing Landmarks from All Countries (Normalized)...")
    total_landmarks = 0
    batch = []
    
    ALLOWED_CLASSES = {'S', 'P', 'T', 'H', 'L'}
    
    with open(ALL_TXT, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            p = line.split('\t')
            if len(p) < 19: continue
            
            f_class = p[6].strip()
            f_code = p[7].strip()
            
            if f_class not in ALLOWED_CLASSES:
                continue
                
            alt_names_raw = p[3].strip()
            alt_count = len(alt_names_raw.split(',')) if alt_names_raw else 0

            keep = False
            if f_code in TIER_1 and alt_count >= T1_THRESH: keep = True
            elif f_code in TIER_2 and alt_count >= T2_THRESH: keep = True
            elif f_code in TIER_3 and alt_count >= T3_THRESH: keep = True
            elif f_code in TIER_4 and alt_count >= T4_THRESH: keep = True

            if keep:
                processed = [col.strip() for col in p]
                processed[1] = normalize_to_ascii(processed[1])
                processed[2] = normalize_to_ascii(processed[2])
                processed[17] = normalize_to_ascii(processed[17])
                
                batch.append(processed)
                if len(batch) >= 10000:
                    cursor.executemany("INSERT OR IGNORE INTO places VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
                    conn.commit()
                    total_landmarks += len(batch)
                    print(f"Landmarks batch complete: {total_landmarks} added.")
                    batch = []
        if batch:
            cursor.executemany("INSERT OR IGNORE INTO places VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)
            conn.commit()
            total_landmarks += len(batch)

    conn.close()
    print(f"\nFinalized: {total_cities} cities and {total_landmarks} major landmarks stored.")

if __name__ == "__main__":
    build_db()
