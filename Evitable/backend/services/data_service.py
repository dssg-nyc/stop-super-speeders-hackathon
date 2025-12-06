from backend.core.database import get_db, DATA_DIR
import duckdb



def register_violation_views(db, violation_sources):
    valid_tables = []
    for table, filename, select_stmt in violation_sources:
        file_path = DATA_DIR / filename
        if file_path.exists():
            loader = (
                "read_parquet"
                if filename.endswith(".parquet")
                else "read_csv_auto" if filename.endswith(".csv") else "read_json_auto"
            )
            try:
                # Register raw view first
                db.con.execute(
                    f"CREATE OR REPLACE VIEW {table}_raw AS SELECT * FROM {loader}('{file_path}');"
                )
                # Create Normalized View
                db.con.execute(
                    f"CREATE OR REPLACE VIEW {table} AS {select_stmt} FROM {table}_raw;"
                )

                valid_tables.append(table)
                print(f"✅ View Registered & Normalized: {table}")
            except Exception as e:
                print(f"❌ Failed to register {table}: {e}")
    return valid_tables


def register_camera_views(db, camera_sources):
    valid_tables = []
    for table, filename, select_stmt in camera_sources:
        file_path = DATA_DIR / filename
        if file_path.exists():
            loader = (
                "read_parquet"
                if filename.endswith(".parquet")
                else "read_csv_auto" if filename.endswith(".csv") else "read_json_auto"
            )
            try:
                db.con.execute(
                    f"CREATE OR REPLACE VIEW {table}_raw AS SELECT * FROM {loader}('{file_path}');"
                )
                db.con.execute(
                    f"CREATE OR REPLACE VIEW {table} AS {select_stmt} FROM {table}_raw;"
                )
                valid_tables.append(table)
                print(f"✅ View Registered & Normalized: {table}")
            except Exception as e:
                print(f"❌ Failed to register {table}: {e}")
    return valid_tables


def create_master_view(db, view_name, source_tables):
    if source_tables:
        # Use UNION instead of UNION ALL to deduplicate data
        union_query = " UNION ".join(
            [f"SELECT * FROM {t}" for t in source_tables]
        )
        db.con.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS {union_query};"
        )
        print(
            f"🔗 Created Master View: {view_name} (Sources: {source_tables})"
        )


def initialize_views():
    db = get_db()
    print("🔄 Initializing Data Views...")
    
    # Define generic selectors
    # We assume schema consistency for files matching the pattern.
    violation_select = (
        "SELECT license_id, "
        "TRY_CAST(violation_year AS INT) AS violation_year, "
        "TRY_CAST(violation_month AS INT) AS violation_month, "
        "points, "
        "county"
    )
    
    camera_select = "SELECT plate, state, try_cast(issue_date as DATE) as issue_date"

    # 1. Register Traffic Violations
    # Find all matching files
    violation_files = sorted(list(DATA_DIR.glob("nyc_traffic_violations_*")))
    violation_sources = []
    
    for i, file_path in enumerate(violation_files):
        # Generate a safe view name, e.g., v_0, v_1 or based on filename stem
        # Sanitizing stem to be valid sql identifier
        safe_stem = file_path.stem.replace(".", "_").replace("-", "_")
        table_name = f"v_{safe_stem}"
        violation_sources.append((table_name, file_path.name, violation_select))

    valid_violation_tables = register_violation_views(db, violation_sources)
    create_master_view(db, "nyc_traffic_violations_historic", valid_violation_tables)

    # 2. Register Speed Cameras (Plates)
    camera_files = sorted(list(DATA_DIR.glob("nyc_speed_cameras_*")))
    camera_sources = []
    
    for i, file_path in enumerate(camera_files):
        safe_stem = file_path.stem.replace(".", "_").replace("-", "_")
        table_name = f"c_{safe_stem}"
        camera_sources.append((table_name, file_path.name, camera_select))

    valid_camera_tables = register_camera_views(db, camera_sources)
    create_master_view(db, "nyc_speed_cameras_historic", valid_camera_tables)


def get_super_speeder_drivers():
    db = get_db()
    # Logic: 11+ points in last 24 months (2024-2025)
    query = """
        SELECT 
            license_id,
            SUM(points) as total_points,
            COUNT(*) as violation_count,
            MAX(make_date(violation_year, violation_month, 1)) as last_violation
        FROM nyc_traffic_violations_historic
        WHERE violation_year >= 2024
        GROUP BY license_id
        HAVING SUM(points) >= 11
        ORDER BY total_points DESC
    """
    try:
        return db.con.execute(query).df().to_dict(orient="records")
    except Exception as e:
        print(f"Error querying drivers: {e}")
        return []

def get_super_speeder_plates():
    db = get_db()
    # Logic: 16+ tickets in last 12 months (since Nov 2024 approx)
    query = """
        SELECT 
            plate,
            state,
            COUNT(*) as ticket_count,
            MAX(issue_date) as last_ticket
        FROM nyc_speed_cameras_historic
        WHERE issue_date >= '2024-11-01'
        GROUP BY plate, state
        HAVING COUNT(*) >= 16
        ORDER BY ticket_count DESC
    """
    try:
        return db.con.execute(query).df().fillna("").to_dict(orient="records")
    except Exception as e:
        print(f"Error querying plates: {e}")
        return []

def get_monthly_violation_drivers(year=2025, month=10):
    db = get_db()
    # Logic: Drivers who accumulated 11+ points in a SINGLE month
    query = f"""
        SELECT 
            license_id,
            SUM(points) as total_points,
            COUNT(*) as violation_count,
            MAX(make_date(violation_year, violation_month, 1)) as last_violation
        FROM nyc_traffic_violations_historic
        WHERE violation_year = {year} AND violation_month = {month}
        GROUP BY license_id
        HAVING SUM(points) >= 11
        ORDER BY total_points DESC
    """
    try:
        return db.con.execute(query).df().to_dict(orient="records")
    except Exception as e:
        print(f"Error querying monthly drivers: {e}")
        return []





