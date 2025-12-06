
import requests
import csv
import io

BASE_URL = "http://localhost:8000/api"

def verify_phase2():
    print("🚀 Verifying Phase 2 Enhancements...")
    
    # 1. High Risk Drivers (24 Month Window)
    try:
        r = requests.get(f"{BASE_URL}/violators/drivers")
        data = r.json()
        count = data['count']
        print(f"\n📊 High Risk Drivers (24mo): {count}")
        if count > 50000:
             print("   ⚠️ WARNING: Count still high. Logic fix might not be applied.")
        else:
             print("   ✅ Count in practical range (~44k).")

        # Check for last_violation field
        if count > 0 and 'last_violation' in data['violators'][0]:
             print("   ✅ 'last_violation' field present.")
        else:
             print("   ❌ 'last_violation' field MISSING.")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 2. Dangerous Vehicles (12 Month Window)
    try:
        r = requests.get(f"{BASE_URL}/violators/plates")
        data = r.json()
        count = data['count']
        print(f"\n🚙 Dangerous Vehicles (12mo): {count}")
        if count > 500:
             print("   ⚠️ WARNING: Count still high. Logic fix might not be applied.")
        else:
             print("   ✅ Count in practical range (~60).")

        # Check for last_ticket field
        if count > 0 and 'last_ticket' in data['violators'][0]:
             print("   ✅ 'last_ticket' field present.")
        else:
             print("   ❌ 'last_ticket' field MISSING.")
    except Exception as e:
         print(f"   ❌ Error: {e}")

    # 3. Recent High Risk (Oct 2025)
    try:
        r = requests.get(f"{BASE_URL}/violators/drivers/recent")
        data = r.json()
        count = data['count']
        print(f"\n📅 Recent High Risk (Oct 2025): {count}")
        
        if count > 0:
             print("   ✅ Recent data found.")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 4. CSV Download Check
    try:
        print("\n📥 Testing CSV Export...")
        r = requests.get(f"{BASE_URL}/violators/drivers/download")
        if r.status_code == 200:
             print("   ✅ Drivers CSV: OK")
        else:
             print(f"   ❌ Drivers CSV: Failed {r.status_code}")
             
        r = requests.get(f"{BASE_URL}/violators/drivers/recent/download")
        if r.status_code == 200:
             print("   ✅ Recent Drivers CSV: OK")
        else:
             print(f"   ❌ Recent Drivers CSV: Failed {r.status_code}")

    except Exception as e:
         print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    verify_phase2()
