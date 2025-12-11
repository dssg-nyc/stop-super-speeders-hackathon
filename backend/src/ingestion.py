"""
SAFENY DuckDB Ingestion Module
Loads cleaned data into DuckDB warehouse
"""

import duckdb
import pandas as pd
from pathlib import Path
import logging
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DuckDBIngester:
    """Loads cleaned datasets into DuckDB warehouse."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.con = None
    
    def connect(self):
        """Establish DuckDB connection."""
        self.con = duckdb.connect(str(self.db_path))
        self.con.execute("INSTALL httpfs; LOAD httpfs;")
        logger.info(f"✅ Connected to DuckDB: {self.db_path}")
    
    def close(self):
        """Close connection."""
        if self.con:
            self.con.close()
            self.con = None
    
    def initialize_schema(self, schema_file: str):
        """Create all tables from SQL schema file."""
        schema_path = Path(schema_file)
        if not schema_path.exists():
            logger.error(f"❌ Schema file not found: {schema_file}")
            return False
        
        logger.info(f"📋 Initializing schema from {schema_file}...")
        sql = schema_path.read_text()
        
        try:
            # Split by semicolon and execute each statement
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            for stmt in statements:
                self.con.execute(stmt)
            logger.info(f"✅ Schema initialized with {len(statements)} statements")
            return True
        except Exception as e:
            logger.error(f"❌ Schema initialization failed: {e}")
            return False
    
    def load_speed_cameras(self, parquet_file: str) -> int:
        """Load cleaned speed camera data into fct_violations."""
        file_path = Path(parquet_file)
        if not file_path.exists():
            logger.warning(f"⚠️ Speed cameras file not found: {parquet_file}")
            return 0
        
        logger.info(f"📥 Loading speed cameras from {file_path.name}...")
        
        try:
            df = pd.read_parquet(file_path)
            
            # Map columns to fct_violations schema
            df_mapped = pd.DataFrame({
                'summons_number': df['summons_number'],
                'driver_id': df.get('plate', None),
                'driver_age': None,  # Speed cameras don't have driver age
                'violation_code': df['violation'],
                'violation_description': df['violation'],
                'points_assessed': 0,
                'county': df['county'],
                'precinct': df.get('precinct', None),
                'street_name': None,  # Extract from violation if possible
                'latitude': None,
                'longitude': None,
                'violation_date': df['issued_date'],
                'violation_year': df['violation_year'],
                'violation_month': df['violation_month'],
                'violation_day_of_week': df['violation_day_of_week'],
                'violation_hour': df.get('violation_hour', None),
                'fine_amount': df['fine_amount'],
                'penalty_amount': df.get('penalty_amount', 0),
                'payment_amount': df.get('payment_amount', 0),
                'interest_amount': df.get('interest_amount', 0),
                'violation_status': df.get('violation_status', 'UNKNOWN'),
                'judgment_date': df.get('judgment_entry_date', None),
                'data_source': 'SPEED_CAMERA',
                'ingested_at': datetime.now()
            })
            
            # Insert
            self.con.execute(
                """
                INSERT INTO fct_violations (
                    summons_number, driver_id, driver_age,
                    violation_code, violation_description, points_assessed,
                    county, precinct, street_name, latitude, longitude,
                    violation_date, violation_year, violation_month, violation_day_of_week, violation_hour,
                    fine_amount, penalty_amount, payment_amount, interest_amount,
                    violation_status, judgment_date, data_source, ingested_at
                )
                SELECT * FROM df_mapped WHERE summons_number IS NOT NULL
                """
            )
            
            count = len(df_mapped)
            logger.info(f"✅ Loaded {count} speed camera violations")
            return count
            
        except Exception as e:
            logger.error(f"❌ Speed camera loading failed: {e}")
            return 0
    
    def load_traffic_violations(self, parquet_file: str) -> int:
        """Load cleaned traffic violations into fct_violations."""
        file_path = Path(parquet_file)
        if not file_path.exists():
            logger.warning(f"⚠️ Traffic violations file not found: {parquet_file}")
            return 0
        
        logger.info(f"📥 Loading traffic violations from {file_path.name}...")
        
        try:
            df = pd.read_parquet(file_path)
            
            # Map columns to fct_violations schema
            df_mapped = pd.DataFrame({
                'summons_number': None,  # Traffic violations don't have summons_number
                'driver_id': df['lic_id'],
                'driver_age': df['age'],
                'violation_code': df['v_code'],
                'violation_description': df['v_code'],
                'points_assessed': df['points'],
                'county': df['county'],
                'precinct': None,
                'street_name': None,
                'latitude': None,
                'longitude': None,
                'violation_date': df['violation_date'],
                'violation_year': df['violation_year'],
                'violation_month': df['violation_month'],
                'violation_day_of_week': df['violation_day_of_week'],
                'violation_hour': df.get('violation_hour', None),
                'fine_amount': 0,  # Traffic violations don't have fine_amount in this dataset
                'penalty_amount': 0,
                'payment_amount': 0,
                'interest_amount': 0,
                'violation_status': 'UNKNOWN',
                'judgment_date': None,
                'data_source': 'TRAFFIC_VIOLATIONS',
                'ingested_at': datetime.now()
            })
            
            # Insert (allow summons_number to be NULL for traffic violations)
            self.con.execute(
                """
                INSERT INTO fct_violations (
                    summons_number, driver_id, driver_age,
                    violation_code, violation_description, points_assessed,
                    county, precinct, street_name, latitude, longitude,
                    violation_date, violation_year, violation_month, violation_day_of_week, violation_hour,
                    fine_amount, penalty_amount, payment_amount, interest_amount,
                    violation_status, judgment_date, data_source, ingested_at
                )
                SELECT * FROM df_mapped
                """
            )
            
            count = len(df_mapped)
            logger.info(f"✅ Loaded {count} traffic violations")
            return count
            
        except Exception as e:
            logger.error(f"❌ Traffic violation loading failed: {e}")
            return 0
    
    def populate_dimension_tables(self):
        """Populate dimension tables from fact table."""
        logger.info("🔄 Populating dimension tables...")
        
        # dim_time - populate for last 5 years
        logger.info("  → dim_time...")
        self.con.execute("""
            INSERT INTO dim_time
            WITH RECURSIVE dates AS (
                SELECT DATE '2020-01-01' as d
                UNION ALL
                SELECT d + INTERVAL 1 DAY
                FROM dates
                WHERE d < TODAY()
            )
            SELECT 
                d as date_key,
                YEAR(d) as year,
                MONTH(d) as month,
                DAY(d) as day_of_month,
                DAYNAME(d) as day_of_week,
                WEEKOFYEAR(d) as week_of_year,
                DAYOFWEEK(d) IN (1, 7) as is_weekend,
                FALSE as is_holiday,
                QUARTER(d) as quarter,
                CONCAT(YEAR(d), '-Q', QUARTER(d)) as fiscal_period
            FROM dates
            ON CONFLICT DO NOTHING
        """)
        
        # dim_violation_type - extract from facts
        logger.info("  → dim_violation_type...")
        self.con.execute("""
            INSERT INTO dim_violation_type
            SELECT DISTINCT
                violation_code,
                violation_description,
                NULL as violation_category,
                CASE 
                    WHEN violation_code LIKE '%SPEED%' OR violation_code LIKE '%ZONE%' THEN 'HIGH'
                    ELSE 'MEDIUM'
                END as severity_level,
                NULL as default_fine_amount,
                NULL as default_points,
                violation_code LIKE '%SPEED%' as is_speed_related
            FROM fct_violations
            WHERE violation_code IS NOT NULL
            ON CONFLICT DO NOTHING
        """)
        
        # dim_driver - extract from facts
        logger.info("  → dim_driver...")
        self.con.execute("""
            INSERT INTO dim_driver
            SELECT 
                driver_id,
                MIN(driver_age) as estimated_age_at_first_violation,
                COUNT(*) as total_violations,
                SUM(COALESCE(points_assessed, 0)) as total_points_accumulated,
                MIN(violation_date) as first_violation_date,
                MAX(violation_date) as last_violation_date,
                COUNT(*) >= 5 as is_repeat_offender,
                SUM(CASE WHEN violation_date >= TODAY() - INTERVAL 1 YEAR THEN 1 ELSE 0 END) as violations_last_year,
                SUM(CASE WHEN violation_date >= TODAY() - INTERVAL 1 MONTH THEN 1 ELSE 0 END) as violations_last_month,
                (SELECT violation_code FROM fct_violations f2 WHERE f2.driver_id = f.driver_id GROUP BY violation_code ORDER BY COUNT(*) DESC LIMIT 1) as most_common_violation_code,
                NOW() as last_updated
            FROM fct_violations f
            WHERE driver_id IS NOT NULL
            GROUP BY driver_id
            ON CONFLICT DO NOTHING
        """)
        
        logger.info("✅ Dimension tables populated")
    
    def compute_aggregates(self):
        """Compute aggregate tables for analysis."""
        logger.info("🔢 Computing aggregate tables...")
        
        # Risk scores by location
        logger.info("  → agg_risk_scores_by_location...")
        self.con.execute("""
            DELETE FROM agg_risk_scores_by_location;
            
            INSERT INTO agg_risk_scores_by_location
            SELECT 
                ROW_NUMBER() OVER (ORDER BY county, street_name) as location_id,
                street_name,
                county,
                NULL as borough,
                precinct,
                NULL as latitude,
                NULL as longitude,
                
                SUM(CASE WHEN violation_date >= TODAY() - INTERVAL 30 DAY THEN 1 ELSE 0 END) as violations_last_30_days,
                SUM(CASE WHEN violation_date >= TODAY() - INTERVAL 90 DAY THEN 1 ELSE 0 END) as violations_last_90_days,
                COUNT(*) as violations_all_time,
                
                -- Simple risk score (can be refined)
                ROUND(
                    100.0 * (
                        SUM(CASE WHEN violation_date >= TODAY() - INTERVAL 30 DAY THEN 1 ELSE 0 END) * 0.5 +
                        SUM(CASE WHEN violation_date >= TODAY() - INTERVAL 90 DAY THEN 1 ELSE 0 END) * 0.3 +
                        COUNT(*) * 0.2
                    ) / NULLIF(COUNT(*), 0),
                    2
                ) as risk_score,
                
                CASE 
                    WHEN COUNT(*) > 1000 THEN 'CRITICAL'
                    WHEN COUNT(*) > 500 THEN 'HIGH'
                    WHEN COUNT(*) > 100 THEN 'MEDIUM'
                    ELSE 'LOW'
                END as risk_tier,
                
                COUNT(DISTINCT violation_code) as violation_types_count,
                ROUND(AVG(COALESCE(fine_amount, 0)), 2) as avg_fine,
                ROUND(AVG(COALESCE(points_assessed, 0)), 2) as avg_points,
                
                TODAY() as computed_date
            FROM fct_violations
            WHERE street_name IS NOT NULL OR county IS NOT NULL
            GROUP BY street_name, county, precinct
        """)
        
        # Repeat offenders
        logger.info("  → agg_repeat_offenders...")
        self.con.execute("""
            DELETE FROM agg_repeat_offenders;
            
            INSERT INTO agg_repeat_offenders
            SELECT 
                driver_id,
                COUNT(*) as violation_count,
                SUM(COALESCE(points_assessed, 0)) as total_points,
                ROUND(AVG(COALESCE(driver_age, 0))) as estimated_avg_age,
                MIN(violation_date) as first_violation_date,
                MAX(violation_date) as last_violation_date,
                
                CASE 
                    WHEN COUNT(*) >= 10 THEN 'CRITICAL'
                    WHEN COUNT(*) >= 5 THEN 'HIGH'
                    WHEN COUNT(*) >= 2 THEN 'MEDIUM'
                    ELSE 'LOW'
                END as offender_tier,
                
                SUM(CASE WHEN violation_date >= TODAY() - INTERVAL 1 YEAR THEN 1 ELSE 0 END) as violations_last_year,
                (SELECT violation_code FROM fct_violations f2 WHERE f2.driver_id = f.driver_id GROUP BY violation_code ORDER BY COUNT(*) DESC LIMIT 1) as most_common_violation_code,
                (SELECT county FROM fct_violations f2 WHERE f2.driver_id = f.driver_id GROUP BY county ORDER BY COUNT(*) DESC LIMIT 1) as most_common_county,
                
                TODAY() as computed_date
            FROM fct_violations f
            WHERE driver_id IS NOT NULL
            GROUP BY driver_id
            HAVING COUNT(*) >= 2
            ORDER BY COUNT(*) DESC
        """)
        
        logger.info("✅ Aggregates computed")
    
    def get_stats(self) -> dict:
        """Get warehouse statistics."""
        if not self.con:
            return {}
        
        try:
            stats = {
                'total_violations': (self.con.execute("SELECT COUNT(*) FROM fct_violations").fetchone() or [0])[0],
                'unique_drivers': (self.con.execute("SELECT COUNT(DISTINCT driver_id) FROM fct_violations").fetchone() or [0])[0],
                'unique_locations': (self.con.execute("SELECT COUNT(DISTINCT street_name) FROM fct_violations").fetchone() or [0])[0],
                'date_range': self.con.execute("SELECT MIN(violation_date), MAX(violation_date) FROM fct_violations").fetchone()
            }
            return stats
        except Exception as e:
            logger.error(f"❌ Stats retrieval failed: {e}")
            return {}


def ingest_pipeline(
    duckdb_path: str,
    cleaned_dir: str,
    schema_file: str,
    fresh_start: bool = False
) -> bool:
    """
    Full ingestion pipeline.
    
    Args:
        duckdb_path: Path to DuckDB file
        cleaned_dir: Directory with cleaned parquet files
        schema_file: Path to SQL schema file
        fresh_start: If True, drops existing tables
    
    Returns:
        Success boolean
    """
    ingester = DuckDBIngester(duckdb_path)
    
    try:
        ingester.connect()
        
        # Initialize schema
        if not ingester.initialize_schema(schema_file):
            return False
        
        # Load data
        cleaned_path = Path(cleaned_dir)
        speed_file = cleaned_path / 'cleaned_speed_cameras.parquet'
        violation_file = cleaned_path / 'cleaned_traffic_violations.parquet'
        
        ingester.load_speed_cameras(str(speed_file))
        ingester.load_traffic_violations(str(violation_file))
        
        # Populate dimensions
        ingester.populate_dimension_tables()
        
        # Compute aggregates
        ingester.compute_aggregates()
        
        # Print stats
        stats = ingester.get_stats()
        logger.info("\n📊 WAREHOUSE STATS:")
        logger.info(f"  Total violations: {stats.get('total_violations', 0):,}")
        logger.info(f"  Unique drivers: {stats.get('unique_drivers', 0):,}")
        logger.info(f"  Unique locations: {stats.get('unique_locations', 0):,}")
        if stats.get('date_range'):
            logger.info(f"  Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        return False
    finally:
        ingester.close()


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    
    root_dir = Path(__file__).resolve().parents[2]
    default_duckdb = root_dir / "data" / "duckdb" / "test.duckdb"
    default_cleaned = root_dir / "data" / "cleaned"
    default_schema = root_dir / "backend" / "sql" / "01_schema.sql"

    parser = argparse.ArgumentParser(description="Ingest cleaned data into DuckDB")
    parser.add_argument("--duckdb-path", default=str(default_duckdb), help="DuckDB path")
    parser.add_argument("--cleaned-dir", default=str(default_cleaned), help="Cleaned data directory")
    parser.add_argument("--schema-file", default=str(default_schema), help="Schema SQL file")
    parser.add_argument("--fresh", action="store_true", help="Fresh start (drop existing tables)")
    
    args = parser.parse_args()
    
    success = ingest_pipeline(
        duckdb_path=args.duckdb_path,
        cleaned_dir=args.cleaned_dir,
        schema_file=args.schema_file,
        fresh_start=args.fresh
    )
    
    exit(0 if success else 1)
