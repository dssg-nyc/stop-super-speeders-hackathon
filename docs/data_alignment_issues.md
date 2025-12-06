# Data Alignment Issues

This document outlines the schema differences and data quality issues found across the different data sources for the Stop Super Speeders hackathon.

## Speed Cameras Data

### Schema Comparison

| Column | Historic (parquet) | Test1 (JSON) | Test2 (CSV) | Test3 (CSV) |
|--------|-------------------|--------------|-------------|-------------|
| summons_number | BIGINT | BIGINT | `Summons Number` BIGINT | BIGINT |
| plate | VARCHAR | VARCHAR | `Plate` VARCHAR | VARCHAR |
| state | VARCHAR | VARCHAR | `State` VARCHAR | VARCHAR |
| license_type | VARCHAR | VARCHAR | `License Type` VARCHAR | VARCHAR |
| county | VARCHAR | VARCHAR | `County` VARCHAR | VARCHAR |
| issuing_agency | VARCHAR | VARCHAR | `Issuing Agency` VARCHAR | VARCHAR |
| violation | VARCHAR | VARCHAR | `Violation` VARCHAR | VARCHAR |
| violation_status | VARCHAR | VARCHAR | `Violation Status` VARCHAR | VARCHAR |
| violation_time | VARCHAR | VARCHAR | `Violation Time` VARCHAR | VARCHAR |
| precinct | BIGINT | BIGINT | **MISSING** | BIGINT |
| issue_date | TIMESTAMP WITH TZ | VARCHAR | **SPLIT: Issue Year/Month/Day** | `issued_date` VARCHAR |
| judgment_entry_date | TIMESTAMP WITH TZ | JSON | `Judgment Entry Date` VARCHAR | VARCHAR |
| created_at | TIMESTAMP WITH TZ | VARCHAR | `Created At` TIMESTAMP | TIMESTAMP |
| fine_amount | DOUBLE | DOUBLE | `Fine Amount` DOUBLE | DOUBLE |
| penalty_amount | DOUBLE | DOUBLE | `Penalty Amount` DOUBLE | DOUBLE |
| interest_amount | DOUBLE | DOUBLE | `Interest Amount` DOUBLE | DOUBLE |
| reduction_amount | DOUBLE | DOUBLE | `Reduction Amount` DOUBLE | DOUBLE |
| payment_amount | DOUBLE | DOUBLE | `Payment Amount` DOUBLE | DOUBLE |
| amount_due | DOUBLE | DOUBLE | `Amount Due` DOUBLE | DOUBLE |

### Issues

1. **Column naming inconsistency**
   - Test2 uses Title Case with spaces (e.g., `Summons Number`)
   - Test3 uses `issued_date` instead of `issue_date`

2. **Date format differences**
   - Historic: Proper TIMESTAMP WITH TIME ZONE
   - Test1: Dates stored as VARCHAR strings
   - Test2: `issue_date` split into separate `Issue Year`, `Issue Month`, `Issue Day` columns
   - Test3: `issued_date` as VARCHAR

3. **Missing columns**
   - Test2 is missing `precinct` column
   - Test3 has extra columns: `api_version`, `issued_date`

---

## Traffic Violations Data

### Schema Comparison

| Column | Historic (parquet) | Test1 (JSON) | Test2 (CSV) | Test3 (CSV) |
|--------|-------------------|--------------|-------------|-------------|
| license_id | VARCHAR | VARCHAR | **MISSING** | `lic_id` VARCHAR |
| county | VARCHAR | VARCHAR | `County` VARCHAR | VARCHAR |
| age | BIGINT | BIGINT | `Age` BIGINT | BIGINT |
| birth_date | DATE | DATE | **SPLIT: Birth Year/Month** | `dob_formatted` DATE |
| violation_code | VARCHAR | VARCHAR | `Violation Code` VARCHAR | `v_code` VARCHAR |
| violation_year | BIGINT | BIGINT | `Violation Year` BIGINT | `v_year` BIGINT |
| violation_month | BIGINT | BIGINT | `Violation Month` BIGINT | `v_month` BIGINT |
| points | BIGINT | BIGINT | `Points` BIGINT | BIGINT |

### Issues

1. **CRITICAL: Test2 is missing `license_id`**
   - This is the primary key for identifying drivers
   - Without `license_id`, Test2 violations cannot be linked to specific drivers
   - **Impact:** ~25,000 violation records cannot be attributed to drivers

2. **Column naming inconsistency**
   - Test2 uses Title Case with spaces
   - Test3 uses abbreviated names: `lic_id`, `v_code`, `v_year`, `v_month`, `dob_formatted`

3. **Date format differences**
   - Historic/Test1: `birth_date` as proper DATE type
   - Test2: Split into `Birth Year` and `Birth Month` (no day!)
   - Test3: `dob_formatted` as DATE

4. **Extra columns in Test3**
   - `meta_sys_version` - system metadata

---

## Impact on Deliverables

### Drivers Table
- **Blocked for Test2:** Cannot calculate driver-level metrics for Test2 data
- **Workaround:** Exclude Test2 from driver calculations, or generate synthetic license_id (not recommended)

### Vehicle/Plate Table
- Speed camera data has `plate` in all sources - no issues
- All violations can be counted for plates

### Threshold Calculations
- 11+ points in 24 months (drivers): Will be incomplete without Test2
- 16 tickets in 12 months (plates): Should work correctly

---

## Recommendations

1. **Request corrected Test2 violations data** with `license_id` column
2. **For the hackathon:** Proceed with available data, document the gap
3. **Add data quality tests** to catch similar issues in future batches
4. **Consider generating synthetic IDs** only as a last resort for demonstration purposes
