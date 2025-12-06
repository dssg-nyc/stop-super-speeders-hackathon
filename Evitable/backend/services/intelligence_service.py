from backend.core.database import get_db
import duckdb

def get_at_risk_drivers():
    """Drivers with 9 or 10 points (Warning Zone)."""
    db = get_db()
    query = """
    SELECT 
        license_id,
        SUM(points) as total_points,
        COUNT(*) as violation_count,
        MAX(make_date(violation_year, violation_month, 1)) as last_violation
    FROM nyc_traffic_violations_historic
    WHERE make_date(violation_year, violation_month, 1) >= (CURRENT_DATE - INTERVAL 24 MONTH)
    GROUP BY license_id
    HAVING SUM(points) BETWEEN 9 AND 10
    ORDER BY total_points DESC
    LIMIT 50;
    """
    return db.con.execute(query).df().to_dict(orient="records")

def get_geo_stats():
    """Violations by County."""
    db = get_db()
    # Driver violations by county
    query = """
    SELECT 
        county,
        COUNT(*) as violation_count,
        SUM(points) as total_points
    FROM nyc_traffic_violations_historic
    GROUP BY county
    ORDER BY violation_count DESC;
    """
    return db.con.execute(query).df().to_dict(orient="records")


def get_super_speeder_drivers():
    """
    Drivers with 11+ points in a 24-month trailing window.
    """
    db = get_db()
    # Note: Using judgment_entry_date as the violation date proxy for now.
    # Adjust logic if violation_date is available or different.
    query = """
    SELECT 
        license_id,
        SUM(points) as total_points,
        COUNT(*) as violation_count,
        MAX(make_date(violation_year, violation_month, 1)) as last_violation
    FROM nyc_traffic_violations_historic
    WHERE make_date(violation_year, violation_month, 1) >= (CURRENT_DATE - INTERVAL 24 MONTH)
    GROUP BY license_id
    HAVING SUM(points) >= 11
    ORDER BY total_points DESC
    LIMIT 100;
    """
    try:
        return db.con.execute(query).df().to_dict(orient="records")
    except Exception as e:
        print(f"Query Error: {e}")
        return []


def get_super_speeder_plates():
    """
    Plates with 16+ tickets in a 12-month trailing window.
    """
    db = get_db()
    query = """
    SELECT 
        plate,
        state,
        COUNT(*) as ticket_count,
        MAX(issue_date) as last_ticket
    FROM nyc_speed_cameras_historic
    WHERE issue_date >= (CURRENT_DATE - INTERVAL 12 MONTH)
    GROUP BY plate, state
    HAVING COUNT(*) >= 16
    ORDER BY ticket_count DESC
    LIMIT 100;
    """
    try:
        return db.con.execute(query).df().to_dict(orient="records")
    except Exception as e:
        print(f"Query Error: {e}")
        return []
