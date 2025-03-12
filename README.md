# Retail-Sales-Forecasting-Inventory-Optimization

An end-to-end retail analytics platform that combines demand forecasting with real-time inventory optimization. Built with a FastAPI backend and an interactive Streamlit dashboard (InventIQ).

## Features

- **Demand Forecasting** — Linear regression model trained on synthetic historical sales data, producing 30-day unit-demand forecasts with confidence bands
- **Inventory Health Monitoring** — Per-SKU stock level tracking with CRITICAL / LOW / OK thresholds and reorder-point alerts
- **Top Product Rankings** — Revenue, margin, and units-sold leaderboards with scatter analysis
- **Interactive Dashboard** — Dark-themed Streamlit UI with Plotly charts; configurable history window and simulation seed

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + Uvicorn |
| Data / ML | pandas, scikit-learn, numpy |
| Frontend | Streamlit + Plotly |
| Data Layer | Synthetic data generation (seed-reproducible) |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/v1/routes.py      # API endpoints
│   │   ├── services/pipeline.py  # Forecasting & inventory logic
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   └── main.py               # FastAPI app entry point
│   └── tests/
├── frontend/
│   └── app.py                    # Streamlit dashboard
├── requirements.txt
└── run_windows.ps1
```

## Getting Started

```bash
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the backend (port 8001)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload

# 4. Start the frontend (port 8501)
streamlit run frontend/app.py --server.port 8501
```

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/v1/retail/forecast` | 30-day demand forecast |
| POST | `/api/v1/retail/inventory-status` | Stock health per SKU |
| POST | `/api/v1/retail/top-products` | Top SKU rankings |
| POST | `/api/v1/retail/full-analysis` | Combined analysis payload |

## Dashboard Preview

The dashboard runs at `http://localhost:8501` and includes:
- **Forecast Tab** — Historical vs predicted demand line chart with trend slope and R² score
- **Inventory Tab** — Per-SKU progress bars with status badges
- **Top Products Tab** — Revenue bar chart + units-sold vs margin scatter
- **Raw Data Tab** — Full dataset table with export

## License

MIT
