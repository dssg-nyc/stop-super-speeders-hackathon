"""
NYC Traffic Violations ETL Script
Reads all traffic violations files and combines them into a single pandas DataFrame
"""

import pandas as pd
from pathlib import Path


def load_all_traffic_violations():
    """
    Load all NYC traffic violations files into a single pandas DataFrame.

    Returns:
        pd.DataFrame: Combined dataframe with all traffic violations data
    """
    # Define the base directory (relative to scripts folder)
    data_dir = Path(__file__).parent.parent / "data" / "opendata"

    # List all traffic violations files
    traffic_files = [
        data_dir / "nyc_traffic_violations_historic.parquet",
        data_dir / "test1_nyc_traffic_violations.json",
        data_dir / "test2_nyc_traffic_violations.csv",
        data_dir / "test3_nyc_traffic_violations.csv"
    ]

    # Read each file into a dataframe
    dfs = []

    for file_path in traffic_files:
        if file_path.exists():
            print(f"Reading {file_path.name}...")

            if file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
                print("historical dtypes:")
                print(df.dtypes)
                print("------------")
            elif file_path.suffix == ".json":
                df = pd.read_json(file_path, lines=True)
                print(df.dtypes)
            elif file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
                print(df.dtypes)
            else:
                print(f"Skipping unsupported file type: {file_path.name}")
                continue

            print(f"Read {len(df):,} rows from {file_path.name}")
            dfs.append(df)
        else:
            print(f"  L File not found: {file_path.name}")

    # Combine all dataframes
    if dfs:
        traffic_violations_df = pd.concat(dfs, ignore_index=True)
        print(f" Combined DataFrame Summary:")
        print(f"  - Total rows: {len(traffic_violations_df):,}")
        print(f"  - Total columns: {len(traffic_violations_df.columns)}")
        print(f"  - Columns: {list(traffic_violations_df.columns)}")
        return traffic_violations_df
    else:
        print("L No dataframes were loaded")
        return pd.DataFrame()


if __name__ == "__main__":
    # Load all traffic violations data
    df = load_all_traffic_violations()

    # Display basic info
    print("\n" + "="*80)
    print("DataFrame Info:")
    print("="*80)
    print(df.info())

    print("\n" + "="*80)
    print("First 10 rows:")
    print("="*80)
    print(df.head(10))

    print("\n" + "="*80)
    print("Data types:")
    print("="*80)
    print(df.dtypes)

    # Write dtypes to CSV file
    dtypes_df = pd.DataFrame({
        'Column': df.dtypes.index,
        'Data Type': df.dtypes.values
    })
    output_file = Path(__file__).parent.parent / "data" / "dtypes_summary.csv"
    dtypes_df.to_csv(output_file, index=False)
    print(f"\nData types written to: {output_file}")
