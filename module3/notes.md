# Module 3: Data Warehouse and BigQuery

## Overview
This module covers data warehousing concepts, BigQuery architecture and optimization, and machine learning capabilities within BigQuery. You'll learn the differences between OLTP and OLAP systems, how to optimize BigQuery for cost and performance, and how to build ML models directly in SQL.

---

## OLTP vs OLAP Systems

### OLTP (Online Transaction Processing)

**Purpose**: Handle day-to-day business operations with fast, short transactions.

**Strategy**: Normalization
- Data organized to minimize redundancy and ensure integrity
- Single piece of information stored in exactly one place
- Data split into many small, related tables (Customers, Products, Orders)

**Characteristics**:
- **Write-optimized**: Designed for fast INSERT/UPDATE operations
- **Space-efficient**: Small storage requirements, historical data archived
- **Real-time**: User-initiated transactions processed immediately
- **Normalized structure**: Multiple related tables with foreign keys

**Trade-offs**:
- Reading complex data requires joining many tables (slower reads)
- Query performance sacrificed for write efficiency
- Not ideal for analytical queries

**Example Use Cases**:
- E-commerce transactions
- Banking systems
- Booking systems
- Inventory management

### OLAP (Online Analytical Processing)

**Purpose**: Support decision-making through complex analysis and long-running queries.

**Strategy**: Denormalization
- Deliberate redundancy to prioritize read speed
- Multiple tables collapsed into flat, wide tables
- Same information duplicated across many rows

**Characteristics**:
- **Read-optimized**: Designed for fast SELECT and aggregation queries
- **Space-intensive**: Large storage requirements due to duplication and aggregation
- **Batch processing**: Periodic refreshes rather than real-time updates
- **Denormalized structure**: Fewer, wider tables with redundant data

**Trade-offs**:
- Writing data is slow and risky (must update millions of rows)
- Not suitable for real-time transactional operations
- Higher storage costs

**Example Use Cases**:
- Business intelligence dashboards
- Sales analytics
- Data mining
- Historical trend analysis

### Comparison Table

| Feature | OLTP | OLAP |
|---------|------|------|
| **Optimization** | Write-heavy | Read-heavy |
| **Structure** | Normalized (many tables) | Denormalized (fewer, wide tables) |
| **Query Type** | Simple, short transactions | Complex, analytical queries |
| **Data Volume** | Small, current data | Large, historical data |
| **Users** | Many concurrent users | Fewer analytical users |
| **Response Time** | Milliseconds | Seconds to minutes |
| **Updates** | Real-time | Batch/scheduled |

---

## Star Schema

The most common denormalization pattern for OLAP systems, designed for fast analytical queries.

### Components

**Fact Table (Center of the Star)**:
- Contains quantitative, measurable data (the "facts")
- Stores metrics about business processes
- Mostly numbers and foreign keys
- Example: `Sales_Fact` with `quantity_sold`, `price`, `discount_amount`

**Dimension Tables (Points of the Star)**:
- Contain descriptive attributes (the "Who, What, Where, When, Why")
- Provide context for facts
- Examples: `Date_Dimension`, `Product_Dimension`, `Store_Dimension`, `Customer_Dimension`

### Visual Structure

```
        Date_Dimension
              |
              |
Product ---- FACT ---- Customer
Dimension    TABLE    Dimension
              |
              |
        Store_Dimension
```

### Benefits

**1. Simplifies Queries**
- Only need to join Fact table to a few Dimension tables
- No complex web of 20+ table joins like normalized OLTP

**2. Fast Aggregation**
- Fact table mostly contains numbers and IDs
- Database can scan and sum millions of rows quickly

**3. BI Tool Optimization**
- Tools like Tableau, PowerBI specifically optimized for Star Schemas
- Drag-and-drop interfaces work naturally with this structure

**4. Predictability**
- Consistent query patterns
- Easy to understand and maintain

### Star Schema vs Snowflake Schema

| Feature | Star Schema | Snowflake Schema |
|---------|-------------|------------------|
| **Normalization** | Denormalized (flat dimensions) | Normalized (dimensions split into sub-tables) |
| **Complexity** | Simple (few joins) | Complex (many joins) |
| **Performance** | Faster reads | Slower reads, saves disk space |
| **Best For** | OLAP analytical queries | Storage-constrained environments |
| **Maintenance** | Easier | More complex |

---

## Data Warehouse Architecture

### Complete Data Flow

```
Data Sources → Staging Area → Data Warehouse → Data Marts
(OLTP DBs)                    (Single Source)   (Dept-Specific)
(Flat Files)                  of Truth
```

### 1. Data Sources & Staging Area

**Sources**:
- Operational systems (OLTP databases)
- Flat files (CSVs, Excel, logs)
- APIs and external services

**Staging Area**:
- Temporary "waiting room" or "construction site"
- Data cleaned, formatted, and validated
- Prevents dirty data from corrupting warehouse
- ETL/ELT processing happens here

### 2. The Data Warehouse (Single Source of Truth)

The central warehouse consolidates three types of data:

**Raw Data**:
- Unprocessed, granular data
- Example: Every individual website click
- **Who needs it**: Data Scientists, ML Engineers, Auditors
- **Why**: Perform complex data mining, train models, debug pipelines, find patterns

**Summary Data**:
- Pre-aggregated data
- Example: Total clicks per day per region
- **Who needs it**: Business analysts, executives
- **Why**: Fast access to metrics without heavy computation

**Metadata**:
- "Data about data"
- Information about when data was collected, original source, transformations applied
- **Who needs it**: Data engineers, governance teams
- **Why**: Track data lineage, ensure compliance, debug issues

### 3. Data Marts (Department-Focused Subsets)

**Purpose**: Curated "storefronts" containing only what specific teams need.

**Why They Exist**:
- Full warehouse too massive and complex for typical users
- Faster queries on smaller, focused datasets
- Pre-filtered and formatted for specific use cases

**Examples**:
- Sales Data Mart (revenue, customers, products)
- Purchasing Data Mart (suppliers, costs, inventory)
- Marketing Data Mart (campaigns, conversions, attribution)

**Who Uses Them**:
- Department managers and analysts
- Casual business users who need simple reports
- Teams wanting fast access without warehouse complexity

---

## BigQuery Overview

### What is BigQuery?

**Serverless Data Warehouse**:
- No servers to manage or database software to install
- Automatic scaling and high availability
- Pay only for resources used

**Built-in Features**:
- Machine learning (BigQuery ML)
- Geospatial analysis (GIS functions)
- Business intelligence (BI Engine)
- Column-oriented storage

**Architecture**:
- Separates compute engine from storage
- Scale storage and compute independently
- Leverage Google's Jupiter network (1TB/s within datacenters)

### Pricing Models

**1. On-Demand Pricing**
- Pay per query based on data processed
- **Cost**: $5 per TB of data scanned
- **Best for**: Variable workloads, development, experimentation

**2. Flat-Rate Pricing**
- Pre-purchase query processing capacity (slots)
- **Cost**: 100 slots = $2,000/month (equivalent to ~400TB on-demand)
- **Best for**: Predictable, high-volume workloads

**Cost Optimization Tips**:
- Use partitioning and clustering to reduce data scanned
- Avoid `SELECT *`, query only needed columns
- Use table expiration for temporary data
- Preview queries to see estimated costs before running

---

## External Tables

### What Are External Tables?

Tables that reference data stored in Google Cloud Storage (GCS) without copying it into BigQuery.

```sql
CREATE OR REPLACE EXTERNAL TABLE `taxi-rides-ny.nytaxi.external_yellow_tripdata`
OPTIONS (
  format = 'CSV',
  uris = [
    'gs://nyc-tl-data/trip_data/yellow_tripdata_2019-*.csv',
    'gs://nyc-tl-data/trip_data/yellow_tripdata_2020-*.csv'
  ]
);
```

### How It Works

- Data stays in GCS buckets
- BigQuery queries it as if it were a native table
- No data copying or loading required
- Wildcard (`*`) patterns match multiple files

### Benefits

**1. Zero Ingestion Cost & Time**
- Skip the ETL loading step entirely
- Query data seconds after it lands in GCS
- No waiting for data import jobs

**2. Cost-Effective Cold Storage**
- GCS storage cheaper than BigQuery storage
- Ideal for rarely-queried historical data
- Pay GCS rates instead of BigQuery rates

**3. Single Source of Truth**
- Other tools (Spark, Python scripts) can use same files
- No risk of BigQuery copy becoming out of sync
- One dataset, multiple access methods

### Trade-offs

**Performance Tax**:
- Slower than native tables (must reach out to GCS)
- CSV parsing happens on every query
- No query result caching

**Metadata Limitations**:
- Cannot enforce schema as strictly
- Broken CSV uploads cause query failures
- No automatic compression optimization

**Best Use Cases**:
- Infrequent queries on large historical datasets
- Data shared across multiple platforms
- Exploratory analysis before full ingestion
- Cost-sensitive archived data

---

## Partitioning in BigQuery

### What is Partitioning?

Dividing a table into segments (partitions) based on a column value, typically a date.

### Benefits

**1. Cost Efficiency (Query Pruning)**

Without partitioning:
```sql
-- Scans ENTIRE table (1.6 GB)
SELECT DISTINCT(VendorID)
FROM yellow_tripdata_non_partitioned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2019-06-30';
```

With partitioning:
```sql
-- Scans ONLY June partition (~106 MB)
SELECT DISTINCT(VendorID)
FROM yellow_tripdata_partitioned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2019-06-30';
```

**Savings**: 15x reduction in data scanned = 15x cost reduction!

**2. Improved Query Performance**
- Only scans relevant partitions
- Full table scans take minutes → partitioned scans take seconds
- Significantly smaller data volume processed

**3. Better Data Management**
- **Easy deletion**: Drop entire partitions instantly and free
- **Data lifecycle**: Set automatic expiration policies per partition
- **Targeted updates**: Update specific time ranges without affecting whole table

**4. Simplified Maintenance**
- Update specific time segments independently
- Avoid write-lock issues on massive tables
- Easier troubleshooting of data quality issues

### Creating Partitioned Tables

```sql
-- Create partitioned table from external table
CREATE OR REPLACE TABLE `taxi-rides-ny.nytaxi.yellow_tripdata_partitioned`
PARTITION BY DATE(tpep_pickup_datetime)
AS
SELECT * FROM `taxi-rides-ny.nytaxi.external_yellow_tripdata`;
```

### Inspecting Partitions

```sql
-- View partition information
SELECT table_name, partition_id, total_rows
FROM `nytaxi.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'yellow_tripdata_partitioned'
ORDER BY total_rows DESC;
```

**Use Case**: Check for partition bias or data distribution issues.

### Partition Types

- **DATE**: Most common, partition by day
- **DATETIME**: Partition by hour or day
- **TIMESTAMP**: Partition by hour or day
- **INTEGER RANGE**: Partition by numeric ranges

### Limitations

- Maximum 4,000 partitions per table
- Can only partition by ONE column (unlike clustering)
- Column must be DATE, DATETIME, TIMESTAMP, or INTEGER

---

## Clustering in BigQuery

### What is Clustering?

Organizing data within partitions by sorting on specific columns (up to 4 columns).

### How It Works

**Column Order Matters**:
```sql
CLUSTER BY VendorID, payment_type, passenger_count
```
- Data sorted first by VendorID
- Then by payment_type within each VendorID
- Then by passenger_count within each payment_type

**Physical Storage**:
- Rows with similar values stored together
- All "VendorID=1" rows in same physical blocks
- Faster scanning when filtering by clustered columns

### Creating Partitioned + Clustered Tables

```sql
CREATE OR REPLACE TABLE `taxi-rides-ny.nytaxi.yellow_tripdata_partitioned_clustered`
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID
AS
SELECT * FROM `taxi-rides-ny.nytaxi.external_yellow_tripdata`;
```

### Performance Comparison

**Partitioned only**:
```sql
-- Scans 1.1 GB
SELECT count(*) as trips
FROM yellow_tripdata_partitioned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31'
  AND VendorID = 1;
```

**Partitioned + Clustered**:
```sql
-- Scans 864.5 MB (21% reduction!)
SELECT count(*) as trips
FROM yellow_tripdata_partitioned_clustered
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31'
  AND VendorID = 1;
```

### When to Use Clustering

**Clustering is Better Than Partitioning When**:
- Filtering on high-cardinality columns (many unique values like user IDs)
- Column types not supported for partitioning (strings)
- Need to optimize for multiple filter columns
- Data has frequent updates (clustering auto-maintains sort order)

**The Overlap Problem**:
- New data inserted can overlap with existing clustered blocks
- Example: New "Android" rows might be written to different physical block than existing "Android" rows
- BigQuery automatically re-clusters in background (no action needed)

### Partitioning vs Clustering

| Feature | Partitioning | Clustering |
|---------|-------------|------------|
| **Columns** | 1 column only | Up to 4 columns |
| **Physical Logic** | Data in separate segments | Data sorted within segments |
| **Cost Estimate** | Exact before query runs | Approximate, not guaranteed |
| **Best For** | Time-series, large categories | High-cardinality columns, IDs |
| **Column Types** | DATE, DATETIME, TIMESTAMP, INTEGER | Any type |
| **Limit** | 4,000 partitions max | No hard limit |

### Choosing Cluster Columns

**Consider**:
- Columns frequently used in WHERE clauses
- Columns used in GROUP BY operations
- Cardinality (number of unique values)
- Query patterns of your users

**Example**: For taxi data, cluster by:
1. `VendorID` (frequently filtered)
2. `payment_type` (used in revenue analysis)
3. `passenger_count` (common aggregation dimension)

---

## BigQuery Best Practices

### 1. Don't Treat WITH Clauses as Prepared Statements

**The Misconception**:
```sql
WITH top_zones AS (
  SELECT pulocationid, SUM(total_amount) as total_revenue
  FROM yellow_tripdata
  GROUP BY 1
  ORDER BY total_revenue DESC
  LIMIT 10
)
-- BigQuery may execute 'top_zones' logic TWICE
SELECT a.pulocationid, a.total_revenue
FROM top_zones a
JOIN zone_lookup b ON a.pulocationid = b.locationid
UNION ALL
SELECT pulocationid, total_revenue
FROM top_zones;
```

**Problem**: BigQuery treats WITH as a macro, potentially re-executing it for each reference.

**Solution**: Use temporary tables for complex, reused subqueries:

```sql
-- Calculate ONCE
CREATE OR REPLACE TEMP TABLE cached_top_zones AS
SELECT pulocationid, SUM(total_amount) as total_revenue
FROM yellow_tripdata
GROUP BY 1
ORDER BY total_revenue DESC
LIMIT 10;

-- Use saved result multiple times (no re-computation)
SELECT a.pulocationid, a.total_revenue
FROM cached_top_zones a
JOIN zone_lookup b ON a.pulocationid = b.locationid
UNION ALL
SELECT pulocationid, total_revenue
FROM cached_top_zones;
```

**Key Insight**:
- **WITH clause**: Great for readability
- **TEMP table**: Great for performance when referenced multiple times

### 2. Avoid Oversharding Tables

**What is Sharding?**
- Manually splitting data across multiple tables by date suffix
- Example: `sales_20230101`, `sales_20230102`, `sales_20230103`
- Query with wildcards: `FROM sales_*`

**Why Avoid It?**

**Performance Hit**:
- BigQuery must load metadata for every individual table
- 1,000 shards = 1,000 metadata loads
- Significant overhead before query even starts

**Modern Solution**: Use partitioned tables instead

| Feature | Partitioning (Recommended) | Sharding (Avoid) |
|---------|---------------------------|------------------|
| **Structure** | One table with internal dividers | Hundreds of separate tables |
| **Metadata Overhead** | Low (one schema) | High (schema per shard) |
| **Ease of Use** | Simple SQL | Complex wildcards |
| **Maintenance** | Easy | Difficult |

### 3. Optimize JOIN Order

**Best Practice**: Place largest table first, smallest table last.

**Why?**

**Broadcast Join Mechanism**:
- BigQuery distributes first (largest) table across workers
- Broadcasts smaller tables to each worker's memory
- Workers perform join locally

**Correct Order**:
```sql
-- ✅ GOOD: Large table first
SELECT *
FROM billion_row_table big
JOIN thousand_row_lookup small
  ON big.id = small.id
```

**Wrong Order**:
```sql
-- ❌ BAD: Small table first
SELECT *
FROM thousand_row_lookup small
JOIN billion_row_table big
  ON small.id = big.id
-- BigQuery may try to broadcast billion_row_table (memory overflow!)
```

**Note**: BigQuery's query optimizer often reorders automatically, but explicit ordering helps with complex multi-table joins.

### 4. Additional Best Practices

**Query Optimization**:
- Avoid `SELECT *`, specify only needed columns
- Use `LIMIT` during development to reduce data scanned
- Filter early (WHERE before JOIN when possible)
- Use `APPROX_COUNT_DISTINCT()` instead of exact count for large datasets

**Cost Management**:
- Preview query cost before running (top-right corner in UI)
- Set custom cost controls and quotas
- Use materialized views for frequently-run expensive queries
- Schedule large queries during off-peak hours

**Schema Design**:
- Use nested and repeated fields (STRUCT, ARRAY) to denormalize
- Choose appropriate data types (INT64 vs STRING for IDs)
- Document schema with column descriptions

---

## BigQuery Internals

### Storage and Compute Separation

**Architecture**:
- Storage and compute on different hardware
- Independent scaling of each component
- Storage costs scale with data size
- Compute costs scale with query complexity

**Communication**:
- **Jupiter Network**: 1TB/s network speed within datacenters
- Enables seamless communication between storage and compute
- No query execution delays despite physical separation

**Benefits**:
- Add storage without adding compute (cost-efficient)
- Burst compute for large queries without provisioning
- Pay only for what you use

### Query Execution Engine

**Tree Structure**:
- Query split into execution tree
- Each node handles separate part of query
- Similar to Spark's distributed processing
- Parallelization across thousands of workers

**Example**:
```
       Root (Aggregate)
           /        \
     Join          Join
    /    \        /    \
 Scan   Scan   Scan   Scan
 (Part1) (Part2) (Part3) (Part4)
```

### Column-Oriented Storage

**How It Works**:
```
Row-oriented:        Column-oriented:
Row1: A, B, C       Column A: Row1, Row2, Row3
Row2: A, B, C       Column B: Row1, Row2, Row3
Row3: A, B, C       Column C: Row1, Row2, Row3
```

**Benefits**:
- **Fast aggregations**: Can read single column without touching others
- **Better compression**: Similar values stored together compress well
- **Selective reads**: Only read columns needed for query
- **Cache-friendly**: Sequential access patterns

**Why It Matters**:
- Queries rarely need all columns
- Analytical queries aggregate on few columns
- Dramatically reduces I/O for wide tables

---

## BigQuery Machine Learning (BQML)

### Overview

Build, train, and deploy ML models using only SQL—no Python or data export required.

**Key Features**:
- Train models directly on BigQuery data
- No data movement required
- Automatic feature preprocessing
- Simple SQL syntax
- Built-in model evaluation

**Trade-offs**:
- **Easiness**: Simple for non-ML specialists
- **Flexibility**: Less customizable than Python frameworks
- **Best For**: Quick prototypes, business analyst use cases
- **Not For**: Cutting-edge research, highly custom models

### Supported Model Types

- **Linear Regression**: Predict continuous values
- **Logistic Regression**: Binary classification
- **K-means Clustering**: Unsupervised grouping
- **Matrix Factorization**: Recommendation systems
- **Time Series**: Forecasting (ARIMA)
- **DNN**: Deep neural networks
- **Boosted Trees**: XGBoost models
- **AutoML**: Automatic model selection

### Complete ML Workflow Example

#### Step 1: Prepare Data

```sql
-- Create ML-ready table with proper schema
CREATE OR REPLACE TABLE `taxi-rides-ny.nytaxi.yellow_tripdata_ml` (
  `passenger_count` INTEGER,
  `trip_distance` FLOAT64,
  `PULocationID` STRING,
  `DOLocationID` STRING,
  `payment_type` STRING,
  `fare_amount` FLOAT64,
  `tolls_amount` FLOAT64,
  `tip_amount` FLOAT64
) AS (
  SELECT 
    passenger_count,
    trip_distance,
    CAST(PULocationID AS STRING),
    CAST(DOLocationID AS STRING),
    CAST(payment_type AS STRING),
    fare_amount,
    tolls_amount,
    tip_amount
  FROM `taxi-rides-ny.nytaxi.yellow_tripdata_partitioned`
  WHERE fare_amount != 0
);
```

**Why Cast to STRING?**
- Prevents BigQuery from treating IDs as numbers
- Location IDs are categorical, not numeric
- Better feature encoding for ML

#### Step 2: Create Model

```sql
-- Train linear regression model
CREATE OR REPLACE MODEL `taxi-rides-ny.nytaxi.tip_model`
OPTIONS (
  model_type='linear_reg',
  input_label_cols=['tip_amount'],
  DATA_SPLIT_METHOD='AUTO_SPLIT'
) AS
SELECT *
FROM `taxi-rides-ny.nytaxi.yellow_tripdata_ml`
WHERE tip_amount IS NOT NULL;
```

**Options Explained**:
- `model_type`: Algorithm to use
- `input_label_cols`: Target variable to predict
- `DATA_SPLIT_METHOD='AUTO_SPLIT'`: Automatic train/test split (80/20)

#### Step 3: Inspect Features

```sql
-- View feature information
SELECT * 
FROM ML.FEATURE_INFO(MODEL `taxi-rides-ny.nytaxi.tip_model`);
```

**Returns**: Feature names, types, and encoding methods.

#### Step 4: Evaluate Model

```sql
-- Get model performance metrics
SELECT *
FROM ML.EVALUATE(MODEL `taxi-rides-ny.nytaxi.tip_model`,
  (
    SELECT *
    FROM `taxi-rides-ny.nytaxi.yellow_tripdata_ml`
    WHERE tip_amount IS NOT NULL
  )
);
```

**Metrics for Linear Regression**:
- `mean_absolute_error`
- `mean_squared_error`
- `r2_score`
- `median_absolute_error`

#### Step 5: Make Predictions

```sql
-- Predict on new data
SELECT *
FROM ML.PREDICT(MODEL `taxi-rides-ny.nytaxi.tip_model`,
  (
    SELECT *
    FROM `taxi-rides-ny.nytaxi.yellow_tripdata_ml`
    WHERE tip_amount IS NOT NULL
  )
);
```

**Returns**: Original data + `predicted_tip_amount` column.

#### Step 6: Explain Predictions

```sql
-- Get feature importance for predictions
SELECT *
FROM ML.EXPLAIN_PREDICT(MODEL `taxi-rides-ny.nytaxi.tip_model`,
  (
    SELECT *
    FROM `taxi-rides-ny.nytaxi.yellow_tripdata_ml`
    WHERE tip_amount IS NOT NULL
  ),
  STRUCT(3 as top_k_features)  -- Show top 3 features
);
```

**Returns**: Prediction + feature attribution scores.

### Hyperparameter Tuning

```sql
-- Train with hyperparameter search
CREATE OR REPLACE MODEL `taxi-rides-ny.nytaxi.tip_hyperparam_model`
OPTIONS (
  model_type='linear_reg',
  input_label_cols=['tip_amount'],
  DATA_SPLIT_METHOD='AUTO_SPLIT',
  num_trials=5,
  max_parallel_trials=2,
  l1_reg=hparam_range(0, 20),
  l2_reg=hparam_candidates([0, 0.1, 1, 10])
) AS
SELECT *
FROM `taxi-rides-ny.nytaxi.yellow_tripdata_ml`
WHERE tip_amount IS NOT NULL;
```

**Hyperparameter Options**:
- `num_trials`: Number of different configurations to try
- `max_parallel_trials`: How many to run simultaneously
- `hparam_range(min, max)`: Search continuous range
- `hparam_candidates([...])`: Search discrete values

**Available Hyperparameters** (model-dependent):
- `l1_reg`, `l2_reg`: Regularization strength
- `learn_rate`: Learning rate for gradient descent
- `max_tree_depth`: For tree-based models
- `num_clusters`: For k-means

---

## Model Deployment

### Export Model to Google Cloud Storage

```bash
# Login to gcloud
gcloud auth login

# Export model to GCS
bq --project_id taxi-rides-ny extract -m nytaxi.tip_model gs://taxi_ml_model/tip_model
```

### Download and Prepare for Serving

```bash
# Create local directory
mkdir /tmp/model

# Copy from GCS to local
gsutil cp -r gs://taxi_ml_model/tip_model /tmp/model

# Prepare for TensorFlow Serving
mkdir -p serving_dir/tip_model/1
cp -r /tmp/model/tip_model/* serving_dir/tip_model/1
```

### Deploy with TensorFlow Serving (Docker)

```bash
# Pull TensorFlow Serving image
docker pull tensorflow/serving

# Run serving container
docker run -p 8501:8501 \
  --mount type=bind,source=$(pwd)/serving_dir/tip_model,target=/models/tip_model \
  -e MODEL_NAME=tip_model \
  -t tensorflow/serving &
```

### Make Predictions via REST API

**Using curl**:
```bash
curl -d '{
  "instances": [
    {
      "passenger_count": 1,
      "trip_distance": 12.2,
      "PULocationID": "193",
      "DOLocationID": "264",
      "payment_type": "2",
      "fare_amount": 20.4,
      "tolls_amount": 0.0
    }
  ]
}' -X POST http://localhost:8501/v1/models/tip_model:predict
```

**Check model status**:
```bash
curl http://localhost:8501/v1/models/tip_model
```

### Using Postman for API Testing

**What is Postman?**
- Unified API platform for testing and development
- User-friendly GUI for sending HTTP requests
- No need to write curl commands manually

**Key Features**:
- **Collections**: Organize related API requests
- **Environments**: Switch between dev/staging/prod
- **Testing**: Automated functional and regression tests
- **Documentation**: Auto-generate API docs
- **Monitoring**: Schedule health checks

**For BQML Deployment**:
1. Open Postman
2. Create POST request to `http://localhost:8501/v1/models/tip_model:predict`
3. Set body to JSON with instance data
4. Send request and view predictions

---

## Key Takeaways

### OLTP vs OLAP
- **OLTP**: Normalized, write-optimized, transactional
- **OLAP**: Denormalized, read-optimized, analytical
- Star schema is the standard OLAP design pattern

### Data Warehouse Architecture
- Raw data for scientists and debugging
- Summary data for business users
- Data marts for department-specific access

### BigQuery Fundamentals
- Serverless, separates storage from compute
- Pay per query ($5/TB) or flat-rate (slots)
- External tables for cost-effective cold storage

### Performance Optimization
- **Partitioning**: Reduce data scanned by date/integer ranges
- **Clustering**: Sort within partitions for specific columns
- Combine both for maximum efficiency (up to 90%+ cost reduction)

### Best Practices
- Use temp tables, not WITH clauses, for repeated complex queries
- Avoid table sharding, use partitioning instead
- Place largest tables first in JOINs
- Preview query costs before running

### BigQuery ML
- Train ML models entirely in SQL
- No data export needed
- Great for quick prototypes and business analysts
- Less flexible than Python frameworks

### Model Deployment
- Export to GCS, serve with TensorFlow Serving
- REST API for predictions
- Use Postman for API testing and development

---

*These notes are from the 2026 Data Engineering Zoomcamp. Contributions welcome!*
