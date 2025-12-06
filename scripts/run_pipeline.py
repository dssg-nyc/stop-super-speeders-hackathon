#!/usr/bin/env python3
"""
Run the violation tracking pipeline.

Processes both speed camera and traffic violation data to find
NEW violators who crossed their respective thresholds.

Thresholds (NY Bill A.2299/S.4045):
  - Speed Cameras: 16+ tickets in trailing 12 months (by plate+state)
  - License Points: 11+ points in trailing 24 months (by license_id)

Usage:
    uv run python scripts/run_pipeline.py
"""

from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

import os
import dotenv
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional

dotenv.load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "opendata"
OUTPUT_DIR = PROJECT_ROOT / "data" / "exports"
SQL_DIR = PROJECT_ROOT / "notebooks" / "sql"

# Historical files
HISTORICAL_CAMERAS = DATA_DIR / "nyc_speed_cameras_historic.parquet"
HISTORICAL_VIOLATIONS = DATA_DIR / "nyc_traffic_violations_historic.parquet"

# SQL files
SQL_CAMERAS = SQL_DIR / "find_new_vehicle_violators.sql"
SQL_DRIVERS = SQL_DIR / "find_new_driver_violators.sql"

# =============================================================================
# ADD YOUR TEST FILES HERE
# =============================================================================
TEST_BATCH = "test2"

CAMERA_FILES = [
    "test2_nyc_speed_cameras.csv",
]

VIOLATION_FILES = [
    "test2_nyc_traffic_violations.csv",
]
# =============================================================================


# --- LLM Structure Definitions ---
class DateParsingRule(BaseModel):
    columns_used: List[str] = Field(description="List of columns needed to construct the date.")
    join_separator: str = Field(" ", description="Separator to join columns if multiple.")
    source_strptime_format: str = Field(..., description="Python strptime format matching the source.")

class ColumnPair(BaseModel):
    historical_column: str = Field(description="Column name from historical data.")
    new_upload_column: Optional[str] = Field(description="Matching column from new upload. None if no match.")

class MappingResult(BaseModel):
    mappings: List[ColumnPair] = Field(description="List of mappings for every historical column.")

def load_camera_file(file_path: Path) -> pd.DataFrame:
    """Load a speed camera file and normalize to standard schema."""
    ext = file_path.suffix.lower()

    if ext == '.parquet':
        df = pd.read_parquet(file_path)
        return pd.DataFrame({
            "issue_date": pd.to_datetime(df["issue_date"]).dt.date,
            "plate": df["plate"].str.upper(),
            "summons_number": df["summons_number"].astype("Int64"),
            "state": df["state"],
        })

    elif ext == '.json':
        df = pd.read_json(file_path, lines=True)
        return pd.DataFrame({
            "issue_date": pd.to_datetime(df["issue_date"], utc=True).dt.date,
            "plate": df["plate"].str.upper(),
            "summons_number": df["summons_number"].astype("Int64"),
            "state": df["state"],
        })

    elif ext == '.csv':
        df = pd.read_csv(file_path)
        cols = [c.lower() for c in df.columns]

        if "issue year" in cols:
            # test2 format: split date columns (Title Case)
            return pd.DataFrame({
                "issue_date": pd.to_datetime(
                    df[["Issue Year", "Issue Month", "Issue Day"]].rename(
                        columns={"Issue Year": "year", "Issue Month": "month", "Issue Day": "day"}
                    )
                ).dt.date,
                "plate": df["Plate"].str.upper(),
                "summons_number": df["Summons Number"].astype("Int64"),
                "state": df["State"],
            })
        elif "issued_date" in cols:
            # test3 format: DD-Mon-YYYY date
            return pd.DataFrame({
                "issue_date": pd.to_datetime(df["issued_date"], format="%d-%b-%Y").dt.date,
                "plate": df["plate"].str.upper(),
                "summons_number": df["summons_number"].astype("Int64"),
                "state": df["state"],
            })
        else:
            # Standard CSV format
            return pd.DataFrame({
                "issue_date": pd.to_datetime(df["issue_date"]).dt.date,
                "plate": df["plate"].str.upper(),
                "summons_number": df["summons_number"].astype("Int64"),
                "state": df["state"],
            })

    else:
        raise ValueError(f"Unsupported file type: {ext}")

def smart_load_and_normalize(file_path: Path, historical_df: pd.DataFrame, target_date_col: str) -> pd.DataFrame:
    """
    Dynamically loads a file and normalizes it to match the historical_df schema 
    using LLM inference for column mapping and date parsing.
    """
    # 1. Generic File Load
    ext = file_path.suffix.lower()
    if ext == '.parquet':
        df = pd.read_parquet(file_path)
    elif ext == '.json':
        df = pd.read_json(file_path, lines=True)
    elif ext == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported type: {ext}")
        
    # If the schema is already identical, skip LLM
    if set(df.columns) == set(historical_df.columns):
        return df

    # 2. LLM Column Mapping
    print(f"    ...Analysing schema for {file_path.name}...")
    
    prompt_mapping = f"""
    Map the columns from the 'New Upload' to the 'Historical Data'.
    Historical Columns: {list(historical_df.columns)}
    New Upload Sample: {df.head(3).to_markdown()}
    
    Requirements:
    1. Return a list of mappings.
    2. Every column from the Historical Data MUST appear in the output.
    3. If a historical column has no match, value is None.
    """
    
    response_map = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_mapping,
        config={"response_mime_type": "application/json", "response_json_schema": MappingResult.model_json_schema()},
    )
    mapping_rule = MappingResult.model_validate_json(response_map.text)
    
    # Apply Column Renaming
    rename_dict = {pair.new_upload_column: pair.historical_column 
                   for pair in mapping_rule.mappings 
                   if pair.new_upload_column is not None}
    df = df.rename(columns=rename_dict)

    # 3. LLM Date Parsing (if the target date column is missing or needs standardization)
    # We only run this if the specific target date column exists in the *mapped* df but might be dirty, 
    # or if we need to derive it from original columns that weren't mapped yet.
    
    # For robustness, we ask the LLM how to construct the specific target date column from the *original* df
    # logic, then assign it to the standardized name.
    
    prompt_date = f"""
    I need to standardize the date into column '{target_date_col}'.
    The target format is standard ISO 8601 (YYYY-MM-DD).
    
    Data Sample: {df.head(3).to_markdown()}
    
    Identify the columns containing date info and define a Python strptime parsing rule.
    """
    
    response_date = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_date,
        config={"response_mime_type": "application/json", "response_json_schema": DateParsingRule.model_json_schema()},
    )
    date_rule = DateParsingRule.model_validate_json(response_date.text)
    
    # Apply Date Transformation
    def parse_date(row):
        try:
            # Note: We use original columns if they exist, otherwise mapped columns
            values = [str(row[col]) for col in date_rule.columns_used if col in row]
            if not values: return None
            raw_string = date_rule.join_separator.join(values)
            dt = datetime.strptime(raw_string, date_rule.source_strptime_format)
            return dt.date() # Return python date object
        except:
            return None

    df[target_date_col] = df.apply(parse_date, axis=1)
    
    # 4. Filter to keep only historical columns
    final_cols = [c for c in historical_df.columns if c in df.columns]
    return df[final_cols]

def load_violation_file(file_path: Path) -> pd.DataFrame:
    """Load a traffic violation file and normalize to standard schema."""
    ext = file_path.suffix.lower()

    if ext == '.parquet':
        df = pd.read_parquet(file_path)
        return pd.DataFrame({
            "license_id": df["license_id"],
            "violation_year": df["violation_year"].astype("Int64"),
            "violation_month": df["violation_month"].astype("Int64"),
            "violation_code": df["violation_code"],
            "points": df["points"].astype("Int64"),
            "county": df["county"],
        })

    elif ext == '.json':
        df = pd.read_json(file_path, lines=True)
        return pd.DataFrame({
            "license_id": df["license_id"],
            "violation_year": df["violation_year"].astype("Int64"),
            "violation_month": df["violation_month"].astype("Int64"),
            "violation_code": df["violation_code"],
            "points": df["points"].astype("Int64"),
            "county": df["county"],
        })

    elif ext == '.csv':
        df = pd.read_csv(file_path)
        cols = [c.lower() for c in df.columns]

        # Test3 format: abbreviated column names (lic_id, v_code, v_year, v_month)
        if "lic_id" in cols or "v_code" in cols:
            return pd.DataFrame({
                "license_id": df["lic_id"],
                "violation_year": df["v_year"].astype("Int64"),
                "violation_month": df["v_month"].astype("Int64"),
                "violation_code": df["v_code"],
                "points": df["points"].astype("Int64"),
                "county": df["county"],
            })

        # Test2 format: Title Case columns (License Id, Violation Year, etc.)
        elif "violation year" in cols or "license id" in cols:
            return pd.DataFrame({
                "license_id": df["License Id"],
                "violation_year": df["Violation Year"].astype("Int64"),
                "violation_month": df["Violation Month"].astype("Int64"),
                "violation_code": df["Violation Code"],
                "points": df["Points"].astype("Int64"),
                "county": df["County"],
            })

        # Standard CSV format with license_id
        elif "violation_year" in cols:
            return pd.DataFrame({
                "license_id": df["license_id"],
                "violation_year": df["violation_year"].astype("Int64"),
                "violation_month": df["violation_month"].astype("Int64"),
                "violation_code": df["violation_code"],
                "points": df["points"].astype("Int64"),
                "county": df["county"],
            })
        else:
            raise ValueError(f"Unknown CSV schema for traffic violations: {file_path}")

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def run_camera_pipeline(test_files: list[Path], output_dir: Path) -> int:
    """Find NEW speed camera violators (16+ tickets in 12 months)."""
    print("\n" + "-"*60)
    print("SPEED CAMERA VIOLATORS (16+ tickets in 12 months)")
    print("-"*60)

    # 1. Load Historical Data
    print(f"  Historical: {HISTORICAL_CAMERAS.name}")
    # Load raw to get schema, then normalize strictly
    hist_raw = pd.read_parquet(HISTORICAL_CAMERAS)
    historical_df = pd.DataFrame({
        "issue_date": pd.to_datetime(hist_raw["issue_date"]).dt.date,
        "plate": hist_raw["plate"].str.upper(),
        "summons_number": hist_raw["summons_number"].astype("Int64"),
        "state": hist_raw["state"],
    })
    print(f"    Loaded {len(historical_df):,} records")

    # 2. Load & Normalize Test Files Dynamically
    test_dfs = []
    for f in test_files:
        print(f"  Test file:  {f.name}")
        try:
            # LLM magic happens here:
            df = smart_load_and_normalize(f, historical_df, target_date_col="issue_date")
            
            # Final Type Enforcement
            df["plate"] = df["plate"].str.upper()
            df["summons_number"] = df["summons_number"].astype("Int64")
            
            print(f"    Loaded {len(df):,} normalized records")
            test_dfs.append(df)
        except Exception as e:
            print(f"    [ERROR] Could not process {f.name}: {e}")

    # Handle case with no valid data
    if not test_dfs:
        print("    No valid test data found.")
        test_df = pd.DataFrame(columns=historical_df.columns)
    else:
        test_df = pd.concat(test_dfs, ignore_index=True)

    # 3. Execute SQL Analysis (Unchanged)
    conn = duckdb.connect(':memory:')
    try:
        conn.register("historical_data", historical_df)
        conn.register("test_data", test_df)

        sql = SQL_CAMERAS.read_text()
        result = conn.execute(sql).fetchdf()
        row_count = len(result)

        print(f"\n  Found {row_count} NEW plate violators")

        # Add metadata columns
        result["source_files"] = ", ".join([f.name for f in test_files])
        result["historical_file"] = HISTORICAL_CAMERAS.name
        result["run_timestamp"] = datetime.now().isoformat()

        # Export
        output_file = output_dir / "new_plate_violators.csv"
        result.to_csv(output_file, index=False)
        print(f"  Exported: {output_file}")

        if row_count > 0:
            print(f"\n  Top violators:")
            for _, row in result.head(5).iterrows():
                print(f"    {row['plate']} ({row['state']}): {row['ticket_count']} tickets")

        return row_count

    finally:
        conn.close()


def run_driver_pipeline(test_files: list[Path], output_dir: Path) -> int:
    """Find NEW driver violators (11+ points in 24 months)."""
    print("\n" + "-"*60)
    print("DRIVER VIOLATORS (11+ points in 24 months)")
    print("-"*60)

    # 1. Load Historical Data
    print(f"  Historical: {HISTORICAL_VIOLATIONS.name}")
    hist_raw = pd.read_parquet(HISTORICAL_VIOLATIONS)
    historical_df = pd.DataFrame({
        "license_id": hist_raw["license_id"],
        "violation_year": hist_raw["violation_year"].astype("Int64"),
        "violation_month": hist_raw["violation_month"].astype("Int64"),
        "violation_code": hist_raw["violation_code"],
        "points": hist_raw["points"].astype("Int64"),
        "county": hist_raw["county"],
    })
    print(f"    Loaded {len(historical_df):,} records")

    # 2. Load & Normalize Test Files Dynamically
    test_dfs = []
    for f in test_files:
        print(f"  Test file:  {f.name}")
        try:
            # We use a temporary date column to catch any full date strings
            df = smart_load_and_normalize(f, historical_df, target_date_col="temp_parsed_date")

            # Post-Processing: Handle Year/Month split if missing
            if "violation_year" not in df.columns or df["violation_year"].isnull().all():
                if "temp_parsed_date" in df.columns:
                    print("    ...Deriving Year/Month from parsed date column...")
                    df["violation_year"] = pd.to_datetime(df["temp_parsed_date"]).dt.year
                    df["violation_month"] = pd.to_datetime(df["temp_parsed_date"]).dt.month
            
            # Clean up temp column if it exists
            if "temp_parsed_date" in df.columns:
                df = df.drop(columns=["temp_parsed_date"])

            # Filter valid licenses
            valid_df = df[df["license_id"].notna()].copy()
            
            # Final Type Enforcement
            valid_df["violation_year"] = valid_df["violation_year"].astype("Int64")
            valid_df["violation_month"] = valid_df["violation_month"].astype("Int64")
            valid_df["points"] = valid_df["points"].astype("Int64")

            print(f"    Loaded {len(valid_df):,} valid records")
            test_dfs.append(valid_df)
        except Exception as e:
            print(f"    [ERROR] Could not process {f.name}: {e}")

    if not test_dfs:
        print("    No valid test data found.")
        test_df = pd.DataFrame(columns=historical_df.columns)
    else:
        test_df = pd.concat(test_dfs, ignore_index=True)

    # 3. Execute SQL Analysis (Unchanged)
    conn = duckdb.connect(':memory:')
    try:
        conn.register("historical_data", historical_df)
        conn.register("test_data", test_df)

        sql = SQL_DRIVERS.read_text()
        result = conn.execute(sql).fetchdf()
        row_count = len(result)

        print(f"\n  Found {row_count} NEW driver violators")

        # Add metadata columns
        result["source_files"] = ", ".join([f.name for f in test_files])
        result["historical_file"] = HISTORICAL_VIOLATIONS.name
        result["run_timestamp"] = datetime.now().isoformat()

        # Export
        output_file = output_dir / "new_driver_violators.csv"
        result.to_csv(output_file, index=False)
        print(f"  Exported: {output_file}")

        if row_count > 0:
            print(f"\n  Top violators:")
            for _, row in result.head(5).iterrows():
                counties = row.get('counties', 'N/A')
                print(f"    {row['license_id']}: {row['total_points']} points - {counties}")

        return row_count

    finally:
        conn.close()


def main():
    print("\n" + "="*60)
    print("STOP SUPER SPEEDERS - VIOLATION TRACKING PIPELINE")
    print("="*60)
    print("Thresholds (NY Bill A.2299/S.4045):")
    print("  - Speed Cameras: 16+ tickets in trailing 12 months")
    print("  - License Points: 11+ points in trailing 24 months")

    # Create timestamped output folder
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_output_dir = OUTPUT_DIR / f"{TEST_BATCH}_{timestamp}"
    run_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nOutput folder: {run_output_dir.name}")

    # Resolve camera files
    camera_files = []
    for filename in CAMERA_FILES:
        path = DATA_DIR / filename
        if path.exists():
            camera_files.append(path)
        else:
            print(f"Warning: Camera file not found: {path}")

    # Resolve violation files
    violation_files = []
    for filename in VIOLATION_FILES:
        path = DATA_DIR / filename
        if path.exists():
            violation_files.append(path)
        else:
            print(f"Warning: Violation file not found: {path}")

    # Run pipelines
    plate_count = 0
    driver_count = 0

    if camera_files:
        plate_count = run_camera_pipeline(camera_files, run_output_dir)

    if violation_files:
        driver_count = run_driver_pipeline(violation_files, run_output_dir)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  New plate violators (SPEED_CAMERA):   {plate_count}")
    print(f"  New driver violators (LICENSE_POINTS): {driver_count}")
    print(f"  Total new violators:                   {plate_count + driver_count}")
    print(f"\nOutput directory: {run_output_dir}")
    print("="*60)


if __name__ == "__main__":
    main()
