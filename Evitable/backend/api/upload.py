from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import io
import pandas as pd
import duckdb
from datetime import datetime
from pathlib import Path
from backend.core.database import DATA_DIR

router = APIRouter()

@router.get("/template/{type}")
async def get_template(type: str):
    """
    Returns a CSV template for the requested type (drivers/plates).
    """
    if type == "drivers":
        # Based on nyc_traffic_violations_historic schema
        df = pd.DataFrame(columns=["license_id", "violation_year", "violation_month", "points", "county"])
    elif type == "plates":
        # Based on nyc_speed_cameras_historic schema
        df = pd.DataFrame(columns=["plate", "state", "issue_date", "violation_time", "fine_amount"])
    else:
        raise HTTPException(status_code=400, detail="Invalid template type. Use 'drivers' or 'plates'.")
    
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=template_{type}.csv"
    return response

@router.post("/analyze")
async def analyze_upload(
    file: UploadFile = File(...), 
    save: bool = True
):
    """
    Analyzes an uploaded CSV file.
    Detects if it's a Driver file (has license_id) or Plate file (has plate).
    Returns list of violators found in the file.
    if save=True, persists the file to the data directory and refreshes the historic views.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    content = await file.read()
    
    try:
        # Load into pandas to infer schema casually, then into DuckDB
        # Using on-the-fly duckdb connection for isolation
        con = duckdb.connect(database=':memory:')
        
        # We need to save bytes to a temp file or read via pandas
        # Reading via pandas is easiest for small uploads
        df = pd.read_csv(io.BytesIO(content))
        
        columns = [c.lower() for c in df.columns]
        
        results = {}
        file_prefix = "upload" # Default fallback
        
        if "license_id" in columns and "points" in columns:
            analyze_type = "drivers"
            file_prefix = "nyc_traffic_violations"
            # Register DF
            con.register('uploaded_drivers', df)
            
            # Run Driver Logic
            if "violation_year" in columns and "violation_month" in columns:
                 query = """
                SELECT 
                    license_id,
                    SUM(points) as total_points,
                    COUNT(*) as violation_count
                FROM uploaded_drivers
                GROUP BY license_id
                HAVING SUM(points) >= 11
                ORDER BY total_points DESC
                """
                 violators = con.execute(query).df().to_dict(orient="records")
                 results = {"type": "drivers", "count": len(violators), "violators": violators}
            else:
                 results = {"error": "Missing violation_year/violation_month columns for driver analysis"}

        elif "plate" in columns and "issue_date" in columns:
            analyze_type = "plates"
            file_prefix = "nyc_speed_cameras"
            con.register('uploaded_plates', df)
            
            # Run Plate Logic
            query = """
            SELECT 
                plate,
                state,
                COUNT(*) as ticket_count
            FROM uploaded_plates
            GROUP BY plate, state
            HAVING COUNT(*) >= 16
            ORDER BY ticket_count DESC
            """
            violators = con.execute(query).df().fillna("").to_dict(orient="records")
            results = {"type": "plates", "count": len(violators), "violators": violators}
            
        else:
            raise HTTPException(status_code=400, detail="Could not detect valid Driver (license_id, points) or Plate (plate, issue_date) columns.")

        # Save Logic
        if save and "error" not in results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize original filename
            original_name = Path(file.filename).stem
            # Format: {prefix}_{timestamp}_{original_name}.csv
            # e.g. nyc_traffic_violations_20231027_101010_myupload.csv
            new_filename = f"{file_prefix}_{timestamp}_{original_name}.csv"
            save_path = DATA_DIR / new_filename
            
            # Write content to file
            with open(save_path, "wb") as f:
                f.write(content)
            
            print(f"💾 Saved uploaded file to: {save_path}")
            
            # Refresh Views
            from backend.services.data_service import initialize_views
            initialize_views()
            
            results["message"] = "File uploaded, analyzed, and integrated into historic data."

        return results

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
