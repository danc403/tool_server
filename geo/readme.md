\# Geographic Engine



This directory contains the localized geographic database and the build tools required to maintain it. This system provides offline-capable geographic resolution for global cities and major landmarks.



\## Components



\### 1. Geographic Database (geo.db)

A pre-compiled SQLite database containing:

\- \*\*Cities \& Towns\*\*: Global coverage with population, elevation, and timezone data.

\- \*\*Landmarks\*\*: Major physical and cultural features (Dams, Canyons, Monuments, etc.).

\- \*\*Metadata\*\*: Resolved state and country names, normalized to printable ASCII.



\### 2. Database Reconstruction Engine (geo\_db.py)

If the database needs to be updated or reconstructed, `geo\_db.py` handles the entire pipeline:

\- \*\*Download\*\*: Fetches the latest `allCountries.zip` from GeoNames.

\- \*\*Extraction\*\*: Unpacks the raw text data.

\- \*\*Filtering\*\*: Applies specialized tier-based filtering to keep the database size efficient while retaining major global locations.

\- \*\*Normalization\*\*: Builds a custom feature dictionary for human-readable landmark types.



\## Installation \& Updates



To rebuild the database from scratch, ensure you have an active internet connection and run:



```bash

python3 geo\_db.py



