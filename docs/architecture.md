# Architecture

## Frontend (Unique)
- Inventory Control Board

## Backend (Robust)
- Forecast + reorder API
- FastAPI routers/services/schemas separation
- Input validation and typed responses

## Database
- SQLite tables: products, sales_history, forecast_runs, recommendations
- Local SQLite for student setup, PostgreSQL upgrade path

## Data Flow
1. Ingest/load raw data into `data/raw/`
2. Clean and transform into `data/processed/`
3. Run analysis/model pipeline via `backend/app/services/`
4. Expose summaries via API endpoints
5. Render visuals in `frontend/app.py`
6. Save charts/reports in `outputs/`
