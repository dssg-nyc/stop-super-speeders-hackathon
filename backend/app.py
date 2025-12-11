"""
SAFENY Super Speeder Detection Web Application

A simple web interface for DMV staff to upload CSV files and identify
drivers who meet the super speeder thresholds defined in the legislation.
"""

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil
import logging
from datetime import datetime
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.cleaning import clean_and_export
from src.ingestion import ingest_pipeline
from src.super_speeder_detector import SuperSpeederDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="SAFENY Super Speeder Detection System")

# Setup paths (project root → backend/frontend/data)
BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent
TEMPLATES_DIR = ROOT_DIR / "frontend" / "templates"
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
UPLOADS_DIR = RAW_DATA_DIR / "uploads"
CLEANED_DIR = DATA_DIR / "cleaned"
DUCKDB_PATH = DATA_DIR / "duckdb" / "test.duckdb"
SCHEMA_FILE = BASE_DIR / "sql" / "01_schema.sql"

# Create necessary directories
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_DIR.mkdir(parents=True, exist_ok=True)

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the upload page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@app.get("/resources", response_class=HTMLResponse)
async def resources(request: Request):
    """Render the resources page."""
    return templates.TemplateResponse(
        "resources.html",
        {"request": request}
    )


@app.post("/upload")
async def upload_and_process(
    request: Request,
    file: UploadFile = File(...),
    file_type: str = Form(...)
):
    """
    Handle CSV file upload and process through the pipeline.
    
    Args:
        file: Uploaded CSV file
        file_type: Either 'speed_camera' or 'traffic_violations'
    """
    try:
        # Validate filename exists
        if not file.filename:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error_title": "Invalid File",
                    "error_message": "Please upload a file with a valid filename."
                }
            )
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error_title": "Invalid File Type",
                    "error_message": "Please upload a CSV file. File must end with .csv"
                }
            )
        
        # Create timestamped upload directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        upload_batch_dir = UPLOADS_DIR / timestamp
        upload_batch_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        file_path = upload_batch_dir / file.filename
        logger.info(f"Saving uploaded file to {file_path}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {file.filename} ({file_path.stat().st_size} bytes)")
        
        # Step 1: Clean the data
        logger.info("Starting data cleaning...")
        speed_cameras_df, violations_df = clean_and_export(
            input_dir=str(upload_batch_dir),
            output_dir=str(CLEANED_DIR),
            file_patterns=["*.csv"]
        )
        
        new_records = len(speed_cameras_df) + len(violations_df)
        logger.info(f"Cleaning complete: {new_records} records cleaned")
        
        # Step 2: Ingest into DuckDB
        logger.info("Starting data ingestion...")
        ingest_stats = ingest_pipeline(
            cleaned_dir=str(CLEANED_DIR),
            duckdb_path=str(DUCKDB_PATH),
            schema_file=str(SCHEMA_FILE)
        )
        
        logger.info(f"Ingestion complete: {ingest_stats}")
        
        # Step 3: Detect super speeders
        logger.info("Detecting super speeders...")
        with SuperSpeederDetector(str(DUCKDB_PATH)) as detector:
            super_speeders, warning_drivers, summary = detector.detect_super_speeders()
            warehouse_stats = detector.get_ingestion_stats()
        
        logger.info(f"Detection complete: {len(super_speeders)} super speeders, {len(warning_drivers)} warning drivers")
        
        # Render results page
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "file_name": file.filename,
                "file_type": file_type.replace('_', ' ').title(),
                "new_records": new_records,
                "super_speeders": super_speeders,
                "warning_drivers": warning_drivers,
                "summary": summary,
                "warehouse_stats": warehouse_stats,
                "timestamp": timestamp
            }
        )
    
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Processing Error",
                "error_message": f"An error occurred while processing your file: {str(e)}. Please check that your CSV file is properly formatted."
            }
        )


@app.get("/driver/{driver_id}", response_class=HTMLResponse)
async def driver_details(request: Request, driver_id: str):
    """Show detailed view for a specific driver."""
    try:
        with SuperSpeederDetector(str(DUCKDB_PATH)) as detector:
            driver_info = detector.get_driver_details(driver_id)
        
        return templates.TemplateResponse(
            "driver_details.html",
            {
                "request": request,
                "driver": driver_info
            }
        )
    
    except Exception as e:
        logger.error(f"Error fetching driver details: {str(e)}", exc_info=True)
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_title": "Driver Not Found",
                "error_message": f"Could not load details for driver {driver_id}"
            }
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "duckdb_exists": DUCKDB_PATH.exists(),
        "schema_exists": SCHEMA_FILE.exists()
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("🚔 SAFENY Super Speeder Detection System")
    print("=" * 80)
    print(f"Starting server at http://localhost:8000")
    print(f"DuckDB: {DUCKDB_PATH}")
    print(f"Uploads: {UPLOADS_DIR}")
    print("=" * 80)
    print("💡 Hot-reload enabled: Edit templates/code and refresh browser!")
    print("=" * 80)
    
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
