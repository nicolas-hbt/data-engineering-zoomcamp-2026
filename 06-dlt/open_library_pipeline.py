"""Template for building a `dlt` pipeline to ingest data from a REST API."""

import dlt
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig


@dlt.source
def open_library_rest_api_source():
    """Define dlt resources from REST API endpoints."""
    config: RESTAPIConfig = {
        "client": {
            "base_url": "http://openlibrary.org/api/",
            # Open Library API is public, no authentication required for basic endpoints
            # For authenticated endpoints, use cookie-based auth (see docs)
        },
        "resources": [
            {
                "name": "books",
                "endpoint": {
                    "path": "books",
                    "method": "GET",
                    "params": {
                        # bibkeys is required - using a sample ISBN
                        # Format: ISBN:0451526538 or multiple: ISBN:0451526538,ISBN:0140328726
                        "bibkeys": "ISBN:0451526538",
                        "format": "json",  # Request JSON format instead of default javascript
                        "jscmd": "data",  # Get full data instead of viewapi
                    },
                    # The API returns a dict with ISBN keys, extract all values
                    "data_selector": "$.*",
                },
            }
        ],
    }

    yield from rest_api_resources(config)


pipeline = dlt.pipeline(
    pipeline_name='open_library_pipeline',
    destination='duckdb',
    # `refresh="drop_sources"` ensures the data and the state is cleaned
    # on each `pipeline.run()`; remove the argument once you have a
    # working pipeline.
    refresh="drop_sources",
    # show basic progress of resources extracted, normalized files and load-jobs on stdout
    progress="log",
)


if __name__ == "__main__":
    load_info = pipeline.run(open_library_rest_api_source())
    print(load_info)  # noqa: T201
