
from backend.services.data_service import initialize_views
from backend.core.database import get_db

def analyze_data():
    initialize_views()
    db = get_db()
    
    print("\n🔎 Traffic Violations Date Analysis...")
    q_v = "SELECT MIN(violation_year), MAX(violation_year), MAX(violation_month) FROM nyc_traffic_violations_historic"
    try:
        print(db.con.execute(q_v).df())
    except Exception as e:
        print(e)

    print("\n🔎 Speed Cameras Date Analysis...")
    q_c = "SELECT MIN(issue_date), MAX(issue_date) FROM nyc_speed_cameras_historic"
    try:
        print(db.con.execute(q_c).df())
    except Exception as e:
        print(e)

if __name__ == "__main__":
    analyze_data()
