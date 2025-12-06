from backend.core.database import get_db
from backend.services.data_service import initialize_views

def debug_harmonization():
    db = get_db()
    initialize_views()
    
    print("\n----- Master View Diagnostics -----")
    
    # 1. Total Count
    try:
        count = db.con.execute("SELECT count(*) FROM nyc_traffic_violations_historic").fetchone()[0]
        print(f"Total Rows in Master View: {count}")
    except Exception as e:
        print(f"Error querying master view: {e}")

    # 2. Check for NULL years (Casting issues)
    try:
        null_years = db.con.execute("SELECT count(*) FROM nyc_traffic_violations_historic WHERE violation_year IS NULL").fetchone()[0]
        print(f"Rows with NULL violation_year: {null_years}")
    except: pass

    # 3. Sample Data from each source
    # We can't easily distinguish source unless we added a column, but we can check the sub-views
    sub_views = ["v_hist", "v_t1", "v_t2", "v_t3"]
    for v in sub_views:
         try:
            c = db.con.execute(f"SELECT count(*) FROM {v}").fetchone()[0]
            print(f"Rows in {v}: {c}")
            
            # Check schema of subview
            # print(db.con.execute(f"DESCRIBE {v}").df())
         except Exception as e:
            print(f"Error checking {v}: {e}")

    # 4. Check Date Range
    print("\n----- Date Range Check -----")
    try:
        # Check raw year values distribution
        print("Year Distribution (Top 10):")
        print(db.con.execute("SELECT violation_year, count(*) FROM nyc_traffic_violations_historic GROUP BY 1 ORDER BY 2 DESC LIMIT 10").df())

        # We need to construct date exactly as the service does
        # make_date(violation_year, violation_month, 1)
        q = """
        SELECT 
            min(make_date(violation_year, violation_month, 1)) as min_date,
            max(make_date(violation_year, violation_month, 1)) as max_date,
            count(*) as valid_dates
        FROM nyc_traffic_violations_historic
        WHERE violation_year IS NOT NULL AND violation_month IS NOT NULL
        """
        print(db.con.execute(q).df())
    except Exception as e:
        print(f"Date check error: {e}")

if __name__ == "__main__":
    debug_harmonization()
