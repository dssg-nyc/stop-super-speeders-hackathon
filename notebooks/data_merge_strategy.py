import duckdb
import os
import pandas as pd

def main():
    print("🚀 Starting Data Merge & Processing Engine...")

    # 1. Connection Setup
    con = duckdb.connect(":memory:")
    con.execute("INSTALL httpfs; LOAD httpfs;")

    # 2. Register Raw Data Files
    DATA_DIR = "../data/opendata"
    # Ensure relative path works if running from notebooks/ dir
    if not os.path.exists(DATA_DIR):
        # Fallback if running from root
        DATA_DIR = "data/opendata"
        
    files = {
        "speed_historic": "nyc_speed_cameras_historic.parquet",
        "speed_test1": "test1_nyc_speed_cameras.json",
        "speed_test2": "test2_nyc_speed_cameras.csv",
        "speed_test3": "test3_nyc_speed_cameras.csv",
        "traffic_historic": "nyc_traffic_violations_historic.parquet",
        "traffic_test1": "test1_nyc_traffic_violations.json",
        "traffic_test2": "test2_nyc_traffic_violations.csv",
        "traffic_test3": "test3_nyc_traffic_violations.csv"
    }

    print("\n📦 Registering Views...")
    for name, filename in files.items():
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            if ".parquet" in filename: 
                con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet('{path}')")
            elif ".json" in filename: 
                con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_json_auto('{path}')")
            elif ".csv" in filename: 
                con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_csv_auto('{path}', all_varchar=True)")
            print(f"  ✅ Registered: {name}")
        else:
            print(f"  ❌ Missing: {path}")

    # 3. Schema Profiling (Simplified for Script)
    print("\n🔍 Profiling Schemas... (Skipping visual output, use notebook for detailed report)")

    # 4. Normalization Views
    print("\n🛠  Building Normalization Views...")
    
    # --- SPEED CAMERAS ---
    # Test 1: JSON Feed
    sql_speed_1 = """
    SELECT 
        *, 
        try_cast(created_at AS TIMESTAMP WITH TIME ZONE) as created_at_cast,
        try_cast(judgment_entry_date AS TIMESTAMP WITH TIME ZONE) as judgment_entry_date_cast,
        try_cast(issue_date AS TIMESTAMP WITH TIME ZONE) as issue_date_cast
    FROM speed_test1
    """
    con.execute(f"""CREATE OR REPLACE VIEW norm_speed_test1 AS 
    SELECT 
        summons_number,
        plate,
        state,
        license_type,
        issue_date_cast as issue_date,
        violation_time,
        violation,
        judgment_entry_date_cast as judgment_entry_date,
        fine_amount,
        penalty_amount,
        interest_amount,
        reduction_amount,
        payment_amount,
        amount_due,
        precinct,
        county,
        issuing_agency,
        violation_status,
        created_at_cast as created_at
    FROM ({sql_speed_1})
    """)

    # Test 2: CSV Feed (Title Case)
    con.execute("""CREATE OR REPLACE VIEW norm_speed_test2 AS
    SELECT
        "Summons Number" as summons_number,
        "Plate" as plate,
        "State" as state,
        "License Type" as license_type,
        make_timestamp("Issue Year" :: int, "Issue Month" :: int, "Issue Day" :: int, 0, 0, 0) as issue_date, 
        "Violation Time" as violation_time,
        "Violation" as violation,
        try_cast("Judgment Entry Date" AS TIMESTAMP WITH TIME ZONE) as judgment_entry_date,
        "Fine Amount" :: double as fine_amount,
        "Penalty Amount" :: double as penalty_amount,
        "Interest Amount" :: double as interest_amount,
        "Reduction Amount" :: double as reduction_amount,
        "Payment Amount" :: double as payment_amount,
        "Amount Due" :: double as amount_due,
        NULL :: bigint as precinct,
        "County" as county,
        "Issuing Agency" as issuing_agency,
        "Violation Status" as violation_status,
        try_cast("Created At" AS TIMESTAMP WITH TIME ZONE) as created_at
    FROM speed_test2
    """)

    # Test 3: CSV Feed (Abbreviated)
    con.execute("""CREATE OR REPLACE VIEW norm_speed_test3 AS
    SELECT
        summons_number,
        plate,
        state,
        license_type,
        try_cast(issued_date AS TIMESTAMP WITH TIME ZONE) as issue_date,
        violation_time,
        violation,
        NULL :: timestamp with time zone as judgment_entry_date,
        fine_amount :: double as fine_amount,
        penalty_amount :: double as penalty_amount,
        interest_amount :: double as interest_amount,
        reduction_amount :: double as reduction_amount,
        payment_amount :: double as payment_amount,
        amount_due :: double as amount_due,
        precinct :: bigint as precinct,
        county,
        issuing_agency,
        violation_status,
        try_cast(created_at AS TIMESTAMP WITH TIME ZONE) as created_at
    FROM speed_test3
    """)
    print("  ✅ Speed Camera Normalization Views Created.")

    # --- TRAFFIC VIOLATIONS ---
    # Test 2
    con.execute("""CREATE OR REPLACE VIEW norm_traffic_test2 AS
    SELECT 
        NULL as license_id,
        make_date("Birth Year" :: int, "Birth Month" :: int, 1) as birth_date,
        "Age" :: bigint as age,
        "Violation Code" as violation_code,
        "Violation Year" :: bigint as violation_year,
        "Violation Month" :: bigint as violation_month,
        "Points" :: bigint as points,
        "County" as county
    FROM traffic_test2
    """)

    # Test 3
    con.execute("""CREATE OR REPLACE VIEW norm_traffic_test3 AS
    SELECT 
        lic_id as license_id,
        try_cast(dob_formatted AS DATE) as birth_date,
        NULL :: bigint as age,
        v_code as violation_code,
        v_year :: bigint as violation_year,
        v_month :: bigint as violation_month,
        points :: bigint as points,
        county
    FROM traffic_test3
    """)
    print("  ✅ Traffic Violation Normalization Views Created.")

    # 5. Controlled Merge
    print("\n🔄 Merging into Final Operational Tables...")
    
    # Speed Cameras Final
    query = """
    CREATE OR REPLACE TABLE speed_cameras_final AS 
    SELECT DISTINCT ON (summons_number) * 
    FROM (
        SELECT * FROM speed_historic                 -- 1. Bases: Historical Ground Truth
        UNION ALL BY NAME
        SELECT * FROM norm_speed_test1               -- 2. Append Normalized Feed 1
        UNION ALL BY NAME
        SELECT * FROM norm_speed_test2               -- 3. Append Normalized Feed 2
        UNION ALL BY NAME
        SELECT * FROM norm_speed_test3               -- 4. Append Normalized Feed 3
    )
    ORDER BY summons_number, created_at DESC;        -- Deduplication Logic
    """
    con.execute(query)
    print("  🎉 Speed Cameras Final Operational Table Created.")

    # Traffic Violations Final
    query_traffic = """
    CREATE OR REPLACE TABLE traffic_violations_final AS 
    SELECT DISTINCT * 
    FROM (
        SELECT * FROM traffic_historic
        UNION ALL BY NAME
        SELECT * FROM traffic_test1
        UNION ALL BY NAME
        SELECT * FROM norm_traffic_test2
        UNION ALL BY NAME
        SELECT * FROM norm_traffic_test3
    )
    """
    con.execute(query_traffic)
    print("  🎉 Traffic Violations Final Operational Table Created.")

    # 6. Speed Camera Engine
    print("\n🚗 Running Speed Camera Engine...")
    
    # 1. Define Window
    res = con.execute("SELECT MAX(issue_date) FROM speed_cameras_final").fetchone()
    if res and res[0]:
        as_of_date = pd.Timestamp(res[0])
    else:
        # Fallback if table is empty
        as_of_date = pd.Timestamp.now()
        
    cutoff_date = as_of_date - pd.DateOffset(months=12)

    print(f"  📅 Engine Run Date: {as_of_date.date()}")
    print(f"  🔙 Analysis Window: {cutoff_date.date()} to {as_of_date.date()}")

    # 2. Run Engine
    engine_sql = f"""
    CREATE OR REPLACE TABLE vehicle_speed_summary AS
    WITH filtered AS (
        SELECT * FROM speed_cameras_final
        WHERE issue_date >= '{cutoff_date}'
    ),
    aggregated AS (
        SELECT
            plate,
            state,
            COUNT(DISTINCT summons_number) as violations_12m,
            MIN(issue_date) as first_violation_12m,
            MAX(issue_date) as last_violation_12m,
            arg_max(county, issue_date) as county_last_seen,
            SUM(fine_amount) as total_fines_12m
        FROM filtered
        GROUP BY plate, state
    )
    SELECT
        row_number() OVER (ORDER BY violations_12m DESC, plate) as vehicle_id,
        plate,
        state,
        county_last_seen,
        violations_12m,
        first_violation_12m,
        last_violation_12m,
        total_fines_12m,
        CASE
            WHEN violations_12m >= 16 THEN 'TRIGGER'
            WHEN violations_12m >= 12 THEN 'WARNING'
            ELSE 'OK'
        END as status,
        16 as trigger_threshold,
        12 as warning_lower_bound,
        CAST('{as_of_date}' AS DATE) as as_of_date
    FROM aggregated
    ORDER BY violations_12m DESC;
    """
    con.execute(engine_sql)
    print("  ✅ Speed Camera Engine Complete.")

    # 3. Export
    EXPORT_DIR = "../data/exports"
    if not os.path.exists("../data") and os.path.exists("data"):
         EXPORT_DIR = "data/exports"

    os.makedirs(EXPORT_DIR, exist_ok=True)
    export_path = os.path.join(EXPORT_DIR, "vehicle_speed_summary.csv")
    
    # Use copy to csv
    con.execute(f"COPY vehicle_speed_summary TO '{export_path}' (HEADER, DELIMITER ',')")
    print(f"\n💾 Results Exported to: {export_path}")

    # Summary Stats
    summary = con.execute("SELECT status, COUNT(*) FROM vehicle_speed_summary GROUP BY status").fetchall()
    print("📊 Engine Results:")
    for s, c in summary: print(f"  {s}: {c}")

    print("\n🚨 TOP RISK VEHICLES (TRIGGER):")
    df_top = con.sql("SELECT * FROM vehicle_speed_summary WHERE status='TRIGGER' LIMIT 5").df()
    print(df_top.to_string(index=False))

    print("\n✅ Script Completed Successfully.")

if __name__ == "__main__":
    main()
