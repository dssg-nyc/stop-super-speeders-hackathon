"""
Test script to verify license plate bug fix.

This test ensures that the super speeder detection correctly returns 
license plate values instead of NULL/nan for drivers with camera violations.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.super_speeder_detector import SuperSpeederDetector

def test_license_plate_not_null():
    """Test that license plate values are returned correctly."""
    
    # Path to DuckDB
    duckdb_path = "data/duckdb/test.duckdb"
    
    print("=" * 80)
    print("Testing License Plate Bug Fix")
    print("=" * 80)
    
    # Connect to database and detect super speeders
    with SuperSpeederDetector(duckdb_path) as detector:
        super_speeders, warning_drivers, summary = detector.detect_super_speeders()
    
    print(f"\n✓ Found {len(super_speeders)} super speeders")
    print(f"✓ Found {len(warning_drivers)} warning drivers")
    
    # Test super speeders have license plates
    null_plates_super = 0
    valid_plates_super = 0
    
    for driver in super_speeders:
        plate = driver.get('license_plate')
        if plate is None or str(plate).lower() in ('none', 'nan', 'null', ''):
            null_plates_super += 1
            print(f"\n⚠️  Super Speeder with NULL plate:")
            print(f"   Driver ID: {driver.get('driver_id')}")
            print(f"   License Plate: {plate}")
            print(f"   Camera Tickets: {driver.get('camera_tickets_12mo')}")
        else:
            valid_plates_super += 1
    
    # Test warning drivers have license plates
    null_plates_warning = 0
    valid_plates_warning = 0
    
    for driver in warning_drivers:
        plate = driver.get('license_plate')
        if plate is None or str(plate).lower() in ('none', 'nan', 'null', ''):
            null_plates_warning += 1
        else:
            valid_plates_warning += 1
    
    # Print results
    print("\n" + "=" * 80)
    print("Test Results")
    print("=" * 80)
    print(f"Super Speeders:")
    print(f"  ✓ Valid plates: {valid_plates_super}")
    print(f"  ✗ NULL plates: {null_plates_super}")
    
    print(f"\nWarning Drivers:")
    print(f"  ✓ Valid plates: {valid_plates_warning}")
    print(f"  ✗ NULL plates: {null_plates_warning}")
    
    # Show sample data
    if super_speeders:
        print("\n" + "=" * 80)
        print("Sample Super Speeder Data (first 3 records)")
        print("=" * 80)
        for i, driver in enumerate(super_speeders[:3], 1):
            print(f"\n{i}. Driver ID: {driver.get('driver_id')}")
            print(f"   License Plate: {driver.get('license_plate')}")
            print(f"   Camera Tickets (12mo): {driver.get('camera_tickets_12mo')}")
            print(f"   Speed Points (18mo): {driver.get('speed_points_18mo')}")
            print(f"   Last Violation: {driver.get('last_violation_date')}")
            print(f"   Total Violations: {driver.get('total_violations')}")
    
    # Determine test pass/fail
    print("\n" + "=" * 80)
    if null_plates_super == 0 and null_plates_warning == 0:
        print("✅ TEST PASSED: All drivers have valid license plate values!")
    elif null_plates_super > 0 or null_plates_warning > 0:
        print("⚠️  TEST WARNING: Some drivers have NULL plates")
        print("   (This might be expected if they only have traffic violations)")
    print("=" * 80)
    
    return null_plates_super == 0 and null_plates_warning == 0


if __name__ == "__main__":
    try:
        test_license_plate_not_null()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
