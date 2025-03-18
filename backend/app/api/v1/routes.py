from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.services.pipeline import (
    generate_sales_data, forecast_and_reorder,
    get_demand_forecast, get_top_products, get_inventory_status,
)

router = APIRouter(prefix="/api/v1/retail", tags=["retail"])


class RetailRequest(BaseModel):
    days: int = 180
    seed: int = 42


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "domain": "retail"}


@router.post("/recommendations")
def recommendations(req: RetailRequest) -> dict:
    df = generate_sales_data(req.days, req.seed)
    out = forecast_and_reorder(df)
    out["sample"] = df.tail(7).to_dict(orient="records")
    return out


@router.post("/forecast")
def forecast(req: RetailRequest) -> dict:
    df = generate_sales_data(req.days, req.seed)
    return get_demand_forecast(df, horizon=30)


@router.post("/top-products")
def top_products(req: RetailRequest) -> list:
    return get_top_products(req.seed)


@router.post("/inventory-status")
def inventory_status(req: RetailRequest) -> list:
    return get_inventory_status(req.seed)
