"""dlt pipeline to ingest NYC taxi data from a REST API."""

import os

import dlt
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig

# Cap number of records for a full run (e.g. for dev/testing). Set to 0 or unset for no cap.
# Example: TAXI_PIPELINE_MAX_RECORDS=5000 for a quick run (~5 pages).
MAX_RECORDS = int(os.environ.get("TAXI_PIPELINE_MAX_RECORDS", "0") or "0")
PAGE_SIZE = 1000

# DuckDB file path. Default: "taxi_pipeline.duckdb" in the current working directory.
# Example: TAXI_PIPELINE_DUCKDB=data/nyc.duckdb
DUCKDB_PATH = os.environ.get("TAXI_PIPELINE_DUCKDB", "taxi_pipeline.duckdb")


@dlt.source
def taxi_rest_api_source():
    """Define dlt resources for the NYC taxi REST API."""
    paginator: dict = {
        "type": "offset",
        "limit": PAGE_SIZE,
        "offset": 0,
        "stop_after_empty_page": True,
        "total_path": None,
    }
    if MAX_RECORDS > 0:
        # Stop after this many records (so the run finishes in a few minutes).
        paginator["maximum_offset"] = max(0, MAX_RECORDS - PAGE_SIZE)

    config: RESTAPIConfig = {
        "client": {
            "base_url": "https://us-central1-dlthub-analytics.cloudfunctions.net/data_engineering_zoomcamp_api",
        },
        "resource_defaults": {
            "endpoint": {
                "params": {
                    "limit": PAGE_SIZE,
                },
            },
        },
        "resources": [
            {
                "name": "nyc_taxi_trips",
                "endpoint": {
                    "path": "",
                    "method": "GET",
                    "paginator": paginator,
                },
            }
        ],
    }

    yield from rest_api_resources(config)


taxi_pipeline = dlt.pipeline(
    pipeline_name="taxi_pipeline",
    destination=dlt.destinations.duckdb(DUCKDB_PATH),
    refresh="drop_sources",
    progress="log",
)


if __name__ == "__main__":
    if MAX_RECORDS > 0:
        print(f"Limiting extract to {MAX_RECORDS} records (set TAXI_PIPELINE_MAX_RECORDS=0 for full run).")  # noqa: T201
    print(f"DuckDB database: {DUCKDB_PATH}")  # noqa: T201
    load_info = taxi_pipeline.run(taxi_rest_api_source())
    print(load_info)  # noqa: T201

