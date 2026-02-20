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
connection: gcp-default

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

# TODO: Add imports needed for your ingestion (e.g., pandas, requests).
# - Put dependencies in the nearest `requirements.txt` (this template has one at the pipeline root).
# Docs: https://getbruin.com/docs/bruin/assets/python
import os
import json
import pandas as pd
from datetime import datetime


# TODO: Only implement `materialize()` if you are using Bruin Python materialization.
# If you choose the manual-write approach (no `materialization:` block), remove this function and implement ingestion
# as a standard Python script instead.
def materialize():

  # Get the start and end dates from Bruin environment variables
  start_date = os.getenv('BRUIN_START_DATE')
  end_date = os.getenv('BRUIN_END_DATE')
  
  # Read pipeline variables
  taxi_types = json.loads(os.getenv('BRUIN_VARS')).get('taxi_types', [])

  # Initialize an empty list to hold DataFrames
  dataframes = []

  # Generate source endpoints based on taxi types and date range
  for taxi_type in taxi_types:
    # Example endpoint generation (modify as needed)
    endpoint = f"https://api.example.com/taxis/{taxi_type}?start_date={start_date}&end_date={end_date}"
    
    # Fetch data (this is a placeholder; implement actual data fetching)
    response = pd.read_json(endpoint)
    
    # Add extracted_at column
    response['extracted_at'] = datetime.now()
    
    # Append the DataFrame to the list
    dataframes.append(response)

  # Concatenate all DataFrames into a single DataFrame
  final_dataframe = pd.concat(dataframes, ignore_index=True)

  return final_dataframe
