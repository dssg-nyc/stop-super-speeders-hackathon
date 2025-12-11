# Backend Architecture Documentation

## Overview

The backend folder (`backend/`) contains all server-side logic, data processing pipelines, and database schema definitions for the SAFENY Super Speeder Detection System.

---

## File Structure

```
backend/
├── app.py                     # FastAPI web application
├── src/
│   ├── __init__.py           # Package initialization
│   ├── cleaning.py           # Data validation & standardization
│   ├── ingestion.py          # DuckDB warehouse loading
│   └── super_speeder_detector.py  # Detection logic
├── sql/
│   └── 01_schema.sql         # Database schema definition
└── tests/
    └── test_super_speeder_detector.py  # Unit tests
```

---

## Core Modules

### `app.py` - FastAPI Web Server

**Purpose:** Main web application entry point

**Key Responsibilities:**
- Handle HTTP requests (upload, display, resources)
- Manage file uploads and validation
- Orchestrate data pipeline (clean → ingest → detect)
- Render Jinja2 templates
- Error handling and logging

**Main Routes:**
| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Upload interface |
| `/upload` | POST | Process CSV upload |
| `/results` | GET | Display detection results |
| `/driver/{id}` | GET | Individual driver details |
| `/resources` | GET | Program information |
| `/health` | GET | Health check |

**Dependencies:**
- FastAPI, Uvicorn
- Jinja2Templates
- Pathlib (path management)

**Running:**
```bash
cd /path/to/project/backend
python app.py
# Server runs on http://localhost:8000
```

---

### `src/cleaning.py` - Data Cleaning Module

**Purpose:** Validate and standardize raw CSV data before database loading

**Key Classes:**
- **DataCleaner:** Handles both speed camera and traffic violation datasets

**Key Functions:**
```python
DataCleaner.clean_speed_cameras(df: pd.DataFrame) → pd.DataFrame
  - Normalizes column names
  - Validates critical fields (plate, violation_date)
  - Handles missing values
  - Returns cleaned DataFrame

DataCleaner.clean_traffic_violations(df: pd.DataFrame) → pd.DataFrame
  - Similar process for violation-specific fields
  - Validates license IDs and point values

clean_and_export(input_dir, output_dir, file_patterns, strict_mode) → Tuple[pd.DataFrame, pd.DataFrame]
  - Batch processes multiple files
  - Exports to Parquet format
  - Returns (speed_cameras_df, violations_df)
```

**Data Validation:**
- **Speed Cameras:** plate, violation_date, violation, fine_amount
- **Violations:** license, violation_date, violation_description, points

**Output:** Parquet files in `../data/cleaned/`

**CLI Usage:**
```bash
python src/cleaning.py \
  --input-dir ../data/raw \
  --output-dir ../data/cleaned \
  --pattern "test*" \
  --strict
```

---

### `src/ingestion.py` - DuckDB Ingestion Pipeline

**Purpose:** Load cleaned data into DuckDB analytics warehouse

**Key Classes:**
- **DuckDBIngester:** Manages database connections and data loading

**Key Functions:**
```python
DuckDBIngester.connect()
  - Establish DuckDB connection
  - Install httpfs extension

DuckDBIngester.initialize_schema(schema_file: str) → bool
  - Execute all SQL statements from 01_schema.sql
  - Create tables and indexes

DuckDBIngester.load_speed_cameras(parquet_file: str) → int
  - Load speed camera violations into fct_violations

DuckDBIngester.load_traffic_violations(parquet_file: str) → int
  - Load traffic violations into fct_violations

ingest_pipeline(duckdb_path, schema_file, cleaned_dir, fresh_start) → bool
  - Complete pipeline: connect → schema → load → compute
```

**Database Output:**
- `fct_violations` (145,000+ rows)
- `dim_driver`, `dim_violation_type`, `dim_time`
- `agg_repeat_offenders` (aggregate table)

**CLI Usage:**
```bash
python src/ingestion.py \
  --duckdb-path ../data/duckdb/test.duckdb \
  --cleaned-dir ../data/cleaned \
  --schema-file ./sql/01_schema.sql \
  --fresh
```

---

### `src/super_speeder_detector.py` - Detection Engine

**Purpose:** Identify drivers meeting super speeder and warning thresholds

**Key Classes:**
- **SuperSpeederDetector:** Queries DuckDB and applies detection logic

**Key Methods:**
```python
SuperSpeederDetector.detect_super_speeders() → Tuple[List[Dict], List[Dict], Dict]
  Returns:
    - super_speeders: List of 1,332+ drivers meeting thresholds
    - warning_drivers: List of 227+ drivers approaching thresholds
    - stats: Summary statistics

SuperSpeederDetector.get_ingestion_stats() → Dict
  Returns:
    - total_violations, unique_drivers, unique_plates
    - date_range, violation breakdown by source
```

**Detection Logic:**

**Super Speeder:** Driver qualifies if:
$$\text{Speed Camera Tickets (12mo)} \geq 16 \quad \text{OR} \quad \text{Violation Points (18mo)} \geq 11$$

**Warning Driver:** Driver approaches if:
$$12 \leq \text{Speed Camera Tickets} < 16 \quad \text{OR} \quad 8 \leq \text{Points} < 11$$

**SQL Queries:** Dynamic temporal queries using date subtraction

---

### `sql/01_schema.sql` - Database Schema

**Purpose:** Define complete DuckDB warehouse structure

**Tables Created:**

1. **fct_violations** (Fact Table)
   - Central table with 145,000+ violation records
   - Columns: summons_number, driver_id, violation_code, points_assessed, violation_date, data_source, etc.

2. **dim_driver** (Driver Dimension)
   - 77,475 unique drivers
   - Columns: driver_id, registration_state

3. **dim_violation_type** (Violation Dimension)
   - Categorical violations (speeding, unsafe speed, etc.)

4. **dim_time** (Time Dimension)
   - Date hierarchy for temporal analysis

5. **agg_repeat_offenders** (Aggregate)
   - Pre-computed violation counts per driver
   - Optimizes detection queries

6. **agg_risk_scores_by_location** (Aggregate)
   - Geographic violation patterns

**Key Indexes:** driver_id, violation_date, data_source

---

### `tests/test_super_speeder_detector.py` - Unit Tests

**Purpose:** Validate detection logic and data integrity

**Test Coverage:**
```python
test_detect_super_speeders()
  - Verify count matches expected threshold

test_license_plate_not_null_super_speeders()
  - All drivers have valid license plates

test_license_plate_matches_driver_id()
  - Data model integrity check

test_warning_drivers_count()
  - Warning threshold logic validation

test_unique_plates_count()
  - Distinct plate count accuracy

test_get_ingestion_stats()
  - Statistics accuracy

test_driver_details_has_license_plate()
  - Individual driver view has data
```

**Run Tests:**
```bash
cd /path/to/project/backend
python -m pytest tests/ -v
```

**Results:** All 7 tests passing on sample data (1,332 super speeders, 227 warning drivers)

---

## Data Flow Diagram

```
[User CSV Upload]
         ↓
[app.py POST /upload]
         ↓
[cleaning.py: validate & standardize]
         ↓
[Parquet files: data/cleaned/]
         ↓
[ingestion.py: load into DuckDB]
         ↓
[DuckDB database: data/duckdb/test.duckdb]
         ↓
[super_speeder_detector.py: query & detect]
         ↓
[results.html: display findings]
```

---

## Configuration & Paths

**Relative to backend root (`backend/`):**

```python
# In app.py
BASE_DIR = Path(__file__).parent  # backend/
ROOT_DIR = BASE_DIR.parent       # project/

TEMPLATES_DIR = ROOT_DIR / "frontend" / "templates"
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
DUCKDB_PATH = DATA_DIR / "duckdb" / "test.duckdb"
SCHEMA_FILE = BASE_DIR / "sql" / "01_schema.sql"
```

---

## Performance Notes

- **Query time:** ~0.5-2s per 200-record upload
- **DuckDB:** Columnar storage optimizes aggregations
- **Parquet caching:** Avoids repeated CSV parsing
- **Indexes:** On driver_id and violation_date for fast filtering

---

## Dependencies

```
fastapi==0.104.1
uvicorn==0.24.0
duckdb==0.9.2
pandas==2.1.3
jinja2==3.1.2
python-multipart==0.0.6
```

Install with:
```bash
pip install -r requirements.txt
# or
uv sync
```

---

## Future Enhancements

1. **Real-time Monitoring:** WebSocket updates for live violations
2. **ML Models:** Predict recidivism and intervention success
3. **API Integration:** Connect to DMV systems
4. **Batch Processing:** Handle datasets 100,000+ rows
5. **Audit Trail:** Log all operations for accountability

