# Module 2: Workflow Orchestration

## Overview
This module introduces workflow orchestration using Kestra, a modern orchestration platform for data pipelines. You'll learn to automate data workflows, schedule tasks, handle backfills, and deploy pipelines to the cloud (GCP).

---

## What is Workflow Orchestration?

### The Problem
Without an orchestrator, coordinating multiple tools in a data pipeline is tedious:
- Manual configuration of each tool
- Connecting APIs together manually
- No centralized monitoring or logging
- Difficult to handle failures and retries

### What an Orchestrator Provides

**1. Centralized Control**
- Tells independent tools how to work together
- Manages dependencies between tasks

**2. Logging & Monitoring**
- Tracks events happening inside and between tools
- Provides visibility into failures and successes

**3. Complex Orchestration Logic**
- Run tasks in parallel
- Loop through operations
- Conditional execution
- Error handling and retries

**4. Automation**
- Scheduled triggers (run at specific times)
- Event-driven triggers (run when data becomes available)
- No human intervention required

**Goal**: Supercharge existing data pipelines with automation, monitoring, and reliability.

---

## Why Kestra?

### Key Features

**Language Agnostic**
- Use multiple programming languages (Python, SQL, Shell, etc.)
- Pick the best language for each specific task
- Not limited to one language like some orchestrators

**Flexible Development Approaches**
- Code-based workflows (write YAML)
- No-code UI builders
- AI-assisted workflow generation
- Mix all approaches together

**Full Visibility**
- Real-time monitoring of workflow execution
- Built-in alerting and notifications
- Detailed execution logs
- Visual topology view of task dependencies

---

## Core Kestra Concepts

### Flow
A container for tasks and their orchestration logic. Think of it as a complete workflow definition.

```yaml
id: my_pipeline
namespace: zoomcamp
description: My first data pipeline
```

**Important**: `id` and `namespace` are immutable. To change them, you must create a new flow.

### Tasks
Individual steps within a flow. Tasks can be:
- Python scripts
- SQL queries
- HTTP requests
- File operations
- Shell commands

```yaml
tasks:
  - id: download_data
    type: io.kestra.plugin.core.http.Download
    uri: https://example.com/data.csv
```

### Inputs
Dynamic values passed to the flow at runtime. Similar to function parameters or Databricks widgets.

```yaml
inputs:
  - id: name
    type: STRING
    defaults: Will
  
  - id: columns_to_keep
    type: ARRAY
    itemType: STRING
    defaults:
      - brand
      - price
```

**Input Types**:
- `STRING`, `INT`, `FLOAT`, `BOOLEAN`
- `ARRAY`, `JSON`
- `SELECT` (dropdown choices, like dbutils.widgets)
- `DATE`, `DATETIME`

### Outputs
Pass data between tasks and flows.

```yaml
tasks:
  - id: generate_output
    type: io.kestra.plugin.core.debug.Return
    format: I was generated during this workflow.
  
  - id: use_output
    type: io.kestra.plugin.core.log.Log
    message: "Output value: {{ outputs.generate_output.value }}"
```

**Key Pattern**: Access outputs using `{{ outputs.<task_id>.<property> }}`

### Variables
Reusable key-value pairs across tasks.

```yaml
variables:
  welcome_message: "Hello, {{ inputs.name }}!"
  
tasks:
  - id: greet
    type: io.kestra.plugin.core.log.Log
    message: "{{ render(vars.welcome_message) }}"
```

### Triggers
Mechanisms to automatically start flow execution.

**Scheduled Trigger** (cron-based):
```yaml
triggers:
  - id: schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 10 * * *"  # Every day at 10:00 AM
    inputs:
      name: Sarah
```

**Event-Driven Trigger** (reacts to events):
```yaml
triggers:
  - id: file_watcher
    type: io.kestra.plugin.core.trigger.Flow
    conditions:
      - type: io.kestra.core.models.conditions.types.ExecutionStatusCondition
        in:
          - SUCCESS
```

### Plugin Defaults
Default values applied to all tasks of a given type within flows.

```yaml
pluginDefaults:
  - type: io.kestra.plugin.core.log.Log
    values:
      level: ERROR  # All log tasks will use ERROR level
```

### Concurrency
Control how many executions of a flow can run simultaneously.

```yaml
concurrency:
  behavior: FAIL  # Fail new executions if limit reached
  limit: 2        # Maximum 2 concurrent executions
```

### Labels
Metadata attached to executions for filtering and debugging.

```yaml
labels:
  dataset: yellow_taxi
  month: "{{ inputs.month }}"
  year: "{{ inputs.year }}"
```

**Benefits**:
- Filter executions without digging through logs
- Track which configuration was used
- Debug specific runs easily

---

## Complete Example Flow

```yaml
id: 01_hello_world
namespace: zoomcamp

inputs:
  - id: name
    type: STRING
    defaults: Will

concurrency:
  behavior: FAIL
  limit: 2

variables:
  welcome_message: "Hello, {{ inputs.name }}!"

tasks:
  - id: hello_message
    type: io.kestra.plugin.core.log.Log
    message: "{{ render(vars.welcome_message) }}"
  
  - id: generate_output
    type: io.kestra.plugin.core.debug.Return
    format: I was generated during this workflow.
  
  - id: sleep
    type: io.kestra.plugin.core.flow.Sleep
    duration: PT15S
  
  - id: log_output
    type: io.kestra.plugin.core.log.Log
    message: "This is an output: {{ outputs.generate_output.value }}"
  
  - id: goodbye_message
    type: io.kestra.plugin.core.log.Log
    message: "Goodbye, {{ inputs.name }}!"

pluginDefaults:
  - type: io.kestra.plugin.core.log.Log
    values:
      level: ERROR

triggers:
  - id: schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 10 * * *"
    inputs:
      name: Sarah
    disabled: true  # Enable when ready to schedule
```

---

## Orchestrating Python Code

### Running Python in Docker Containers

Kestra automatically spins up Docker containers to run your code, handling dependencies with UV.

```yaml
id: 02_python
namespace: zoomcamp

tasks:
  - id: collect_stats
    type: io.kestra.plugin.scripts.python.Script
    taskRunner:
      type: io.kestra.plugin.scripts.runner.docker.Docker
      containerImage: python:slim
    dependencies:
      - requests
      - kestra
    script: |
      from kestra import Kestra
      import requests
      
      def get_docker_image_downloads(image_name: str = "kestra/kestra"):
          """Queries Docker Hub API for image download count."""
          url = f"https://hub.docker.com/v2/repositories/{image_name}/"
          response = requests.get(url)
          data = response.json()
          downloads = data.get('pull_count', 'Not available')
          return downloads
      
      downloads = get_docker_image_downloads()
      
      # Generate outputs for use in other tasks
      outputs = {'downloads': downloads}
      Kestra.outputs(outputs)
```

**Key Points**:
- Container is automatically destroyed after execution
- Dependencies installed automatically with UV
- Use `Kestra.outputs()` to pass data to subsequent tasks
- Can reference Python files from GitHub instead of inline scripts

### Process Runner vs Docker Runner

**Docker Runner** (default):
- Spins up a fresh container
- Isolated environment
- Slower startup
- Best for: Python/Node.js scripts requiring dependencies

**Process Runner**:
- Runs directly on the Kestra server
- No container overhead
- Faster execution
- Best for: Simple shell commands, wget, curl

```yaml
tasks:
  - id: download_file
    type: io.kestra.plugin.scripts.shell.Commands
    runner: PROCESS  # Run directly, no container
    commands:
      - wget {{ inputs.url }} -O data.csv
```

---

## Building Data Pipelines

### Extract-Transform-Load (ETL) Pattern

```yaml
id: 03_getting_started_data_pipeline
namespace: zoomcamp

inputs:
  - id: columns_to_keep
    type: ARRAY
    itemType: STRING
    defaults:
      - brand
      - price

tasks:
  # EXTRACT
  - id: extract
    type: io.kestra.plugin.core.http.Download
    uri: https://dummyjson.com/products
  
  # TRANSFORM
  - id: transform
    type: io.kestra.plugin.scripts.python.Script
    containerImage: python:3.11-alpine
    inputFiles:
      data.json: "{{ outputs.extract.uri }}"
    outputFiles:
      - "*.json"
    env:
      COLUMNS_TO_KEEP: "{{ inputs.columns_to_keep }}"
    script: |
      import json
      import os
      
      columns_to_keep_str = os.getenv("COLUMNS_TO_KEEP")
      columns_to_keep = json.loads(columns_to_keep_str)
      
      with open("data.json", "r") as file:
          data = json.load(file)
      
      filtered_data = [
          {column: product.get(column, "N/A") for column in columns_to_keep}
          for product in data["products"]
      ]
      
      with open("products.json", "w") as file:
          json.dump(filtered_data, file, indent=4)
  
  # LOAD (Query)
  - id: query
    type: io.kestra.plugin.jdbc.duckdb.Queries
    inputFiles:
      products.json: "{{ outputs.transform.outputFiles['products.json'] }}"
    sql: |
      INSTALL json;
      LOAD json;
      SELECT brand, round(avg(price), 2) as avg_price
      FROM read_json_auto('{{ workingDir }}/products.json')
      GROUP BY brand
      ORDER BY avg_price DESC;
    fetchType: STORE
```

**Key Patterns**:
- `inputFiles`: Pass outputs from previous tasks as files
- `outputFiles`: Specify which files to capture from task execution
- `env`: Pass inputs/variables as environment variables
- `{{ workingDir }}`: Reference Kestra's working directory

---

## Loading Data to PostgreSQL (ETL)

### Complete ETL Flow with Staging Tables

```yaml
id: 04_taxi_postgres
namespace: zoomcamp

inputs:
  - id: taxi
    type: SELECT
    values: [green, yellow]
    defaults: green
  - id: year
    type: STRING
    defaults: "2019"
  - id: month
    type: STRING
    defaults: "01"

variables:
  download_url: >
    https://github.com/DataTalksClub/nyc-tlc-data/releases/download/
    {{ inputs.taxi }}/{{ inputs.taxi }}_tripdata_{{ inputs.year }}-{{ inputs.month }}.csv.gz
  table_name: "{{ inputs.taxi }}_tripdata"
  staging_table_name: "{{ inputs.taxi }}_tripdata_staging"

labels:
  dataset: "{{ inputs.taxi }}"
  year: "{{ inputs.year }}"
  month: "{{ inputs.month }}"

tasks:
  # EXTRACT
  - id: extract
    type: io.kestra.plugin.scripts.shell.Commands
    runner: PROCESS
    outputFiles:
      - "*.csv"
    commands:
      - wget {{ render(vars.download_url) }} -O archive.csv.gz
      - gunzip archive.csv.gz
  
  # CREATE MAIN TABLE
  - id: create_table
    type: io.kestra.plugin.jdbc.postgresql.Query
    sql: |
      CREATE TABLE IF NOT EXISTS {{ vars.table_name }} (
        VendorID INTEGER,
        lpep_pickup_datetime TIMESTAMP,
        lpep_dropoff_datetime TIMESTAMP,
        passenger_count INTEGER,
        trip_distance DOUBLE PRECISION,
        -- ... more columns
        unique_row_id TEXT,
        filename TEXT
      );
  
  # CREATE STAGING TABLE
  - id: create_staging_table
    type: io.kestra.plugin.jdbc.postgresql.Query
    sql: |
      DROP TABLE IF EXISTS {{ vars.staging_table_name }};
      CREATE TABLE {{ vars.staging_table_name }} (LIKE {{ vars.table_name }});
  
  # LOAD TO STAGING
  - id: load_to_staging
    type: io.kestra.plugin.jdbc.postgresql.CopyIn
    from: "{{ outputs.extract.outputFiles['archive.csv'] }}"
    table: "{{ vars.staging_table_name }}"
    columns:
      - VendorID
      - lpep_pickup_datetime
      - lpep_dropoff_datetime
      - passenger_count
      - trip_distance
      # ... list all CSV columns
  
  # TRANSFORM (Add metadata)
  - id: transform_staging
    type: io.kestra.plugin.jdbc.postgresql.Query
    sql: |
      UPDATE {{ vars.staging_table_name }}
      SET 
        unique_row_id = MD5(
          COALESCE(CAST(VendorID AS TEXT), '') ||
          COALESCE(CAST(lpep_pickup_datetime AS TEXT), '')
          -- ... hash all relevant columns
        ),
        filename = '{{ inputs.taxi }}_tripdata_{{ inputs.year }}-{{ inputs.month }}.csv';
  
  # LOAD (Merge to main table)
  - id: merge_to_main
    type: io.kestra.plugin.jdbc.postgresql.Query
    sql: |
      INSERT INTO {{ vars.table_name }}
      SELECT * FROM {{ vars.staging_table_name }}
      ON CONFLICT (unique_row_id) DO NOTHING;

pluginDefaults:
  - type: io.kestra.plugin.jdbc.postgresql
    values:
      url: jdbc:postgresql://postgres:5432/ny_taxi
      username: root
      password: root

taskCache:
  enabled: true  # Cache extract step if already run
```

**Why Staging Tables?**
- Validate data before loading to main table
- Add metadata (unique IDs, source filenames)
- Transform data safely without affecting production
- Enable upserts and conflict resolution

**Task Caching**:
```yaml
taskCache:
  enabled: true
```
- Skips expensive extract operations if already executed
- Reuses cached results from previous runs
- Saves time and bandwidth

---

## Scheduling and Backfills

### Scheduled Triggers

Replace manual inputs with scheduled execution:

```yaml
triggers:
  - id: green_taxi_schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 9 1 * *"  # First day of month at 9 AM
    inputs:
      taxi: green
      year: "{{ trigger.date | date('yyyy') }}"
      month: "{{ trigger.date | date('MM') }}"
  
  - id: yellow_taxi_schedule
    type: io.kestra.plugin.core.trigger.Schedule
    cron: "0 20 1 * *"  # First day of month at 8 PM
    inputs:
      taxi: yellow
      year: "{{ trigger.date | date('yyyy') }}"
      month: "{{ trigger.date | date('MM') }}"
```

**Cron Format**: `minute hour day month day_of_week`
- `0 9 1 * *`: 9:00 AM on the 1st of every month
- `0 */2 * * *`: Every 2 hours
- `0 0 * * 0`: Every Sunday at midnight

### Backfilling Historical Data

Run the flow for past time periods to load historical data:

**In Kestra UI**:
1. Go to your flow
2. Click "Backfill" button
3. Set start date: `2019-01-01T09:00:00`
4. Set end date: `2019-02-02T00:00:00`
5. Execute

**Important**: Backfill period must include the times when scheduled triggers would have fired.
- Schedule: 9 AM on 1st of month
- Need data for January → Include `2019-01-01T09:00:00`
- Need data for February → Include `2019-02-01T09:00:00`
- End date: `2019-02-02` ensures February 1st 9 AM is included

---

## ETL vs ELT for Cloud Data Warehouses

### ETL (Extract-Transform-Load)

Traditional approach used for PostgreSQL:

1. **Extract**: Download data from source
2. **Transform**: Clean and process data locally (Python/pandas)
3. **Load**: Insert transformed data to database

**Use Case**: Local databases, limited storage, need immediate validation

### ELT (Extract-Load-Transform)

Modern approach for cloud data warehouses (BigQuery, Snowflake):

1. **Extract**: Download data from source
2. **Load**: Upload raw data to Data Lake (GCS) → then to Data Warehouse (BigQuery)
3. **Transform**: Use warehouse's computing power for transformations

**Why ELT for BigQuery?**
- **Performance**: BigQuery can transform massive datasets in seconds
- **Cost**: Pay only for query execution time
- **Scalability**: Cloud resources scale automatically
- **Separation**: Raw data preserved in Data Lake for re-processing

### Data Flow in GCP

```
GitHub (Source)
    ↓ Extract
Your Machine/Kestra
    ↓ Load
Google Cloud Storage (Data Lake - Raw CSV files)
    ↓ Load + Transform
BigQuery (Data Warehouse - Structured tables)
```

**Key Point**: Data is physically loaded to GCS first, then BigQuery reads from GCS to create optimized tables.

---

## Setting Up Google Cloud Platform

### Prerequisites

1. **Create GCP Project**
2. **Enable APIs**:
   - Cloud Storage API
   - BigQuery API
3. **Create Service Account**:
   - IAM & Admin → Service Accounts → Create
   - Grant roles:
     - Storage Admin
     - BigQuery Admin
   - Create JSON key → Download `service-account.json`

### Securing Credentials in Kestra

**Never commit secrets to Git!** Add to `.gitignore`:
```
service-account.json
.env_encoded
```

**Store credentials in Kestra Secrets**:
1. Navigate to Kestra UI → Settings → Secrets
2. Add new secret: `GCP_SERVICE_ACCOUNT`
3. Paste contents of `service-account.json`

**Store configuration in KV Store**:

```yaml
id: 06_gcp_kv
namespace: zoomcamp

tasks:
  - id: gcp_project_id
    type: io.kestra.plugin.core.kv.Set
    key: GCP_PROJECT_ID
    kvType: STRING
    value: your-project-id
  
  - id: gcp_location
    type: io.kestra.plugin.core.kv.Set
    key: GCP_LOCATION
    kvType: STRING
    value: europe-west2
  
  - id: gcp_bucket_name
    type: io.kestra.plugin.core.kv.Set
    key: GCP_BUCKET_NAME
    kvType: STRING
    value: your-globally-unique-bucket-name
  
  - id: gcp_dataset
    type: io.kestra.plugin.core.kv.Set
    key: GCP_DATASET
    kvType: STRING
    value: zoomcamp
```

### Creating GCP Resources with Kestra

```yaml
id: 07_gcp_setup
namespace: zoomcamp

tasks:
  - id: create_gcs_bucket
    type: io.kestra.plugin.gcp.gcs.CreateBucket
    ifExists: SKIP
    storageClass: REGIONAL
    name: "{{ kv('GCP_BUCKET_NAME') }}"
  
  - id: create_bq_dataset
    type: io.kestra.plugin.gcp.bigquery.CreateDataset
    name: "{{ kv('GCP_DATASET') }}"
    ifExists: SKIP

pluginDefaults:
  - type: io.kestra.plugin.gcp
    values:
      serviceAccount: "{{ secret('GCP_SERVICE_ACCOUNT') }}"
      projectId: "{{ kv('GCP_PROJECT_ID') }}"
      location: "{{ kv('GCP_LOCATION') }}"
      bucket: "{{ kv('GCP_BUCKET_NAME') }}"
```

**After execution**:
- GCS bucket created in Cloud Storage
- BigQuery dataset created

---

## Loading Data to BigQuery (ELT)

### Complete ELT Flow

```yaml
id: 08_taxi_gcp
namespace: zoomcamp

inputs:
  - id: taxi
    type: SELECT
    values: [green, yellow]
  - id: year
    type: STRING
  - id: month
    type: STRING

variables:
  download_url: >
    https://github.com/DataTalksClub/nyc-tlc-data/releases/download/
    {{ inputs.taxi }}/{{ inputs.taxi }}_tripdata_{{ inputs.year }}-{{ inputs.month }}.csv.gz
  gcs_file: "{{ kv('GCP_DATASET') }}.{{ inputs.taxi }}_tripdata"
  bq_table: "{{ kv('GCP_PROJECT_ID') }}.{{ kv('GCP_DATASET') }}.{{ inputs.taxi }}_tripdata"

labels:
  dataset: "{{ inputs.taxi }}"
  year: "{{ inputs.year }}"
  month: "{{ inputs.month }}"

tasks:
  # EXTRACT
  - id: extract
    type: io.kestra.plugin.scripts.shell.Commands
    runner: PROCESS
    outputFiles:
      - "*.csv"
    commands:
      - wget {{ render(vars.download_url) }} -O archive.csv.gz
      - gunzip archive.csv.gz
  
  # LOAD to GCS
  - id: load_to_gcs
    type: io.kestra.plugin.gcp.gcs.Upload
    from: "{{ outputs.extract.outputFiles['archive.csv'] }}"
    to: "gs://{{ kv('GCP_BUCKET_NAME') }}/{{ vars.gcs_file }}/{{ inputs.year }}-{{ inputs.month }}.csv"
  
  # CREATE BigQuery Table (if needed)
  - id: create_bq_table
    type: io.kestra.plugin.gcp.bigquery.Query
    sql: |
      CREATE TABLE IF NOT EXISTS `{{ vars.bq_table }}` (
        VendorID INT64,
        lpep_pickup_datetime TIMESTAMP,
        lpep_dropoff_datetime TIMESTAMP,
        passenger_count INT64,
        trip_distance FLOAT64,
        -- ... more columns (BigQuery syntax!)
        unique_row_id STRING,
        filename STRING
      );
  
  # CREATE Staging Table
  - id: create_staging_table
    type: io.kestra.plugin.gcp.bigquery.Query
    sql: |
      CREATE OR REPLACE TABLE `{{ vars.bq_table }}_staging`
      LIKE `{{ vars.bq_table }}`;
  
  # LOAD from GCS to Staging Table
  - id: load_to_staging
    type: io.kestra.plugin.gcp.bigquery.Load
    destinationTable: "{{ vars.bq_table }}_staging"
    format: CSV
    csvOptions:
      fieldDelimiter: ","
      skipLeadingRows: 1
    from:
      - "{{ outputs.load_to_gcs.uri }}"
  
  # TRANSFORM (Add metadata)
  - id: transform_staging
    type: io.kestra.plugin.gcp.bigquery.Query
    sql: |
      UPDATE `{{ vars.bq_table }}_staging`
      SET 
        unique_row_id = TO_HEX(MD5(
          CONCAT(
            CAST(VendorID AS STRING),
            CAST(lpep_pickup_datetime AS STRING)
            -- ... all columns
          )
        )),
        filename = '{{ inputs.taxi }}_tripdata_{{ inputs.year }}-{{ inputs.month }}.csv'
      WHERE TRUE;
  
  # LOAD (Merge to main table)
  - id: merge_to_main
    type: io.kestra.plugin.gcp.bigquery.Query
    sql: |
      MERGE `{{ vars.bq_table }}` T
      USING `{{ vars.bq_table }}_staging` S
      ON T.unique_row_id = S.unique_row_id
      WHEN NOT MATCHED THEN
        INSERT ROW;

pluginDefaults:
  - type: io.kestra.plugin.gcp
    values:
      serviceAccount: "{{ secret('GCP_SERVICE_ACCOUNT') }}"
      projectId: "{{ kv('GCP_PROJECT_ID') }}"
      location: "{{ kv('GCP_LOCATION') }}"
```

### BigQuery Syntax Differences

**Table References**:
- PostgreSQL: `table_name`
- BigQuery: `` `project_id.dataset.table_name` ``

**Data Types**:
- PostgreSQL: `INTEGER`, `DOUBLE PRECISION`, `TEXT`
- BigQuery: `INT64`, `FLOAT64`, `STRING`

**MERGE Syntax**:
```sql
-- BigQuery requires explicit MERGE syntax
MERGE `target_table` T
USING `source_table` S
ON T.id = S.id
WHEN NOT MATCHED THEN INSERT ROW
```

**Performance**: BigQuery transformations are dramatically faster (seconds vs minutes for large datasets).

---

## Backfills with BigQuery

Same backfill process as PostgreSQL, but leveraging cloud performance:

1. Set up scheduled triggers for both green and yellow taxi data
2. Use backfill feature to load historical months
3. Monitor execution in Kestra UI
4. Query data in BigQuery Console

**Result**: Months of data loaded and transformed in minutes instead of hours.

---

## AI-Assisted Workflow Development

### AI Copilot in Kestra

Kestra includes an AI Copilot powered by Gemini that understands Kestra's syntax and best practices.

**Setup**:

1. Get Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

2. Configure in `docker-compose.yml`:
```yaml
services:
  kestra:
    environment:
      KESTRA_CONFIGURATION: |
        kestra:
          ai:
            type: gemini
            gemini:
              model-name: gemini-2.5-flash
              api-key: ${GEMINI_API_KEY}
```

3. Restart Kestra:
```bash
export GEMINI_API_KEY="your-api-key-here"
docker compose up -d
```

**Using AI Copilot**:
1. Open Kestra UI → Create new flow
2. Click AI Copilot button (✨ sparkle icon)
3. Enter natural language prompt:
   - "Create a flow that loads NYC taxi data to BigQuery"
   - "Add error handling to my extract task"
   - "Schedule this flow to run daily"

**Why AI Copilot > ChatGPT**:
- **Context-aware**: Has access to current Kestra documentation
- **Executable code**: Generates working YAML that runs immediately
- **Best practices**: Follows Kestra conventions and patterns
- **Up-to-date**: Uses latest plugin versions and features

### Context Engineering with ChatGPT

If using ChatGPT or other generic AI:
- Provide Kestra documentation links
- Include example flows in your prompt
- Specify plugin versions
- Expect to debug and adjust generated code

**Recommendation**: Use Kestra's built-in AI Copilot for best results.

---

## Best Practices

### Workflow Design
- Use meaningful IDs for flows and tasks
- Add descriptions to document purpose
- Apply labels to executions for filtering
- Use variables for reusable values
- Enable task caching for expensive operations

### Error Handling
- Set appropriate concurrency limits
- Use `ifExists: SKIP` for idempotent operations
- Implement retries for flaky external APIs
- Monitor execution logs regularly

### Security
- Never commit service account keys to Git
- Store credentials in Kestra Secrets
- Use KV Store for non-sensitive configuration
- Rotate API keys periodically
- Set up `.gitignore` properly

### Performance
- Use Process Runner for simple commands
- Enable task caching where appropriate
- Consider ELT over ETL for large datasets
- Leverage cloud warehouse compute power
- Run independent tasks in parallel

### Cloud Resources
- Use `ifExists: SKIP` to avoid recreation errors
- Set lifecycle policies on GCS buckets
- Monitor BigQuery costs (query bytes processed)
- Clean up unused datasets and tables
- Use regional storage for cost optimization

---

## Common Issues and Solutions

**Issue**: AI Copilot not working
- **Solution**: Verify `GEMINI_API_KEY` is set correctly and Kestra is restarted

**Issue**: BigQuery authentication failed
- **Solution**: Check service account has required permissions and JSON key is valid

**Issue**: Task cache not working
- **Solution**: Ensure `taskCache: enabled: true` is set at flow level

**Issue**: Backfill creating duplicate data
- **Solution**: Implement proper UPSERT logic with `ON CONFLICT DO NOTHING` (PostgreSQL) or `MERGE` (BigQuery)

**Issue**: GCS bucket name already exists
- **Solution**: Bucket names must be globally unique; choose a different name

**Issue**: Scheduled trigger not firing
- **Solution**: Check `disabled: false` and verify cron syntax

**Issue**: Python dependencies not installing
- **Solution**: List all dependencies explicitly in `dependencies` array

---

## Key Takeaways

1. **Orchestration is essential** for production data pipelines—don't manually coordinate tasks
2. **Kestra's language-agnostic** approach lets you use the best tool for each job
3. **Labels and monitoring** make debugging much easier than digging through logs
4. **ELT is preferred for cloud warehouses** to leverage their computational power
5. **Task caching** saves time and resources for expensive operations
6. **Backfills** let you efficiently load historical data using the same workflow
7. **AI Copilot** accelerates development when it has proper context
8. **Security first**: always use secrets management, never commit credentials

---

*These notes are from the 2026 Data Engineering Zoomcamp. Contributions and improvements welcome!*
