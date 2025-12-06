from fastapi import APIRouter, HTTPException
import pandas as pd
import io
from fastapi.responses import StreamingResponse
from backend.services.data_service import get_super_speeder_drivers, get_super_speeder_plates, get_monthly_violation_drivers

router = APIRouter()

@router.get("/drivers")
async def get_drivers():
    """
    Get list of drivers that triggered the ISA threshold (11+ pts / 24 mos).
    """
    results = get_super_speeder_drivers()
    return {"count": len(results), "violators": results}

@router.get("/drivers/recent")
async def get_recent_drivers():
    """
    Get list of drivers that triggered 11+ points in the LAST MONTH (Oct 2025).
    """
    results = get_monthly_violation_drivers(year=2025, month=10)
    return {"count": len(results), "violators": results}

@router.get("/drivers/download")
async def download_drivers():
    """
    Download High Risk Drivers (24 month) as CSV.
    """
    results = get_super_speeder_drivers()
    df = pd.DataFrame(results)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=high_risk_drivers_24mo.csv"
    return response

@router.get("/drivers/recent/download")
async def download_recent_drivers():
    """
    Download Recent High Risk Drivers (Oct 2025) as CSV.
    """
    results = get_monthly_violation_drivers(year=2025, month=10)
    df = pd.DataFrame(results)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=recent_high_risk_drivers_oct2025.csv"
    return response

@router.get("/plates")
async def get_plates():
    """
    Get list of plates that triggered the ISA threshold (16+ tickets / 12 mos).
    """
    results = get_super_speeder_plates()
    return {"count": len(results), "violators": results}

@router.get("/plates/download")
async def download_plates():
    """
    Download Dangerous Vehicles (12 month) as CSV.
    """
    results = get_super_speeder_plates()
    df = pd.DataFrame(results)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=dangerous_vehicles_12mo.csv"
    return response

