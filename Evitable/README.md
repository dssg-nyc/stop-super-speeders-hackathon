# Stop Super Speeders System 🚦

Families for Safe Streets Logic Monitor - Built for NYC DSSG Hackathon.

## 🏗️ Architecture
-   **Backend**: FastAPI + DuckDB (Data Processing & API).
-   **Frontend**: Next.js + ShadcnUI (Premium Dashboard).
-   **Data**: Historical Traffic Violations & Speed Camera data.

## 🚀 How to Run (Quickstart)

### Option 1: Development Mode (Active)
The system is set up for local development.

**1. Backend** (Port 8000)
```bash
cd backend
# If not running already
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
View Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

**2. Frontend** (Port 3000)
```bash
cd frontend
npm run dev
```
View Dashboard: [http://localhost:3000](http://localhost:3000)

### Option 2: Docker Compose (Production-like)
To run everything with one command:
```bash
docker-compose up --build
```

## 📊 Features Implemented
1.  **Driver Triggers**: Identifies drivers with 11+ points in 24 months.
2.  **Plate Triggers**: Identifies vehicles with 16+ tickets in 12 months.
3.  **Visual Dashboard**:
    -   High-level counters.
    -   Badges for severity.
    -   Tabbed tables for Drivers vs Vehicles.

## ✨ Advanced Features (Phase 2)

### 1. Data Upload (Sandbox Mode)
-   Navigate to the **"Sandbox Upload"** tab.
-   Download a template (Driver or Plate).
-   Upload your CSV to instantly check for violators.
-   *Privacy:* Data is processed in-memory and not stored permanently.

### 2. Intelligence Dashboard
-   Navigate to the **"Intelligence"** tab.
-   **At Risk Warning**: See drivers who are 1 ticket away from the threshold (9-10 points).
-   **Geo Breakdown**: Visual chart of violations by county.

### 3. Data Harmonization (Phase 3)
-   **Unified Data View**: The system now automatically ingests both *Historic* Parquet files and *Test* JSON/CSV files.
-   **Seamless Merge**: A DuckDB `UNION ALL` view combines `nyc_*_historic` with `test1_`, `test2_`, and `test3_` datasets.
-   **Analysis**: The "Super Speeder" logic runs across this combined dataset, ensuring even the newest test cases are captured.

## 📁 Key Files
-   `backend/services/data_service.py`: Core Logic & **Union View Construction**.
-   `backend/services/intelligence_service.py`: Predictive Logic.
-   `backend/api/upload.py`: CSV Parsing Logic.
-   `frontend/src/components/UploadSection.tsx`: Drag & Drop UI.
-   `frontend/src/components/IntelligenceSection.tsx`: Charts & Tables.
