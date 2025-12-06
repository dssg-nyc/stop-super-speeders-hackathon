
from backend.services.data_service import initialize_views
from backend.core.database import get_db

def analyze_2025():
    initialize_views()
    db = get_db()
    
    print("🔎 Analyzing 2025 Distribution...")
    query = """
    SELECT 
        violation_month,
        COUNT(*) as total_v
    FROM nyc_traffic_violations_historic
    WHERE violation_year = 2025
    GROUP BY violation_month
    ORDER BY violation_month
    """
    try:
        print(db.con.execute(query).df())
    except Exception as e:
        print(e)

if __name__ == "__main__":
    analyze_2025()
