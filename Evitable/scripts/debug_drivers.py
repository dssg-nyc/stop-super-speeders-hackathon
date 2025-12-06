from backend.core.database import get_db, DATA_DIR
import duckdb

def debug_data():
    db = get_db()
    
    # 1. Register Views (in case)
    files = {
        "nyc_traffic_violations_historic": "nyc_traffic_violations_historic.parquet",
    }
    for table, filename in files.items():
        file_path = DATA_DIR / filename
        db.con.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT * FROM read_parquet('{file_path}');")

    # 2. Check Date Range
    print("----- Traffic Violations Verification -----")
    try:
        query = """
        SELECT 
            MIN(judgment_entry_date) as min_date,
            MAX(judgment_entry_date) as max_date,
            COUNT(*) as total_rows
        FROM nyc_traffic_violations_historic
        """
        print(db.con.execute(query).df())
        
        # 3. Check sample rows to ensure columns exist
        print("\n----- Sample Rows -----")
        print(db.con.execute("SELECT * FROM nyc_traffic_violations_historic LIMIT 5").df())

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_data()
