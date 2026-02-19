"""@bruin

# TODO: Set the asset name (recommended pattern: schema.asset_name).
# - Convention in this module: use an `ingestion.` schema for raw ingestion tables.
name: ingestion.trips

# TODO: Set the asset type.
# Docs: https://getbruin.com/docs/bruin/assets/python
type: python

# TODO: Pick a Python image version (Bruin runs Python in isolated environments).
# Example: python:3.11
image: python:3.11

# TODO: Set the connection.
connection: duckdb-default

# TODO: Choose materialization (optional, but recommended).
# Bruin feature: Python materialization lets you return a DataFrame (or list[dict]) and Bruin loads it into your destination.
# This is usually the easiest way to build ingestion assets in Bruin.
# Alternative (advanced): you can skip Bruin Python materialization and write a "plain" Python asset that manually writes
# into DuckDB (or another destination) using your own client library and SQL. In that case:
# - you typically omit the `materialization:` block
# - you do NOT need a `materialize()` function; you just run Python code
# Docs: https://getbruin.com/docs/bruin/assets/python#materialization
materialization:
  # TODO: choose `table` or `view` (ingestion generally should be a table)
  type: table
  # TODO: pick a strategy.
  # suggested strategy: append
  strategy: append

# TODO: Define output columns (names + types) for metadata, lineage, and quality checks.
# Tip: mark stable identifiers as `primary_key: true` if you plan to use `merge` later.
# Docs: https://getbruin.com/docs/bruin/assets/columns
columns:
  - name: pickup_datetime
    type: timestamp
    description: "When the meter was engaged"
  - name: dropoff_datetime
    type: timestamp
    description: "When the meter was disengaged"

@bruin"""

import json
import os
import pandas as pd
import requests
from io import BytesIO  # For read_csv
from glob import glob

# TODO: Only implement `materialize()` if you are using Bruin Python materialization.
# If you choose the manual-write approach (no `materialization:` block), remove this function and implement ingestion
# as a standard Python script instead.


DTYPES = {
    "VendorID": "Int64",
    "RatecodeID": "Int64",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "passenger_count": "Int64",
    "payment_type": "Int64",
    "trip_type": "Int64",           # green only (ok if missing)
    "store_and_fwd_flag": "string",
    "trip_distance": "float64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "ehail_fee": "float64",         # green only (ok if missing)
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64",
    # FHV
    "dispatching_base_num": "string",
    "PUlocationID": "Int64",
    "DOlocationID": "Int64",
    "SR_Flag": "string",
    "Affiliated_base_number": "string",
}

PARSE_DATES = [
    # yellow
    "tpep_pickup_datetime", "tpep_dropoff_datetime",
    # green
    "lpep_pickup_datetime", "lpep_dropoff_datetime",
    # fhv
    "pickup_datetime", "dropOff_datetime",
]

TARGET_COLUMNS = [
    "data_file_month",
    "service_type",
    "trip_id",
    "vendor_id",
    "pickup_datetime",
    "dropoff_datetime",
    "pickup_location_id",
    "dropoff_location_id",
    "trip_distance",
    "passenger_count",
    "ratecode_id",
    "store_and_fwd_flag",
    "payment_type",
    "fare_amount",
    "extra",
    "mta_tax",
    "tip_amount",
    "tolls_amount",
    "improvement_surcharge",
    "total_amount",
    "trip_type",
    "ehail_fee",
    "dispatching_base_num",
    "affiliated_base_number",
    "sr_flag",
    "extracted_at",
]

def read_taxi_file_from_bytes(content: bytes, service: str) -> pd.DataFrame:
    """Adapted read_taxi_file for in-memory bytes (requests response)"""
    df = pd.read_csv(
        BytesIO(content),
        compression="gzip",
        dtype=DTYPES,
        parse_dates=PARSE_DATES,
        low_memory=False,
    )
    
    # Add service_type
    df["service_type"] = service
    
    # Normalize datetime columns
    if "tpep_pickup_datetime" in df.columns:
        df["pickup_datetime"] = df["tpep_pickup_datetime"]
        df["dropoff_datetime"] = df["tpep_dropoff_datetime"]
    elif "lpep_pickup_datetime" in df.columns:
        df["pickup_datetime"] = df["lpep_pickup_datetime"]
        df["dropoff_datetime"] = df["lpep_dropoff_datetime"]
    elif "pickup_datetime" in df.columns:
        df["pickup_datetime"] = df["pickup_datetime"]  # FHV already normalized
        df["dropoff_datetime"] = df["dropOff_datetime"] if "dropOff_datetime" in df.columns else pd.NA
    
    # Normalize location columns
    df["pickup_location_id"] = df.get("PULocationID") or df.get("PUlocationID")
    df["dropoff_location_id"] = df.get("DOLocationID") or df.get("DOlocationID")
    
    # Normalize other columns
    df["vendor_id"] = df.get("VendorID")
    df["ratecode_id"] = df.get("RatecodeID")
    
    if "SR_Flag" in df.columns:
        df["sr_flag"] = pd.to_numeric(df["SR_Flag"], errors="coerce").astype("Int64")
    else:
        df["sr_flag"] = pd.NA
    
    df["affiliated_base_number"] = df.get("Affiliated_base_number")
    df["dispatching_base_num"] = df.get("dispatching_base_num")
    
    # Null out green-only columns for other services
    if service != "green":
        df["trip_type"] = pd.NA
        df["ehail_fee"] = pd.NA
    
    df["extracted_at"] = datetime.utcnow()
    
    return df

def add_trip_id(df: pd.DataFrame) -> pd.DataFrame:
    """Generate trip_id from key fields"""
    key_cols = ["service_type", "pickup_datetime", "dropoff_datetime", 
                "pickup_location_id", "dropoff_location_id", "fare_amount"]
    
    # Fill missing keys with NA string for hashing
    for col in key_cols:
        if col not in df.columns:
            df[col] = pd.NA
    
    key_str = df[key_cols].astype(str).agg('|'.join, axis=1).str.encode('utf-8')
    df["trip_id"] = [hashlib.sha256(x).hexdigest()[:32] for x in key_str]  # Shortened for varchar
    return df

def materialize():
    vars_ = json.loads(os.environ.get("BRUIN_VARS", "{}"))
    taxi_types = vars_.get("taxi_types", ["green"])
    
    start_date = os.environ["BRUIN_START_DATE"]  # "2020-01-01"
    end_date = os.environ["BRUIN_END_DATE"]      # "2020-01-31"
    
    BASE_URL = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download"
    
    year = start_date[:4]
    month = start_date[5:7]
    data_file_month = f"{year}-{month}"
    
    dfs = []
    
    for service in taxi_types:
        csv_file_name = f"{service}_tripdata_{year}-{month}.csv.gz"
        url = f"{BASE_URL}/{service}/{csv_file_name}"
        
        print(f"Fetching {service}: {url}")  # Debug log
        
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Use the unified reader
        df = read_taxi_file_from_bytes(response.content, service)
        df = add_trip_id(df)
        
        # Add year/month metadata for lineage
        df["data_file_month"] = data_file_month
        
        # Select only target columns (fills missing as NA)
        available_cols = [col for col in TARGET_COLUMNS if col in df.columns]
        df = df[available_cols]  # Keep your metadata
        
        dfs.append(df)
    
    if not dfs:
        return pd.DataFrame(columns=TARGET_COLUMNS)
    
    df = pd.concat(dfs, ignore_index=True)
    
    # Reorder to match schema + your extras at end
    cols = TARGET_COLUMNS
    df = df.reindex(columns=cols)
    
    return df