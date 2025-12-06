import duckdb
from pathlib import Path

DATA_DIR = Path("../data/opendata")

def inspect_test_files():
    files = [
        "test1_nyc_traffic_violations.json",
        "test2_nyc_traffic_violations.csv",
        "test3_nyc_traffic_violations.csv",
        "test1_nyc_speed_cameras.json",
        "test2_nyc_speed_cameras.csv",
        "test3_nyc_speed_cameras.csv"
    ]
    
    con = duckdb.connect()
    
    for filename in files:
        file_path = DATA_DIR / filename
        if not file_path.exists():
            print(f"❌ Missing: {filename}")
            continue
            
        print(f"\n🧐 Inspecting {filename}...")
        try:
            # Determine loader
            loader = "read_json_auto" if filename.endswith(".json") else "read_csv_auto"
            query = f"DESCRIBE SELECT * FROM {loader}('{file_path}')"
            df = con.execute(query).df()
            print(f"✅ {filename}: {df['column_name'].tolist()}")
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")

if __name__ == "__main__":
    inspect_test_files()
