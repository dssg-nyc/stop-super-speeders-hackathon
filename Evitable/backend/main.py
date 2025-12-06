from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.database import get_db

app = FastAPI(
    title="Stop Super Speeders API",
    description="API for tracking high-risk drivers and vehicles in NYC",
    version="1.0.0"
)

from backend.api.violators import router as violators_router
from backend.api.upload import router as upload_router
from backend.api.intelligence import router as intelligence_router

app.include_router(violators_router, prefix="/api/violators", tags=["Violators"])
app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
app.include_router(intelligence_router, prefix="/api/intelligence", tags=["Intelligence"])

# CORS Setup
origins = [
    "http://localhost:3000",  # Next.js
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    db = get_db()
    from backend.services.data_service import initialize_views
    initialize_views()
    print("✅ System Startup: Database Connected & Views Registered")

@app.get("/")
async def root():
    return {"message": "Stop Super Speeders API is running 🚀"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
