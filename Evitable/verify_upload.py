
import requests
import pandas as pd
import io
import time

# Create a dummy CSV for drivers
csv_content = """license_id,violation_year,violation_month,points,county
TEST_LICENSE_001,2024,1,12,NY
TEST_LICENSE_002,2024,1,5,NY
"""

# Create a dummy CSV for plates
plate_csv_content = """plate,state,issue_date,violation_time,fine_amount
TEST_PLATE_001,NY,2024-01-01,12:00,50
TEST_PLATE_001,NY,2024-01-02,12:00,50
TEST_PLATE_001,NY,2024-01-03,12:00,50
TEST_PLATE_001,NY,2024-01-04,12:00,50
TEST_PLATE_001,NY,2024-01-05,12:00,50
TEST_PLATE_001,NY,2024-01-06,12:00,50
TEST_PLATE_001,NY,2024-01-07,12:00,50
TEST_PLATE_001,NY,2024-01-08,12:00,50
TEST_PLATE_001,NY,2024-01-09,12:00,50
TEST_PLATE_001,NY,2024-01-10,12:00,50
TEST_PLATE_001,NY,2024-01-11,12:00,50
TEST_PLATE_001,NY,2024-01-12,12:00,50
TEST_PLATE_001,NY,2024-01-13,12:00,50
TEST_PLATE_001,NY,2024-01-14,12:00,50
TEST_PLATE_001,NY,2024-01-15,12:00,50
TEST_PLATE_001,NY,2024-01-16,12:00,50
"""

def test_upload_drivers():
    print("🚀 Uploading Drivers CSV...")
    files = {'file': ('test_drivers.csv', csv_content, 'text/csv')}
    try:
        response = requests.post('http://localhost:8000/api/upload/analyze', files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ Upload Driver Success")
        else:
            print("❌ Upload Driver Failed")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_upload_plates():
    print("\n🚀 Uploading Plates CSV...")
    files = {'file': ('test_plates.csv', plate_csv_content, 'text/csv')}
    try:
        response = requests.post('http://localhost:8000/api/upload/analyze', files=files)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ Upload Plate Success")
        else:
            print("❌ Upload Plate Failed")
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    # Wait for server to be potentially ready if we were running it, but we assume it's running or we will start it.
    test_upload_drivers()
    test_upload_plates()
