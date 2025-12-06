import duckdb
from pathlib import Path

DATA_DIR = Path("../data/opendata")
FILE_PATH = DATA_DIR / "nyc_traffic_violations_historic.parquet"

def inspect_schema():
    if not FILE_PATH.exists():
        print(f"❌ File not found: {FILE_PATH}")
        return

    print(f"🧐 Inspecting {FILE_PATH}...")
    try:
        con = duckdb.connect()
        # Describe the parquet file directly
        df = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{FILE_PATH}')").df()
        print(df)
        
        # Also print first row to see date formats
        print("\n----- Sample Data (First Row) -----")
        print(con.execute(f"SELECT * FROM read_parquet('{FILE_PATH}') LIMIT 1").df())
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_schema()
