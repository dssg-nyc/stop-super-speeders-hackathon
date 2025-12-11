"""
SAFENY Data Cleaning Module
Standardizes NYC traffic violation datasets for analytics
"""

import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataCleaner:
    """Validates and cleans NYC traffic violation datasets."""
    
    def __init__(self, strict_mode=False):
        """
        Args:
            strict_mode: If True, drop rows with ANY nulls. If False, drop only critical nulls.
        """
        self.strict_mode = strict_mode
        self.stats = {}
    
    # ============ SPEED CAMERA DATA CLEANING ============
    
    def clean_speed_cameras(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean speed camera violation data.
        
        Flexible handling of different column name variations.
        """
        logger.info(f"🔍 Cleaning speed camera data: {len(df)} rows input")
        input_count = len(df)
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower().str.strip()
        
        # Map alternative column names
        col_map = {
            'created_at': 'created_at',
            'issue date': 'issued_date',
            'issue_date': 'issued_date',
            'issued_date': 'issued_date',
            'issue year': 'issue_year',
            'issue_year': 'issue_year',
            'issue month': 'issue_month',
            'issue_month': 'issue_month',
            'issue day': 'issue_day',
            'issue_day': 'issue_day',
            'summons number': 'summons_number',
            'summons_number': 'summons_number',
            'violation': 'violation',
            'plate': 'plate',
            'plate id': 'plate',
            'plate_id': 'plate',
            'fine amount': 'fine_amount',
            'fine_amount': 'fine_amount',
            'penalty amount': 'penalty_amount',
            'penalty_amount': 'penalty_amount',
            'payment amount': 'payment_amount',
            'payment_amount': 'payment_amount',
            'interest amount': 'interest_amount',
            'interest_amount': 'interest_amount',
            'amount due': 'amount_due',
            'amount_due': 'amount_due',
            'violation status': 'violation_status',
            'violation_status': 'violation_status',
            'violation county': 'county',
        }
        
        for old_name, new_name in col_map.items():
            if old_name in df.columns:
                df.rename(columns={old_name: new_name}, inplace=True)
        
        base_columns = list(df.columns)
        
        # 1. Remove critical nulls (check which columns exist)
        critical_cols = [col for col in ['summons_number', 'plate', 'fine_amount', 'issued_date'] if col in df.columns]
        if critical_cols:
            df = df.dropna(subset=critical_cols)
        
        if self.strict_mode:
            df = df.dropna(subset=base_columns)
        
        # 2. Standardize dates - try multiple column name variations
        if 'issued_date' in df.columns:
            df['issued_date'] = pd.to_datetime(df['issued_date'], errors='coerce')
        elif 'issue_year' in df.columns and 'issue_month' in df.columns:
            issue_year = pd.to_numeric(df.get('issue_year', pd.Series(dtype='object')), errors='coerce')
            issue_month = pd.to_numeric(df.get('issue_month', pd.Series(dtype='object')), errors='coerce')
            issue_day = pd.to_numeric(df.get('issue_day', pd.Series(1, index=df.index)), errors='coerce') if 'issue_day' in df.columns else pd.Series(1, index=df.index)
            issue_day = issue_day.clip(lower=1, upper=31).fillna(1)
            
            df['issued_date'] = pd.to_datetime(
                pd.DataFrame({
                    'year': issue_year.astype('Int64'),
                    'month': issue_month.astype('Int64'),
                    'day': issue_day.astype('Int64')
                }),
                errors='coerce'
            )
        else:
            df['issued_date'] = pd.NaT
        
        if 'judgment_entry_date' in df.columns:
            df['judgment_entry_date'] = pd.to_datetime(df['judgment_entry_date'], errors='coerce')
        
        # Try to get date fields from either issued_date or year/month/day columns
        if 'issued_date' in df.columns and df['issued_date'].notna().any():
            df['violation_year'] = pd.to_datetime(df['issued_date']).dt.year
            df['violation_month'] = pd.to_datetime(df['issued_date']).dt.month
            df['violation_day_of_week'] = pd.to_datetime(df['issued_date']).dt.day_name()
        else:
            df['violation_year'] = pd.to_numeric(df.get('issue_year', pd.Series(dtype='object')), errors='coerce')
            df['violation_month'] = pd.to_numeric(df.get('issue_month', pd.Series(dtype='object')), errors='coerce')
            df['violation_day_of_week'] = None
        
        if 'issue_year' in df.columns:
            df['violation_year'] = df['violation_year'].fillna(pd.to_numeric(df['issue_year'], errors='coerce'))
        if 'issue_month' in df.columns:
            df['violation_month'] = df['violation_month'].fillna(pd.to_numeric(df['issue_month'], errors='coerce'))
        
        # Try to extract hour from violation_time (format: HH:MM? or HH:MM A/P)
        violation_time_col = df.get('violation_time', df.get('violation time', pd.Series([None]*len(df), index=df.index)))
        if not isinstance(violation_time_col, pd.Series):
            violation_time_col = pd.Series(violation_time_col, index=df.index)
        df['violation_hour'] = self._extract_hour(violation_time_col)
        
        # 3. Normalize column names and validate numeric columns
        df.columns = df.columns.str.lower().str.strip()
        numeric_cols = ['fine_amount', 'penalty_amount', 'payment_amount', 'interest_amount', 'amount_due']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna(0.0)
            else:
                df[col] = 0.0
        
        # 4. Standardize text fields
        if 'violation' in df.columns:
            df['violation'] = df['violation'].astype(str).str.strip().str.upper()
        else:
            df['violation'] = 'UNKNOWN'
        if 'county' in df.columns:
            df['county'] = df['county'].fillna('UNKNOWN').astype(str).str.strip().str.upper()
        else:
            df['county'] = 'UNKNOWN'
        if 'plate' in df.columns:
            df['plate'] = df['plate'].astype(str).str.strip().str.upper()
        else:
            df['plate'] = None
        
        # 5. Remove duplicates (keep first)
        if 'summons_number' in df.columns:
            df = df.drop_duplicates(subset=['summons_number'], keep='first')
        
        # 6. Add source marker
        df['data_source'] = 'SPEED_CAMERA'
        
        output_count = len(df)
        self.stats['speed_cameras'] = {
            'input': input_count,
            'output': output_count,
            'removed': input_count - output_count,
            'pct_retained': round(100 * output_count / input_count, 1) if input_count > 0 else 0
        }
        logger.info(f"✅ Speed camera cleaned: {output_count} rows ({self.stats['speed_cameras']['pct_retained']}% retained)")
        
        return df
    
    # ============ TRAFFIC VIOLATIONS DATA CLEANING ============
    
    def clean_traffic_violations(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean traffic violation records.
        Flexible handling of different column name variations.
        """
        logger.info(f"🔍 Cleaning traffic violation data: {len(df)} rows input")
        input_count = len(df)
        
        # Normalize column names to lowercase
        df.columns = df.columns.str.lower().str.strip()
        
        # Standardize column names to canonical fields
        rename_map = {
            'violation code': 'v_code',
            'violation_code': 'v_code',
            'v code': 'v_code',
            'violation year': 'v_year',
            'violation_year': 'v_year',
            'v year': 'v_year',
            'violation month': 'v_month',
            'violation_month': 'v_month',
            'v month': 'v_month',
            'license_id': 'lic_id',
            'license id': 'lic_id',
            'lic id': 'lic_id',
            'driver_id': 'lic_id'
        }
        for old, new in rename_map.items():
            if old in df.columns:
                df.rename(columns={old: new}, inplace=True)
        
        base_columns = list(df.columns)
        
        # 1. Remove critical nulls (check which columns exist)
        critical_cols = [col for col in ['lic_id', 'v_code', 'v_year', 'v_month'] if col in df.columns]
        if critical_cols:
            df = df.dropna(subset=critical_cols)
        
        if self.strict_mode:
            df = df.dropna(subset=base_columns)
        
        # Reconstruct violation_date from v_year and v_month (or violation_year/violation_month)
        year_col = 'v_year' if 'v_year' in df.columns else None
        month_col = 'v_month' if 'v_month' in df.columns else None
        
        if year_col and month_col:
            df[year_col] = pd.to_numeric(df[year_col], errors='coerce').astype('Int64')
            df[month_col] = pd.to_numeric(df[month_col], errors='coerce').astype('Int64')
            
            # Validate year and month ranges
            df = df[(df[year_col] >= 2000) & (df[year_col] <= pd.Timestamp.now().year)]
            df = df[(df[month_col] >= 1) & (df[month_col] <= 12)]
            
            df['violation_date'] = pd.to_datetime(
                pd.DataFrame({
                    'year': df[year_col].astype('Int64'),
                    'month': df[month_col].astype('Int64'),
                    'day': pd.Series(1, index=df.index, dtype='Int64')
                }),
                errors='coerce'
            )
        else:
            df['violation_date'] = pd.NaT
        
        # 3. Extract year, month, day_of_week
        mask = df['violation_date'].notna()
        df.loc[mask, 'violation_year'] = pd.to_datetime(df.loc[mask, 'violation_date']).dt.year
        df.loc[mask, 'violation_month'] = pd.to_datetime(df.loc[mask, 'violation_date']).dt.month
        df.loc[mask, 'violation_day_of_week'] = pd.to_datetime(df.loc[mask, 'violation_date']).dt.day_name()
        
        # Fallback to year_col/month_col if needed
        if year_col and ('violation_year' not in df.columns or df['violation_year'].isna().all()):
            df['violation_year'] = df.get(year_col, None)
        if month_col and ('violation_month' not in df.columns or df['violation_month'].isna().all()):
            df['violation_month'] = df.get(month_col, None)
            
        df['violation_hour'] = None  # Traffic violations don't have hour granularity
        
        # 4. Validate numeric columns
        if 'age' in df.columns:
            df['age'] = pd.to_numeric(df['age'], errors='coerce')
            # Validate age
            df = df[(df['age'].isna()) | ((df['age'] >= 16) & (df['age'] <= 120))]
            
        if 'points' in df.columns:
            df['points'] = pd.to_numeric(df['points'], errors='coerce').fillna(0).astype(int)
        else:
            df['points'] = 0
        
        # 5. Standardize text
        code_col = None
        for col in ['v_code', 'violation_code', 'violation code']:
            if col in df.columns:
                code_col = col
                break
        if code_col:
            df[code_col] = df[code_col].astype(str).str.strip().str.upper()
        
        if 'county' in df.columns:
            df['county'] = df['county'].fillna('UNKNOWN').astype(str).str.strip().str.upper()
        else:
            df['county'] = 'UNKNOWN'
        
        # Find driver ID column (could be lic_id, license_id, etc.)
        driver_id_col = None
        for col in ['lic_id', 'license_id', 'driver_id']:
            if col in df.columns:
                driver_id_col = col
                break
        if driver_id_col:
            df[driver_id_col] = df[driver_id_col].astype(str).str.strip().str.upper()
        
        # 6. Remove duplicates on key columns that exist
        subset_cols = [col for col in [driver_id_col, code_col, 'violation_date'] if col and col in df.columns]
        if subset_cols:
            df = df.drop_duplicates(subset=subset_cols, keep='first')
        
        # 7. Add source marker
        df['data_source'] = 'TRAFFIC_VIOLATIONS'
        
        output_count = len(df)
        self.stats['traffic_violations'] = {
            'input': input_count,
            'output': output_count,
            'removed': input_count - output_count,
            'pct_retained': round(100 * output_count / input_count, 1) if input_count > 0 else 0
        }
        logger.info(f"✅ Traffic violations cleaned: {output_count} rows ({self.stats['traffic_violations']['pct_retained']}% retained)")
        
        return df
    
    # ============ UTILITY FUNCTIONS ============
    
    @staticmethod
    def _extract_hour(time_series: pd.Series) -> pd.Series:
        """Extract hour from time strings like '02:43P' or '10:52A'"""
        def parse_hour(t):
            if pd.isna(t):
                return None
            try:
                t = str(t).strip().upper()
                if 'A' in t or 'P' in t:
                    dt = pd.to_datetime(t, format='%I:%M%p', errors='coerce')
                    return dt.hour if pd.notna(dt) else None
                elif ':' in t:
                    hour = int(t.split(':')[0])
                    return hour if 0 <= hour <= 23 else None
            except Exception:
                pass
            return None
        
        return time_series.apply(parse_hour)
    
    def get_stats(self) -> Dict:
        """Return cleaning statistics"""
        return self.stats


# ============ MAIN PIPELINE ============

def clean_and_export(
    input_dir: str,
    output_dir: str,
    file_patterns: Optional[List[str]] = None,
    strict_mode: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load raw datasets, clean them, and export to output directory.
    
    Args:
        input_dir: Directory containing raw CSV/Parquet files
        output_dir: Directory to write cleaned files
        file_patterns: Specific file patterns to process (e.g., ['test3*'])
        strict_mode: If True, drop any rows with nulls
    
    Returns:
        Tuple of (cleaned_speed_cameras_df, cleaned_violations_df)
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    cleaner = DataCleaner(strict_mode=strict_mode)
    
    # Find datasets
    speed_camera_files = list(input_path.glob('*speed_cameras*.csv')) + list(input_path.glob('*speed_cameras*.parquet'))
    violation_files = list(input_path.glob('*traffic_violations*.csv')) + list(input_path.glob('*traffic_violations*.parquet'))
    
    # Filter by pattern if specified
    if file_patterns:
        import fnmatch
        speed_camera_files = [f for f in speed_camera_files if any(fnmatch.fnmatch(f.name, p) for p in file_patterns)]
        violation_files = [f for f in violation_files if any(fnmatch.fnmatch(f.name, p) for p in file_patterns)]
    
    logger.info(f"\n📂 Found {len(speed_camera_files)} speed camera files and {len(violation_files)} violation files")
    
    # Load and clean speed cameras
    speed_dfs = []
    for file in speed_camera_files:
        logger.info(f"📥 Loading {file.name}...")
        if file.suffix == '.parquet':
            df = pd.read_parquet(file)
        else:
            df = pd.read_csv(file)
        df_clean = cleaner.clean_speed_cameras(df)
        speed_dfs.append(df_clean)
    
    # Load and clean violations
    violation_dfs = []
    for file in violation_files:
        logger.info(f"📥 Loading {file.name}...")
        if file.suffix == '.parquet':
            df = pd.read_parquet(file)
        else:
            df = pd.read_csv(file)
        df_clean = cleaner.clean_traffic_violations(df)
        violation_dfs.append(df_clean)
    
    # Combine
    speed_cameras_combined = pd.concat(speed_dfs, ignore_index=True) if speed_dfs else pd.DataFrame()
    violations_combined = pd.concat(violation_dfs, ignore_index=True) if violation_dfs else pd.DataFrame()
    
    # Export
    if len(speed_cameras_combined) > 0:
        out_file = output_path / 'cleaned_speed_cameras.parquet'
        speed_cameras_combined.to_parquet(out_file, index=False)
        logger.info(f"✅ Exported {len(speed_cameras_combined)} speed camera records to {out_file}")
    
    if len(violations_combined) > 0:
        out_file = output_path / 'cleaned_traffic_violations.parquet'
        violations_combined.to_parquet(out_file, index=False)
        logger.info(f"✅ Exported {len(violations_combined)} violation records to {out_file}")
    
    # Print stats
    logger.info("\n📊 CLEANING SUMMARY:")
    for dataset, stats in cleaner.get_stats().items():
        logger.info(f"  {dataset}: {stats['output']:,} rows ({stats['pct_retained']}% retained)")
    
    return speed_cameras_combined, violations_combined


if __name__ == "__main__":
    import argparse
    
    root_dir = Path(__file__).resolve().parents[2]
    default_input = root_dir / "data" / "raw"
    default_output = root_dir / "data" / "cleaned"

    parser = argparse.ArgumentParser(description="Clean NYC traffic violation datasets")
    parser.add_argument("--input-dir", default=str(default_input), help="Input directory")
    parser.add_argument("--output-dir", default=str(default_output), help="Output directory")
    parser.add_argument("--strict", action="store_true", help="Drop all rows with any nulls")
    parser.add_argument("--pattern", nargs="+", help="File patterns to process (e.g., test3*)")
    
    args = parser.parse_args()
    
    clean_and_export(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        file_patterns=args.pattern,
        strict_mode=args.strict
    )
