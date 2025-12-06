#!/usr/bin/env python3
"""
Run the violation tracking pipeline.

Processes both speed camera and traffic violation data to find
NEW violators who crossed their respective thresholds.

Usage:
    uv run python scripts/run_pipeline.py
"""

from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

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
TEST_BATCH = "test1"

CAMERA_FILES = [
    "test1_nyc_speed_cameras.json",
]

VIOLATION_FILES = [
    "test1_nyc_traffic_violations.json",
]
# =============================================================================


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
            # test2 format: split date columns
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
            # test3 format
            return pd.DataFrame({
                "issue_date": pd.to_datetime(df["issued_date"]).dt.date,
                "plate": df["plate"].str.upper(),
                "summons_number": df["summons_number"].astype("Int64"),
                "state": df["state"],
            })
        else:
            return pd.DataFrame({
                "issue_date": pd.to_datetime(df["issue_date"]).dt.date,
                "plate": df["plate"].str.upper(),
                "summons_number": df["summons_number"].astype("Int64"),
                "state": df["state"],
            })

    else:
        raise ValueError(f"Unsupported file type: {ext}")


def load_violation_file(file_path: Path) -> pd.DataFrame:
    """Load a traffic violation file and normalize to standard schema."""
    ext = file_path.suffix.lower()

    if ext == '.parquet':
        df = pd.read_parquet(file_path)
        return pd.DataFrame({
            "license_id": df["license_id"],
            "issue_date": pd.to_datetime(
                df["violation_year"].astype(str) + "-" + df["violation_month"].astype(str) + "-01"
            ).dt.date,
            "points": df["points"].astype("Int64"),
        })

    elif ext == '.json':
        df = pd.read_json(file_path, lines=True)
        return pd.DataFrame({
            "license_id": df["license_id"],
            "issue_date": pd.to_datetime(
                df["violation_year"].astype(str) + "-" + df["violation_month"].astype(str) + "-01"
            ).dt.date,
            "points": df["points"].astype("Int64"),
        })

    elif ext == '.csv':
        df = pd.read_csv(file_path)
        cols = [c.lower() for c in df.columns]

        if "violation_year" in cols:
            return pd.DataFrame({
                "license_id": df["license_id"],
                "issue_date": pd.to_datetime(
                    df["violation_year"].astype(str) + "-" + df["violation_month"].astype(str) + "-01"
                ).dt.date,
                "points": df["points"].astype("Int64"),
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

    # Load historical
    print(f"  Historical: {HISTORICAL_CAMERAS.name}")
    historical_df = load_camera_file(HISTORICAL_CAMERAS)

    # Load test files
    test_dfs = []
    for f in test_files:
        print(f"  Test file:  {f.name}")
        test_dfs.append(load_camera_file(f))

    test_df = pd.concat(test_dfs, ignore_index=True) if test_dfs else pd.DataFrame({
        "issue_date": pd.Series(dtype="object"),
        "plate": pd.Series(dtype="str"),
        "summons_number": pd.Series(dtype="Int64"),
        "state": pd.Series(dtype="str"),
    })

    # Execute SQL
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

    # Load historical
    print(f"  Historical: {HISTORICAL_VIOLATIONS.name}")
    historical_df = load_violation_file(HISTORICAL_VIOLATIONS)

    # Load test files
    test_dfs = []
    for f in test_files:
        print(f"  Test file:  {f.name}")
        test_dfs.append(load_violation_file(f))

    test_df = pd.concat(test_dfs, ignore_index=True) if test_dfs else pd.DataFrame({
        "license_id": pd.Series(dtype="str"),
        "issue_date": pd.Series(dtype="object"),
        "points": pd.Series(dtype="Int64"),
    })

    # Execute SQL
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

        # Export
        output_file = output_dir / "new_driver_violators.csv"
        result.to_csv(output_file, index=False)
        print(f"  Exported: {output_file}")

        if row_count > 0:
            print(f"\n  Top violators:")
            for _, row in result.head(5).iterrows():
                print(f"    {row['license_id']}: {row['total_points']} points ({row['violation_count']} violations)")

        return row_count

    finally:
        conn.close()


def main():
    print("\n" + "="*60)
    print("STOP SUPER SPEEDERS - VIOLATION TRACKING PIPELINE")
    print("="*60)

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
    print(f"  New plate violators:  {plate_count}")
    print(f"  New driver violators: {driver_count}")
    print(f"  Total new violators:  {plate_count + driver_count}")
    print("="*60)


if __name__ == "__main__":
    main()
