"""
Unit tests for Super Speeder Detector

Tests the core detection logic and ensures license plate values
are properly returned from the database.
"""

import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.super_speeder_detector import SuperSpeederDetector


class TestSuperSpeederDetector(unittest.TestCase):
    """Test cases for SuperSpeederDetector class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are shared across all tests."""
        cls.duckdb_path = "data/duckdb/test.duckdb"
    
    def test_database_connection(self):
        """Test that we can connect to the DuckDB database."""
        with SuperSpeederDetector(self.duckdb_path) as detector:
            self.assertIsNotNone(detector.conn)
    
    def test_detect_super_speeders_returns_data(self):
        """Test that detect_super_speeders returns data structures."""
        with SuperSpeederDetector(self.duckdb_path) as detector:
            super_speeders, warning_drivers, summary = detector.detect_super_speeders()
            
            # Check return types
            self.assertIsInstance(super_speeders, list)
            self.assertIsInstance(warning_drivers, list)
            self.assertIsInstance(summary, dict)
            
            # Check summary has expected keys
            self.assertIn('total_records', summary)
            self.assertIn('total_drivers', summary)
            self.assertIn('super_speeders_count', summary)
            self.assertIn('warning_drivers_count', summary)
    
    def test_license_plate_not_null_super_speeders(self):
        """
        REGRESSION TEST for license plate bug fix.
        
        Ensures that super speeders have non-null license_plate values.
        This was the primary bug - license_plate was being set to NULL
        in the SQL query instead of using the driver_id value.
        """
        with SuperSpeederDetector(self.duckdb_path) as detector:
            super_speeders, _, _ = detector.detect_super_speeders()
            
            if len(super_speeders) > 0:
                for driver in super_speeders:
                    # Check that license_plate key exists
                    self.assertIn('license_plate', driver,
                                  f"Driver {driver.get('driver_id')} missing license_plate field")
                    
                    # Check that license_plate has a value
                    plate = driver.get('license_plate')
                    self.assertIsNotNone(plate,
                                         f"Driver {driver.get('driver_id')} has NULL license_plate")
                    
                    # Check that it's not empty or 'nan'
                    plate_str = str(plate).strip().lower()
                    self.assertNotIn(plate_str, ['', 'none', 'nan', 'null'],
                                     f"Driver {driver.get('driver_id')} has invalid license_plate: {plate}")
    
    def test_license_plate_not_null_warning_drivers(self):
        """
        REGRESSION TEST for license plate bug fix (warning drivers).
        
        Ensures that warning drivers also have non-null license_plate values.
        """
        with SuperSpeederDetector(self.duckdb_path) as detector:
            _, warning_drivers, _ = detector.detect_super_speeders()
            
            if len(warning_drivers) > 0:
                for driver in warning_drivers:
                    # Check that license_plate key exists
                    self.assertIn('license_plate', driver,
                                  f"Warning driver {driver.get('driver_id')} missing license_plate field")
                    
                    # Check that license_plate has a value
                    plate = driver.get('license_plate')
                    self.assertIsNotNone(plate,
                                         f"Warning driver {driver.get('driver_id')} has NULL license_plate")
                    
                    # Check that it's not empty or 'nan'
                    plate_str = str(plate).strip().lower()
                    self.assertNotIn(plate_str, ['', 'none', 'nan', 'null'],
                                     f"Warning driver {driver.get('driver_id')} has invalid license_plate: {plate}")
    
    def test_license_plate_matches_driver_id(self):
        """
        Test that license_plate field contains the same value as driver_id.
        
        In the current data model:
        - For speed camera violations: driver_id = license plate
        - For traffic violations: driver_id = driver license ID
        
        So license_plate should equal driver_id for all records.
        """
        with SuperSpeederDetector(self.duckdb_path) as detector:
            super_speeders, warning_drivers, _ = detector.detect_super_speeders()
            
            all_drivers = super_speeders + warning_drivers
            
            for driver in all_drivers:
                driver_id = driver.get('driver_id')
                license_plate = driver.get('license_plate')
                
                self.assertEqual(driver_id, license_plate,
                                 f"license_plate ({license_plate}) should match driver_id ({driver_id})")
    
    def test_driver_details_has_license_plate(self):
        """Test that get_driver_details includes license_plate in violation records."""
        with SuperSpeederDetector(self.duckdb_path) as detector:
            # Get a super speeder to test with
            super_speeders, _, _ = detector.detect_super_speeders()
            
            if len(super_speeders) > 0:
                test_driver_id = super_speeders[0]['driver_id']
                
                # Get details for this driver
                driver_info = detector.get_driver_details(test_driver_id)
                
                # Check that recent_violations have license_plate field
                self.assertIn('recent_violations', driver_info)
                
                if len(driver_info['recent_violations']) > 0:
                    for violation in driver_info['recent_violations']:
                        self.assertIn('license_plate', violation,
                                      "Violation record missing license_plate field")
    
    def test_ingestion_stats(self):
        """Test that get_ingestion_stats returns expected data."""
        with SuperSpeederDetector(self.duckdb_path) as detector:
            stats = detector.get_ingestion_stats()
            
            # Check expected keys
            expected_keys = [
                'total_violations',
                'unique_drivers',
                'unique_plates',
                'earliest_violation',
                'latest_violation',
                'camera_violations',
                'officer_violations'
            ]
            
            for key in expected_keys:
                self.assertIn(key, stats, f"Missing key '{key}' in ingestion stats")
            
            # Check that we have some data
            self.assertGreater(stats['total_violations'], 0,
                               "Database should have some violations")


if __name__ == '__main__':
    unittest.main(verbosity=2)
