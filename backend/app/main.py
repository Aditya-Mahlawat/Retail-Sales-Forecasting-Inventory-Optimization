from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from backend.app.api.v1.routes import router
from backend.app.core.database import init_db, engine
from backend.app.services.data_generator import seed_database_if_empty

app = FastAPI(
    title="NexStock Enterprise · Retail Sales Forecasting & Multi-Echelon Inventory Optimization Suite",
    description="Production-grade retail supply chain intelligence API with multi-model demand forecasting, stochastic safety stock optimization, EOQ analysis, 9-box ABC-XYZ portfolio matrix, what-if stress testing, and purchase order lifecycle management.",
    version="2.0.0",
)

# Enable CORS for local and web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
def on_startup() -> None:
    init_db()
    with Session(engine) as session:
        seed_database_if_empty(session)
