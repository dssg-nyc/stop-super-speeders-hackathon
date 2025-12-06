from fastapi import APIRouter
from backend.services.intelligence_service import get_at_risk_drivers, get_geo_stats

router = APIRouter()

@router.get("/at-risk")
async def at_risk():
    data = get_at_risk_drivers()
    return {"count": len(data), "drivers": data}

@router.get("/geo-stats")
async def geo_stats():
    data = get_geo_stats()
    return {"stats": data}
