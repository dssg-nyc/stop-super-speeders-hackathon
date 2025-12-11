# Data Architecture Documentation

## Overview

The data folder (`data/`) contains all datasets, database files, and processed outputs for the SAFENY system. It's organized into three subdirectories with clear separation of concerns.

---

## Folder Structure

```
data/
├── raw/                          # Raw and staging data
│   ├── demo/                    # Sample datasets for testing
│   │   ├── demo_speed_cameras.csv
│   │   └── demo_traffic_violations.csv
│   ├── uploads/                 # User-uploaded CSV files (timestamped)
│   ├── *.csv & *.parquet        # Historic raw data files
│   └── RNCleaning.py            # Legacy cleaning script
├── cleaned/                      # Processed, validated data
│   ├── cleaned_speed_cameras.parquet
│   ├── cleaned_traffic_violations.parquet
│   └── exports/                 # Analysis exports
└── duckdb/                       # Database files
    └── test.duckdb              # DuckDB warehouse (145,000+ rows)
```

---

## `raw/` - Raw Data Directory

**Purpose:** Store unprocessed CSV files and demo datasets

### Subdirectories

#### `demo/` - Sample Datasets
```
demo_speed_cameras.csv       (200 rows)
demo_traffic_violations.csv  (200 rows)
```

**Purpose:** Test data for demonstration and development

**Usage:**
```bash
python backend/src/cleaning.py \
  --input-dir data/raw/demo \
  --output-dir data/cleaned
```

**Schema:**

**Speed Cameras (demo_speed_cameras.csv)**
```
Columns: Summons Number, Plate ID, Registration State, 
         Issue Date, Violation, Fine Amount
Rows: 200 sample violations
Date Range: October - November 2025
```

**Traffic Violations (demo_traffic_violations.csv)**
```
Columns: Summons Number, License, Issue Date, 
         Violation Description, Points, Fine Amount
Rows: 200 sample violations
Date Range: October - November 2025
```

#### `uploads/` - User-Uploaded Files
```
20251206_155431/
  ├── user_file_1.csv
  └── user_file_2.csv
20251206_160830/
  └── another_upload.csv
... (timestamped directories)
```

**Structure:**
- Each upload creates a timestamped directory
- Format: `YYYYMMDD_HHMMSS/`
- Preserves original filenames

**Lifecycle:**
1. File uploaded → saved to timestamped dir
2. File validated → processed by cleaning.py
3. Output → stored in `data/cleaned/`
4. Original upload retained (audit trail)

### Historic Raw Data Files

**Available datasets:**

| File | Rows | Format | Purpose |
|------|------|--------|---------|
| `test1_nyc_speed_cameras.csv` | Sample | CSV | Development |
| `test1_nyc_traffic_violations.csv` | Sample | CSV | Development |
| `test2_nyc_speed_cameras.csv` | Sample | CSV | Development |
| `test2_nyc_traffic_violations.csv` | Sample | CSV | Development |
| `test3_nyc_speed_cameras.csv` | Sample | CSV | Development |
| `test3_nyc_traffic_violations.csv` | Sample | CSV | Development |
| `nyc_speed_cameras_historic.parquet` | 77,000+ | Parquet | Historic data |
| `nyc_traffic_violations_historic.parquet` | 68,000+ | Parquet | Historic data |
| `test1_nyc_speed_cameras.json` | Sample | JSON | Format example |
| `test1_nyc_traffic_violations.json` | Sample | JSON | Format example |

---

## `cleaned/` - Processed Data Directory

**Purpose:** Store validated, standardized data ready for analysis

### Files

#### `cleaned_speed_cameras.parquet`

**Format:** Apache Parquet (columnar, compressed)

**Columns after cleaning:**
```
summons_number      (STRING)  - Unique violation ID
plate               (STRING)  - License plate
registration_state  (STRING)  - Vehicle registration state
issued_date         (DATE)    - Date of violation
violation           (STRING)  - Violation description
fine_amount         (DECIMAL) - Fine amount in dollars
county              (STRING)  - County of violation
precinct            (INTEGER) - Precinct code (if available)
```

**Data Quality:**
- Null rate: < 1% (critical fields)
- Duplicate rows: 0% (removed during cleaning)
- Outliers: Checked (extreme fine amounts flagged)

**Statistics:**
- Total rows: 145,000+
- Unique plates: 55,506
- Date range: Oct 1, 2025 - Nov 24, 2025
- Average fine: $65.00

#### `cleaned_traffic_violations.parquet`

**Columns after cleaning:**
```
summons_number       (STRING)  - Unique violation ID
license_id           (STRING)  - Driver license ID
issue_date           (DATE)    - Date of violation
violation_description(STRING)  - Violation type
points_assessed      (INTEGER) - Points on license
fine_amount          (DECIMAL) - Fine amount in dollars
violation_code       (STRING)  - Code for violation type
```

**Data Quality:**
- Null rate: < 2%
- Point values: Valid range 0-25
- Duplicate rows: 0%

**Statistics:**
- Total rows: 145,000+
- Unique drivers: 77,475
- Date range: Oct 1, 2025 - Nov 24, 2025
- Average points: 3.2

### Parquet Format Benefits

```
Why Parquet instead of CSV?

✓ Compression: 10x smaller file size
✓ Speed: Columnar format → faster aggregations
✓ Typing: Schema enforcement (no type inference)
✓ Compatibility: Works with DuckDB, Pandas, Arrow
✓ Caching: Avoid re-parsing from CSV
```

### `exports/` - Analysis Outputs

**Purpose:** Store results and exports from analysis

**Example exports:**
```
reports/
├── super_speeders_2025-12-06.csv
├── violation_summary.xlsx
└── geographic_heatmap.geojson
```

---

## `duckdb/` - Database Directory

**Purpose:** Store the analytical data warehouse

### `test.duckdb` - Main Database File

**What it contains:**

1. **Fact Tables**
   ```sql
   fct_violations (145,000+ rows)
   - Central fact table with all violations
   - Columns: violation_id, driver_id, violation_code, 
             points_assessed, violation_date, data_source, ...
   ```

2. **Dimension Tables**
   ```sql
   dim_driver (77,475 rows)
   - Driver dimension
   - Columns: driver_id, registration_state, violation_count
   
   dim_violation_type (50 rows)
   - Violation categories
   - Columns: violation_code, violation_description, severity
   
   dim_time (365 rows)
   - Date hierarchy
   - Columns: date, year, month, day, quarter
   ```

3. **Aggregate Tables**
   ```sql
   agg_repeat_offenders (77,475 rows)
   - Pre-computed violation counts per driver
   - Columns: driver_id, violation_count, recent_violations_count,
              total_points, last_violation_date
   
   agg_risk_scores_by_location (varies)
   - Geographic violation patterns
   - Columns: location, violation_count, avg_severity
   ```

### Database Size

```
File: test.duckdb
Size: ~50-100 MB (depends on data)
Rows: 145,000+ violation records
Compression: DuckDB native compression
```

### Querying Examples

```sql
-- Count super speeders
SELECT COUNT(DISTINCT driver_id) as super_speeder_count
FROM fct_violations
WHERE violation_date >= CURRENT_DATE - INTERVAL 12 MONTH
GROUP BY driver_id
HAVING COUNT(*) >= 16;

-- Get violation distribution
SELECT violation_code, COUNT(*) as count
FROM fct_violations
GROUP BY violation_code
ORDER BY count DESC;

-- Average violations per driver
SELECT AVG(violation_count) as avg_violations
FROM agg_repeat_offenders;
```

### Backup & Recovery

**Regular backups recommended:**
```bash
# Backup
cp data/duckdb/test.duckdb data/duckdb/test.duckdb.backup_$(date +%Y%m%d)

# Restore
cp data/duckdb/test.duckdb.backup_20251210 data/duckdb/test.duckdb
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Lifecycle                            │
└─────────────────────────────────────────────────────────────┘

[1. Raw Data]
  ├── data/raw/demo/ (sample files)
  ├── data/raw/uploads/ (user uploads)
  └── data/raw/*.csv (historic files)
           ↓
[2. Cleaning Pipeline]
  src/cleaning.py validates & standardizes
           ↓
[3. Cleaned Data]
  ├── data/cleaned/cleaned_speed_cameras.parquet
  └── data/cleaned/cleaned_traffic_violations.parquet
           ↓
[4. Ingestion Pipeline]
  src/ingestion.py loads into DuckDB
           ↓
[5. Analytical Database]
  data/duckdb/test.duckdb
  ├── fct_violations (145,000+ rows)
  ├── dim_driver (77,475 unique)
  ├── agg_repeat_offenders
  └── (other dimension tables)
           ↓
[6. Detection Engine]
  src/super_speeder_detector.py queries database
           ↓
[7. Results Display]
  results.html shows findings to users
```

---

## Storage Optimization

### Current Usage

```
data/raw/
  ├── demo/                    ~500 KB
  ├── uploads/                 ~200 MB (timestamped uploads)
  └── historic/                ~400 MB (parquet files)
  Total: ~600 MB

data/cleaned/
  ├── cleaned_speed_cameras.parquet    ~30 MB
  ├── cleaned_traffic_violations.parquet ~25 MB
  └── exports/                         ~50 MB
  Total: ~105 MB

data/duckdb/
  └── test.duckdb             ~75 MB
  Total: ~75 MB

Grand Total: ~780 MB
```

### Cleanup Recommendations

**To save space:**
1. Archive old `uploads/` directories (> 30 days)
2. Compress historic raw files (test1, test2, test3)
3. Keep only latest cleaned parquet files

---

## Future Data Features

1. **Live Data Feeds:** Real-time violation imports from NYC Open Data
2. **Incremental Ingestion:** Append-only updates (no full reload)
3. **Data Validation Dashboard:** Monitor cleaning metrics
4. **Archival:** Move old uploads to cold storage
5. **Time-series Analysis:** Historical trend tracking
6. **Data Versioning:** Git-like tracking of dataset versions

---

## Accessing Data Programmatically

### Python Examples

**Load cleaned Parquet:**
```python
import pandas as pd

speed_cameras = pd.read_parquet('data/cleaned/cleaned_speed_cameras.parquet')
print(speed_cameras.head())
```

**Query DuckDB:**
```python
import duckdb

conn = duckdb.connect('data/duckdb/test.duckdb')
result = conn.execute("""
  SELECT driver_id, COUNT(*) as violations
  FROM fct_violations
  GROUP BY driver_id
  ORDER BY violations DESC
  LIMIT 10
""").fetch_all()
```

**CLI Examples:**
```bash
# Query database directly
duckdb data/duckdb/test.duckdb "SELECT COUNT(*) FROM fct_violations"

# List all tables
duckdb data/duckdb/test.duckdb ".tables"
```

---

## Data Retention Policy

| Type | Retention | Location |
|------|-----------|----------|
| Raw uploads | 90 days | `data/raw/uploads/` |
| Cleaned data | Permanent | `data/cleaned/` |
| Database | Permanent | `data/duckdb/` |
| Exports | 180 days | `data/cleaned/exports/` |
| Backups | 1 year | Archive storage |

