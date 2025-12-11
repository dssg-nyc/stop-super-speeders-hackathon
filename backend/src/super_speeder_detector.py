"""
Super Speeder Detection Module

Identifies drivers who meet the thresholds defined in the legislation:
1. At least 16 speed camera tickets within 12 months, OR
2. At least 11 speed-related license points within 18 months

Also identifies drivers in "warning bands" just below these thresholds.
"""

import duckdb
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from pathlib import Path


# Threshold constants based on the bill
CAMERA_TICKET_THRESHOLD = 16
CAMERA_TICKET_WINDOW_MONTHS = 12
POINTS_THRESHOLD = 11
POINTS_WINDOW_MONTHS = 18

# Warning band: drivers within this distance from threshold
WARNING_BAND_TICKETS = 2
WARNING_BAND_POINTS = 2


class SuperSpeederDetector:
    """Detects super speeders and at-risk drivers from DuckDB warehouse."""
    
    def __init__(self, duckdb_path: str):
        """Initialize detector with path to DuckDB file."""
        self.duckdb_path = duckdb_path
        self.conn = None
    
    def connect(self):
        """Connect to DuckDB."""
        self.conn = duckdb.connect(self.duckdb_path)
        return self
    
    def close(self):
        """Close DuckDB connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def detect_super_speeders(self) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Detect super speeders and warning-band drivers.
        
        Returns:
            Tuple of (super_speeders, warning_drivers, summary_stats)
        """
        if not self.conn:
            raise RuntimeError("Not connected to DuckDB. Call connect() first.")
        
        # Get current date for window calculations
        today = datetime.now().date()
        camera_cutoff = today - timedelta(days=CAMERA_TICKET_WINDOW_MONTHS * 30)
        points_cutoff = today - timedelta(days=POINTS_WINDOW_MONTHS * 30)
        
        # Query for super speeders (meet threshold)
        super_speeders_query = f"""
        WITH driver_stats AS (
            SELECT 
                driver_id,
                driver_id as license_plate,
                COUNT(CASE 
                    WHEN data_source = 'SPEED_CAMERA' 
                    AND violation_date >= DATE '{camera_cutoff}'
                    THEN 1 
                END) as camera_tickets_12mo,
                SUM(CASE 
                    WHEN violation_date >= DATE '{points_cutoff}'
                    AND points_assessed IS NOT NULL
                    THEN points_assessed 
                    ELSE 0 
                END) as speed_points_18mo,
                MAX(violation_date) as last_violation_date,
                COUNT(*) as total_violations
            FROM fct_violations
            WHERE driver_id IS NOT NULL
                GROUP BY driver_id
        )
        SELECT 
            driver_id,
            license_plate,
            camera_tickets_12mo,
            speed_points_18mo,
            last_violation_date,
            total_violations,
            CASE 
                WHEN camera_tickets_12mo >= {CAMERA_TICKET_THRESHOLD} THEN 'CAMERA_THRESHOLD'
                WHEN speed_points_18mo >= {POINTS_THRESHOLD} THEN 'POINTS_THRESHOLD'
                ELSE 'BOTH'
            END as threshold_met
        FROM driver_stats
        WHERE camera_tickets_12mo >= {CAMERA_TICKET_THRESHOLD}
           OR speed_points_18mo >= {POINTS_THRESHOLD}
        ORDER BY camera_tickets_12mo DESC, speed_points_18mo DESC
        """
        
        # Query for warning band drivers (close to threshold)
        warning_query = f"""
        WITH driver_stats AS (
            SELECT 
                driver_id,
                driver_id as license_plate,
                COUNT(CASE 
                    WHEN data_source = 'SPEED_CAMERA' 
                    AND violation_date >= DATE '{camera_cutoff}'
                    THEN 1 
                END) as camera_tickets_12mo,
                SUM(CASE 
                    WHEN violation_date >= DATE '{points_cutoff}'
                    AND points_assessed IS NOT NULL
                    THEN points_assessed 
                    ELSE 0 
                END) as speed_points_18mo,
                MAX(violation_date) as last_violation_date,
                COUNT(*) as total_violations
            FROM fct_violations
            WHERE driver_id IS NOT NULL
                GROUP BY driver_id
        )
        SELECT 
            driver_id,
            license_plate,
            camera_tickets_12mo,
            speed_points_18mo,
            last_violation_date,
            total_violations,
            CASE 
                WHEN camera_tickets_12mo >= ({CAMERA_TICKET_THRESHOLD} - {WARNING_BAND_TICKETS}) 
                THEN {CAMERA_TICKET_THRESHOLD} - camera_tickets_12mo
                ELSE 999
            END as tickets_to_threshold,
            CASE 
                WHEN speed_points_18mo >= ({POINTS_THRESHOLD} - {WARNING_BAND_POINTS})
                THEN {POINTS_THRESHOLD} - speed_points_18mo
                ELSE 999
            END as points_to_threshold
        FROM driver_stats
        WHERE (
            camera_tickets_12mo >= ({CAMERA_TICKET_THRESHOLD} - {WARNING_BAND_TICKETS})
            OR speed_points_18mo >= ({POINTS_THRESHOLD} - {WARNING_BAND_POINTS})
        )
        AND camera_tickets_12mo < {CAMERA_TICKET_THRESHOLD}
        AND speed_points_18mo < {POINTS_THRESHOLD}
        ORDER BY tickets_to_threshold ASC, points_to_threshold ASC
        """
        
        # Execute queries
        super_speeders = self.conn.execute(super_speeders_query).fetchdf().to_dict('records')
        warning_drivers = self.conn.execute(warning_query).fetchdf().to_dict('records')
        
        # Get summary stats
        total_records_query = "SELECT COUNT(*) as total FROM fct_violations"
        total_drivers_query = "SELECT COUNT(DISTINCT driver_id) as total FROM fct_violations WHERE driver_id IS NOT NULL"
        
        total_records = self.conn.execute(total_records_query).fetchone()[0]
        total_drivers = self.conn.execute(total_drivers_query).fetchone()[0]
        
        summary = {
            'total_records': total_records,
            'total_drivers': total_drivers,
            'super_speeders_count': len(super_speeders),
            'warning_drivers_count': len(warning_drivers),
            'camera_threshold': CAMERA_TICKET_THRESHOLD,
            'camera_window_months': CAMERA_TICKET_WINDOW_MONTHS,
            'points_threshold': POINTS_THRESHOLD,
            'points_window_months': POINTS_WINDOW_MONTHS
        }
        
        return super_speeders, warning_drivers, summary
    
    def get_driver_details(self, driver_id: str) -> Dict:
        """
        Get detailed violation history for a specific driver.
        
        Args:
            driver_id: Driver license ID
            
        Returns:
            Dictionary with driver details and violation history
        """
        if not self.conn:
            raise RuntimeError("Not connected to DuckDB. Call connect() first.")
        
        # Get driver violations
        violations_query = f"""
        SELECT 
            violation_date,
            violation_hour,
            violation_code,
            violation_description,
            data_source,
            street_name as location,
            county,
            precinct,
            points_assessed,
            fine_amount,
                driver_age,
                driver_id as license_plate
        FROM fct_violations
        WHERE driver_id = '{driver_id}'
        ORDER BY violation_date DESC
        LIMIT 50
        """
        
        violations = self.conn.execute(violations_query).fetchdf().to_dict('records')
        
        # Get aggregate stats for this driver
        stats_query = f"""
        SELECT 
            COUNT(*) as total_violations,
            SUM(points_assessed) as total_points,
            SUM(fine_amount) as total_fines,
            MIN(violation_date) as first_violation,
            MAX(violation_date) as last_violation,
                AVG(driver_age) as avg_age,
                0 as unique_plates
        FROM fct_violations
        WHERE driver_id = '{driver_id}'
        """
        
        stats = self.conn.execute(stats_query).fetchone()
        
        return {
            'driver_id': driver_id,
            'total_violations': stats[0],
            'total_points': stats[1] or 0,
            'total_fines': stats[2] or 0,
            'first_violation': stats[3],
            'last_violation': stats[4],
                'average_age': stats[5] if stats[5] is not None else None,
                'unique_plates': 0,
            'recent_violations': violations
        }
    
    def get_ingestion_stats(self) -> Dict:
        """Get statistics about the current data in the warehouse."""
        if not self.conn:
            raise RuntimeError("Not connected to DuckDB. Call connect() first.")
        
        stats_query = """
        SELECT 
            COUNT(*) as total_violations,
            COUNT(DISTINCT driver_id) as unique_drivers,
            COUNT(DISTINCT CASE WHEN data_source = 'SPEED_CAMERA' THEN driver_id END) as unique_plates,
            MIN(violation_date) as earliest_violation,
            MAX(violation_date) as latest_violation,
            COUNT(CASE WHEN data_source = 'SPEED_CAMERA' THEN 1 END) as camera_violations,
            COUNT(CASE WHEN data_source = 'TRAFFIC_VIOLATIONS' THEN 1 END) as officer_violations
        FROM fct_violations
        """
        
        result = self.conn.execute(stats_query).fetchone()
        
        return {
            'total_violations': result[0],
            'unique_drivers': result[1],
            'unique_plates': result[2],
            'earliest_violation': result[3],
            'latest_violation': result[4],
            'camera_violations': result[5],
            'officer_violations': result[6]
        }


def format_driver_export(driver_details: Dict) -> str:
    """
    Format driver details as plain text for export/clipboard.
    
    Args:
        driver_details: Dictionary with driver info
        
    Returns:
        Formatted text block
    """
    lines = []
    lines.append("=" * 60)
    lines.append(f"DRIVER LICENSE ID: {driver_details['driver_id']}")
    lines.append("=" * 60)
    lines.append(f"Total Violations: {driver_details['total_violations']}")
    lines.append(f"Total Points: {driver_details['total_points']}")
    lines.append(f"Total Fines: ${driver_details['total_fines']:,.2f}")
    lines.append(f"First Violation: {driver_details['first_violation']}")
    lines.append(f"Last Violation: {driver_details['last_violation']}")
    lines.append(f"Unique Plates: {driver_details['unique_plates']}")
    lines.append("")
    lines.append("RECENT VIOLATIONS:")
    lines.append("-" * 60)
    
    for v in driver_details['recent_violations'][:10]:
        lines.append(f"{v['violation_date']} | {v['data_source']} | {v['violation_code']}")
        lines.append(f"  Location: {v.get('location', 'N/A')} ({v.get('county', 'N/A')})")
        lines.append(f"  Points: {v.get('points_assessed', 0)} | Fine: ${v.get('fine_amount', 0):,.2f}")
        lines.append("")
    
    return "\n".join(lines)
