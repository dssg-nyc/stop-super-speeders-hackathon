"""
NYC Traffic Violations ETL Script
Reads all traffic violations files and combines them into a single pandas DataFrame
"""

import json
import pandas as pd
from pathlib import Path


def load_all_traffic_violations(traffic_files):
    """
    Load all NYC traffic violations files into a single pandas DataFrame.

    Returns:
        pd.DataFrame: Combined dataframe with all traffic violations data
    """

    final_schema = ["license_id", "county", "violation_code", "violation_year", "violation_month", "points"]
    # Read each file into a dataframe
    dfs = []
    schema_mapping_path = Path(__file__).parent / "traffic_violations_column_mappings.json"
    with open(schema_mapping_path, 'r') as f:
        schema_mapping = json.load(f)
    for file_path in traffic_files:
        if file_path.exists():
            print(f"Reading {file_path.name}...")
            if file_path.suffix == ".parquet":
                df = pd.read_parquet(file_path)
            elif file_path.suffix == ".json":
                df = pd.read_json(file_path, lines=True)
            elif file_path.suffix == ".csv":
                df = pd.read_csv(file_path)
            else:
                print(f"Skipping unsupported file type: {file_path.name}")
                continue

            for col in df.columns:
                if schema_mapping.get(col) is None:
                    continue
                else:
                    df.rename(columns={col: schema_mapping[col]}, inplace=True)
            df_final = df[final_schema]
            dfs.append(df_final)
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
    # Define the base directory (relative to scripts folder)
    data_dir = Path(__file__).parent.parent / "data" / "opendata"
    # List all traffic violations files
    traffic_files_1 = [
        data_dir / "nyc_traffic_violations_historic.parquet",
        data_dir / "test1_nyc_traffic_violations.json",
    ]
    # List all traffic violations files
    traffic_files_2 = [
        data_dir / "nyc_traffic_violations_historic.parquet",
        data_dir / "test2_nyc_traffic_violations.csv",
    ]

    # List all traffic violations files
    traffic_files_3 = [
        data_dir / "nyc_traffic_violations_historic.parquet",
        data_dir / "test3_nyc_traffic_violations.csv"
    ]
    # Load all traffic violations data
    df1 = load_all_traffic_violations(traffic_files_1)
    df1.drop_duplicates(inplace=True)
    df2 = load_all_traffic_violations(traffic_files_2)
    df2.drop_duplicates(inplace=True)
    print(df2.equals(df1))
    df3 = load_all_traffic_violations(traffic_files_3)
    df3.drop_duplicates(inplace=True)
    print(df3.equals(df1))

    df1['datetime'] = pd.to_datetime(df1['violation_year'].astype(str) + '-' + df1['violation_month'].astype(str) + '-01')
    df1 = df1.sort_values(by=['license_id', 'datetime']).reset_index(drop=True)
    print(df1.head(10))