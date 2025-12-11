# Notebooks Documentation

## Overview

The notebooks folder (`notebooks/`) contains Jupyter analysis notebooks for exploring data, validating findings, and documenting analysis workflows.

---

## Folder Structure

```
notebooks/
├── Hackathon.ipynb              # Main analysis and exploration
├── 02_analysis.ipynb            # Advanced analysis workflows
└── README.md                    # Notebook guide
```

---

## `Hackathon.ipynb` - Main Analysis Notebook

**Purpose:** Primary exploration and analysis of violation data

**Key Sections:**

### 1. Setup & Configuration
```python
# Environment
DATA_DIR = "../data/raw"
BASE_URL = "https://fastopendata.org/dssg-safestreets"

# Libraries
import pandas as pd
import numpy as np
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
```

### 2. Data Loading
**Loads from:**
- Speed camera CSV files
- Traffic violation CSV files
- Historic parquet datasets

**Outputs:**
```python
speed_cameras_df   # DataFrame with speed violations
violations_df      # DataFrame with traffic violations
combined_df        # Merged dataset for analysis
```

### 3. Exploratory Data Analysis (EDA)

**Analyses included:**
- Distribution of violations by type
- Violations per driver (histogram)
- Temporal patterns (violations over time)
- Geographic distribution (if location data available)
- Fine amount statistics

**Visualizations:**
```
- Histogram: Violation count per driver
- Time series: Violations by date
- Box plot: Fine amount distribution
- Bar chart: Top 10 violation types
```

### 4. Data Cleaning Validation

**Checks performed:**
```python
# Check for nulls
print(speed_cameras_df.isnull().sum())

# Check for duplicates
duplicates = speed_cameras_df.duplicated(subset=['summons_number'])
print(f"Duplicates: {duplicates.sum()}")

# Validate date ranges
print(speed_cameras_df['issued_date'].min())
print(speed_cameras_df['issued_date'].max())

# Check fine amounts
print(speed_cameras_df['fine_amount'].describe())
```

### 5. Super Speeder Detection Validation

**Manual queries to verify detection logic:**
```python
# Count drivers with 16+ speed camera tickets
super_speeders = speed_cameras_df.groupby('plate').size()
super_speeders = super_speeders[super_speeders >= 16]
print(f"Super speeders (cameras): {len(super_speeders)}")

# Count drivers with 11+ violation points
violations_grouped = violations_df.groupby('license')['points'].sum()
super_speeders_points = violations_grouped[violations_grouped >= 11]
print(f"Super speeders (points): {len(super_speeders_points)}")
```

### 6. Summary Statistics

**Generates summary table:**
```
Total violations:        145,000+
Unique drivers:          77,475
Unique license plates:   55,506
Date range:             Oct 1 - Nov 24, 2025
Speed camera tickets:    70,000+
Officer violations:      75,000+
Average points per violation: 3.2
```

### 7. Export Results

**Exports to:**
```python
# CSV exports
summary_stats.to_csv('../data/cleaned/exports/summary_stats.csv')
super_speeders.to_csv('../data/cleaned/exports/super_speeders.csv')

# Visualization exports (optional)
plt.savefig('../data/cleaned/exports/violation_distribution.png')
```

---

## `02_analysis.ipynb` - Advanced Analysis Notebook

**Purpose:** Deeper analysis workflows and hypothesis testing

**Key Sections:**

### 1. DuckDB Connection

```python
import duckdb

# Connect to database
conn = duckdb.connect('../data/duckdb/test.duckdb')

# Query tables
drivers_df = conn.execute("""
  SELECT driver_id, COUNT(*) as violation_count
  FROM fct_violations
  GROUP BY driver_id
  ORDER BY violation_count DESC
""").fetch_df()

# Display results
print(drivers_df.head(10))
```

### 2. Temporal Analysis

**Time series analysis:**
```python
# Violations by month
monthly_violations = conn.execute("""
  SELECT DATE_TRUNC('month', violation_date) as month,
         COUNT(*) as violation_count
  FROM fct_violations
  GROUP BY month
  ORDER BY month
""").fetch_df()

# Plot
monthly_violations.set_index('month')['violation_count'].plot()
plt.title('Monthly Violation Trend')
plt.xlabel('Month')
plt.ylabel('Violation Count')
```

### 3. Violation Type Analysis

**Distribution by violation type:**
```python
# Top violations
top_violations = conn.execute("""
  SELECT violation_code, violation_description, COUNT(*) as count
  FROM fct_violations
  JOIN dim_violation_type ON fct_violations.violation_code = dim_violation_type.code
  GROUP BY violation_code, violation_description
  ORDER BY count DESC
  LIMIT 20
""").fetch_df()

# Visualize
top_violations.plot(x='violation_description', y='count', kind='barh')
```

### 4. Risk Score Analysis

**Analyze driver risk patterns:**
```python
# Get repeat offender scores
risk_scores = conn.execute("""
  SELECT driver_id, violation_count, total_points,
         CASE
           WHEN violation_count >= 16 THEN 'SUPER_SPEEDER'
           WHEN violation_count >= 12 THEN 'HIGH_RISK'
           WHEN violation_count >= 8 THEN 'MODERATE_RISK'
           ELSE 'LOW_RISK'
         END as risk_category
  FROM agg_repeat_offenders
  ORDER BY violation_count DESC
""").fetch_df()

# Risk distribution
risk_dist = risk_scores['risk_category'].value_counts()
print(risk_dist)
```

### 5. Geographic Analysis (if location data available)

```python
# Violations by precinct/location
location_analysis = conn.execute("""
  SELECT county, COUNT(*) as violation_count, AVG(fine_amount) as avg_fine
  FROM fct_violations
  WHERE county IS NOT NULL
  GROUP BY county
  ORDER BY violation_count DESC
""").fetch_df()

# Create map visualization (if coordinates available)
```

### 6. Hypothesis Testing

**Example hypotheses:**
```python
# H1: Speed camera violations are increasing over time
# H2: Certain violation types have higher point values
# H3: Geographic hotspots exist for speeding violations

# Use statistical tests (t-test, chi-square, etc.)
from scipy import stats

# Example: Compare violation counts by data source
speed_camera_mean = violations_by_source['SPEED_CAMERA'].mean()
officer_mean = violations_by_source['TRAFFIC_VIOLATION'].mean()

t_stat, p_value = stats.ttest_ind(
  violations_by_source['SPEED_CAMERA'],
  violations_by_source['TRAFFIC_VIOLATION']
)

print(f"T-statistic: {t_stat}, P-value: {p_value}")
```

### 7. Model Development (Future)

**Placeholder for predictive models:**
```python
# Predict driver behavior / recidivism
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

# Feature engineering
X = driver_features[['violation_count', 'total_points', 'months_active']]
y = driver_labels['is_recidivist']

# Train model
model = RandomForestClassifier()
model.fit(X, y)

# Predict on new data
predictions = model.predict(new_drivers)
```

---

## `README.md` - Notebook Guide

**Purpose:** Quick start guide for running and understanding notebooks

**Contents:**

```markdown
# Jupyter Notebooks Guide

## Quick Start

### Prerequisites
- Python 3.10+
- Jupyter installed: `pip install jupyter`
- DuckDB: `pip install duckdb`
- Pandas: `pip install pandas`

### Running Notebooks

1. **Start Jupyter**
   ```bash
   cd notebooks/
   jupyter notebook
   ```

2. **Open Hackathon.ipynb**
   - Click on file in browser
   - Run cells sequentially (Shift+Enter)
   - Observe outputs

### Data Requirements

Before running notebooks, ensure:
- `data/raw/` has CSV files OR
- `data/cleaned/` has Parquet files OR
- `data/duckdb/test.duckdb` exists

### Cell-by-Cell Breakdown

**Hackathon.ipynb:**

| Cell | Purpose | Dependencies |
|------|---------|---|
| 1 | Imports | None |
| 2 | Config | None |
| 3 | Load data | data/raw/ files |
| 4-6 | EDA | Loaded data |
| 7-10 | Validation | Loaded data |
| 11-15 | Detection logic | Loaded data |
| 16+ | Exports | Validated data |

### Common Issues

**Q: "Module not found: duckdb"**
A: Install: `pip install duckdb`

**Q: "FileNotFoundError: data/raw/..."**
A: Ensure you're in `notebooks/` directory or adjust paths

**Q: "No module named 'seaborn'"**
A: Install: `pip install seaborn matplotlib`
```

---

## Running Notebooks in VS Code

### Setup

1. **Install Jupyter extension in VS Code**
   - Search "Jupyter" in extensions
   - Install Microsoft's Jupyter extension

2. **Select Python kernel**
   - Open .ipynb file
   - Click "Select Kernel" (top right)
   - Choose your venv Python

### Executing Cells

```
Shift+Enter   - Run current cell and move to next
Ctrl+Enter    - Run current cell
Ctrl+Shift+P  - Command palette (run all cells, etc.)
```

---

## Analysis Workflow Example

**Typical analysis session:**

```
1. Open Hackathon.ipynb
   ↓
2. Run setup cells (1-3)
   - Loads libraries
   - Sets configuration
   ↓
3. Run data loading cell (4)
   - Imports CSVs
   - Creates DataFrames
   ↓
4. Run EDA cells (5-6)
   - Visualizes distributions
   - Prints summary stats
   ↓
5. Run validation cells (7-10)
   - Checks data quality
   - Validates schema
   ↓
6. Run detection logic (11-15)
   - Identifies super speeders
   - Counts warning drivers
   ↓
7. Export results (16+)
   - Save to CSV
   - Generate visualizations
   ↓
8. Done! Review findings
```

---

## Tips & Best Practices

### Notebook Organization

✓ **Good:**
```python
# === SECTION 1: DATA LOADING ===
# Clear markdown headers between sections
# One logical task per cell
# Descriptive variable names
```

✗ **Avoid:**
```python
# 100 lines of code in one cell
# No comments or organization
# Variable names like df1, df2, df3
```

### Memory Management

```python
# Clear memory after large operations
del large_dataframe
import gc
gc.collect()
```

### Reproducibility

```python
# Set random seed for consistent results
import numpy as np
np.random.seed(42)

# Document data assumptions
"""
This analysis assumes:
- Data covers Oct 1 - Nov 24, 2025
- Null values < 2%
- No data leakage between train/test
"""
```

### Performance

```python
# Use DuckDB for large datasets (faster)
# Avoid loading entire CSV if possible
result = duckdb.query("SELECT * FROM large_table LIMIT 1000").to_df()

# Cache expensive operations
@functools.lru_cache(maxsize=128)
def expensive_function(x):
    return process(x)
```

---

## Future Notebook Ideas

1. **Predictive Modeling:** Recidivism prediction
2. **Geographic Analysis:** Heatmaps of speeding hotspots
3. **Time Series Forecasting:** Predict future violation trends
4. **Causal Analysis:** Effect of ISA devices on recidivism
5. **Fairness Audit:** Bias detection in detection thresholds
6. **Cost-Benefit Analysis:** ROI of ISA program

