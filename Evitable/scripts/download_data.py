import duckdb
import requests
import os
import time
from pathlib import Path

# Config
DATA_DIR = Path("../data/opendata")
BASE_URL = "https://fastopendata.org/dssg-safestreets"
TARGET_FILES = [
    "nyc_speed_cameras_historic.parquet",
    "test1_nyc_speed_cameras.json",
    "test2_nyc_speed_cameras.csv",
    "test3_nyc_speed_cameras.csv",
    "nyc_traffic_violations_historic.parquet",
    "test1_nyc_traffic_violations.json",
    "test2_nyc_traffic_violations.csv",
    "test3_nyc_traffic_violations.csv"
]

def download_and_cache_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 Checking Data Assets in {DATA_DIR}...")
    
    for filename in TARGET_FILES:
        local_path = DATA_DIR / filename
        url = f"{BASE_URL}/{filename}"
        
        if local_path.exists() and local_path.stat().st_size > 0:
            print(f"📂 Cached: '{filename}'")
            continue
            
        print(f"⬇️  Downloading '{filename}'...")
        for attempt in range(1, 4):
            try:
                with requests.get(url, stream=True, headers={'Connection': 'close'}, timeout=(10, 60)) as r:
                    r.raise_for_status()
                    with open(local_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                print(f"✅ Saved to {local_path}")
                time.sleep(1)
                break
            except Exception as e:
                print(f"❌ Failed attempt {attempt} for {filename}: {e}")
                if local_path.exists():
                    local_path.unlink()
                if attempt < 3:
                    time.sleep(2)
                else:
                    print(f"❌ Could not download {filename}")

if __name__ == "__main__":
    download_and_cache_data()
