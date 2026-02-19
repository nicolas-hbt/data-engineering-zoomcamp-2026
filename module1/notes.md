# Module 1: Containerization and Infrastructure as Code

## Overview
This module covers Docker fundamentals for data engineering workflows and Infrastructure as Code (IaC) using Terraform. You'll learn to containerize data pipelines, manage databases with Docker, and provision cloud infrastructure programmatically.

---

## Docker Fundamentals

### Core Concepts

**Docker Containers are Stateless**
- When you create a container, make changes, and exit, those changes are lost if you create a new container
- However, stopped containers persist and can be restarted with their state intact
- Each container has a unique `CONTAINER_ID` and name for identification

**Key Docker Commands**

```bash
# List all container IDs
docker ps -a -q

# Remove all containers at once
docker rm $(docker ps -a -q)

# Remove container after running (clean up automatically)
docker run --rm <image_name>
```

### Volume Mapping

Volume mapping allows you to share files between your host machine and Docker containers:

```bash
docker run -v $(pwd)/test:/app/test <image_name>
```

This maps `$(pwd)/test` from your host to `/app/test` in the container, making data persistent and accessible.

---

## Building Docker Images for Data Pipelines

### Basic Dockerfile Structure

```dockerfile
# Base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy files from host to container
COPY pipeline.py .
COPY requirements.txt .
COPY data.csv .

# Install dependencies
RUN pip install -r requirements.txt

# Default command
ENTRYPOINT ["python", "pipeline.py"]
```

### Using UV for Faster Dependency Management

UV is a Rust-based Python package manager that's significantly faster than conda or pip:

```dockerfile
FROM python:3.9

# Copy UV from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy project files
COPY . .

# Install dependencies with locked versions for reproducibility
RUN uv sync --locked
```

**Key Points:**
- `--locked` ensures exact version reproducibility between environments
- UV can be enabled via entrypoint or environment variable
- Even when using UV in containers, you can still use tools like `pgcli` from your host machine

---

## Running PostgreSQL with Docker

### Starting a PostgreSQL Container

```bash
docker run -it \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=ny_taxi \
  -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:13
```

### Connecting to PostgreSQL

```bash
pgcli -h localhost -p 5432 -u root -d ny_taxi
```

Parameters correspond to your container configuration:
- `-h`: host (localhost when accessing from host machine)
- `-p`: port (mapped port)
- `-u`: username
- `-d`: database name

---

## Loading Data into PostgreSQL with Python

### Schema Inference Issues with CSV

CSV files don't have embedded schemas, leading to incorrect data type inference:

```python
import pandas as pd

# Problem: pandas may infer wrong types
df = pd.read_csv('data.csv')
# passenger_count might be float instead of int
# datetime fields might be read as strings
```

**Solution:** Explicitly define schema using `dtype` parameter and parse dates:

```python
df = pd.read_csv(
    'data.csv',
    dtype={'passenger_count': 'Int64'},
    parse_dates=['tpep_pickup_datetime', 'tpep_dropoff_datetime']
)
```

### Chunked Data Loading

For large datasets, load data in chunks to avoid memory issues:

```python
from sqlalchemy import create_engine

# Create database connection
engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')

# Load data in chunks
df_iter = pd.read_csv('data.csv', iterator=True, chunksize=100000)

for chunk in df_iter:
    chunk.to_sql(name='yellow_taxi_trips', con=engine, if_exists='append')
```

**Why SQLAlchemy?**
- Pandas uses SQLAlchemy to interact with different database engines
- Provides a consistent interface across PostgreSQL, MySQL, SQLite, etc.

---

## Docker Networking

### Creating Networks for Container Communication

Containers need to be on the same network to communicate:

```bash
# Create a network
docker network create pg-network

# Run PostgreSQL on the network
docker run -it \
  --network=pg-network \
  --name pg-database \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=ny_taxi \
  postgres:13

# Run your application on the same network
docker run -it \
  --network=pg-network \
  my-data-pipeline
```

Containers on the same network can reference each other by container name instead of localhost.

---

## Docker Compose

### Simplifying Multi-Container Setups

Instead of running multiple `docker run` commands, define all services in `docker-compose.yaml`:

```yaml
version: '3.8'

services:
  pgdatabase:
    image: postgres:13
    environment:
      - POSTGRES_USER=root
      - POSTGRES_PASSWORD=root
      - POSTGRES_DB=ny_taxi
    volumes:
      - ./ny_taxi_postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - pg-network

  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@admin.com
      - PGADMIN_DEFAULT_PASSWORD=root
    ports:
      - "8080:80"
    networks:
      - pg-network

networks:
  pg-network:
    driver: bridge
```

**Commands:**
```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Stop all services
docker-compose down
```

---

## SQL Refresher

### JOIN Types

**Inner Join (Explicit)**
```sql
SELECT
    t.tpep_pickup_datetime,
    t.total_amount,
    CONCAT(zpu."Borough", ' | ', zpu."Zone") AS pickup_loc,
    CONCAT(zdo."Borough", ' | ', zdo."Zone") AS dropoff_loc
FROM yellow_taxi_trips t
JOIN zones zpu ON t."PULocationID" = zpu."LocationID"
JOIN zones zdo ON t."DOLocationID" = zdo."LocationID"
LIMIT 100;
```

**Left Join** (keeps all rows from left table)
```sql
SELECT *
FROM yellow_taxi_trips t
LEFT JOIN zones z ON t."PULocationID" = z."LocationID"
```

### Data Quality Checks

**Finding NULL values:**
```sql
SELECT *
FROM yellow_taxi_trips
WHERE "PULocationID" IS NULL 
   OR "DOLocationID" IS NULL;
```

**Finding IDs not in lookup table:**
```sql
SELECT *
FROM yellow_taxi_trips
WHERE "PULocationID" NOT IN (SELECT "LocationID" FROM zones)
   OR "DOLocationID" NOT IN (SELECT "LocationID" FROM zones);
```

### Aggregations

**Group by date:**
```sql
SELECT
    CAST(tpep_dropoff_datetime AS DATE) AS day,
    COUNT(1) AS trip_count,
    MAX(total_amount) AS max_amount,
    MAX(passenger_count) AS max_passengers
FROM yellow_taxi_trips
GROUP BY CAST(tpep_dropoff_datetime AS DATE)
ORDER BY day ASC;
```

**Group by multiple fields:**
```sql
SELECT
    CAST(tpep_dropoff_datetime AS DATE) AS day,
    "DOLocationID",
    COUNT(1) AS trip_count
FROM yellow_taxi_trips
GROUP BY 1, 2  -- Can reference columns by position
ORDER BY day ASC, "DOLocationID" ASC;
```

---

## Infrastructure as Code with Terraform

### What is Terraform?

Terraform is an open-source IaC tool that allows you to:
- **Define infrastructure as code**: Write configuration files instead of clicking through cloud consoles
- **Version control infrastructure**: Track changes in Git like application code
- **Reproduce environments**: Create identical infrastructure across dev, staging, and production
- **Automate provisioning**: Spin up and tear down resources programmatically

### Why Use Terraform for Data Engineering?

**Reproducibility**: Define your exact cluster configuration (GPUs, libraries, versions) once and recreate it reliably

**Cost Control**: Automatically destroy expensive resources after jobs complete

**Collaboration**: Share infrastructure definitions with team members via Git

**Documentation**: Infrastructure code serves as living documentation

### Key Terraform Concepts

**Declarative vs Imperative:**
- You describe the *desired end state*, not the steps to get there
- Terraform figures out what needs to be created, updated, or deleted

**State Management:**
- Terraform tracks your infrastructure in a state file
- Compares desired state (your code) with actual state (what's deployed)
- Determines the minimum changes needed

### Core Terraform Files

```
project/
├── main.tf          # Main configuration
├── variables.tf     # Input variables
├── terraform.tfstate # State file (auto-generated, don't edit)
└── .terraform/      # Provider plugins (auto-generated)
```

### Basic Terraform Workflow

```bash
# 1. Initialize (download provider plugins)
terraform init

# 2. Preview changes (safe, read-only)
terraform plan

# 3. Apply changes (creates/modifies infrastructure - costs money!)
terraform apply

# 4. Destroy everything (removes all resources)
terraform destroy
```

### Example: Creating GCP Resources

**main.tf:**
```hcl
terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  backend "local" {}  # Store state locally
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Create a GCS bucket for data lake
resource "google_storage_bucket" "data_lake" {
  name          = "${var.project_id}-data-lake"
  location      = var.region
  force_destroy = true
  
  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}

# Create a BigQuery dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id = "ny_taxi_data"
  location   = var.region
}
```

**variables.tf:**
```hcl
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}
```

### Securing Sensitive Data

**Never hardcode secrets in Terraform files!**

Use environment variables:
```bash
# Linux/Mac
export TF_VAR_project_id="my-gcp-project"
export TF_VAR_databricks_token="secret-token"

# Windows PowerShell
$env:TF_VAR_project_id="my-gcp-project"
```

Mark variables as sensitive:
```hcl
variable "databricks_token" {
  type      = string
  sensitive = true  # Prevents logging in console
}
```

### GCP Service Account Setup

For GCP, you need a service account:
1. Create service account in GCP Console
2. Grant necessary permissions (Storage Admin, BigQuery Admin, etc.)
3. Download JSON key file
4. Set environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
   ```

---

## Best Practices

### Docker
- Use `.dockerignore` to exclude unnecessary files from images
- Always use `--rm` flag for one-off containers to clean up
- Pin specific image versions for reproducibility (`python:3.9` not `python:latest`)
- Use multi-stage builds to reduce final image size
- Use `--locked` with UV to ensure dependency reproducibility

### Terraform
- Always run `terraform plan` before `apply`
- Store state files securely (use remote backends for teams)
- Use variables for everything that might change between environments
- Add `.terraform/` and `*.tfstate` to `.gitignore`
- Tag resources for cost tracking and organization
- **Be aware**: `terraform apply` deploys real infrastructure and incurs costs!

### Data Engineering
- Always validate data types when loading CSVs
- Use chunked loading for large datasets
- Implement data quality checks (NULL checks, referential integrity)
- Document your schema and data pipeline assumptions

---

## Common Issues and Solutions

**Issue**: Container can't connect to PostgreSQL
- **Solution**: Ensure both containers are on the same Docker network

**Issue**: Pandas reads dates as strings
- **Solution**: Use `parse_dates` parameter in `pd.read_csv()`

**Issue**: Out of memory when loading large files
- **Solution**: Use `chunksize` parameter and iterative loading

**Issue**: Terraform fails with authentication error
- **Solution**: Verify `GOOGLE_APPLICATION_CREDENTIALS` is set correctly and service account has required permissions

**Issue**: Port already in use (5432, 8080)
- **Solution**: Stop conflicting services or map to different host ports

---

*These notes are from the 2026 Data Engineering Zoomcamp. Feel free to contribute improvements or corrections!*
