from typing import List, Dict, Any, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlmodel import Session, select

from backend.app.core.database import get_session
from backend.app.models.record import Product, DailySale, PurchaseOrder
from backend.app.schemas.record import (
    RetailRequest, ProductSchema, ForecastResponse, HistoryPoint,
    InventoryHealthItem, EOQItem, ABCXYZResponse,
    SimulationRequest, SimulationResponse,
    PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse,
    ExecutiveSummaryResponse,
)
from backend.app.services.data_generator import (
    seed_database_if_empty, reset_and_seed_database, ingest_sales_csv
)
from backend.app.services.forecasting import generate_forecast
from backend.app.services.inventory import (
    calculate_eoq, evaluate_inventory_health, compute_abc_xyz
)
from backend.app.services.simulation import run_supply_chain_simulation
from backend.app.services.order_service import (
    list_purchase_orders, create_purchase_order, update_purchase_order_status,
    generate_replenishment_suggestions
)
from backend.app.services.pipeline import (
    generate_sales_data, forecast_and_reorder,
    get_demand_forecast, get_top_products, get_inventory_status
)

router = APIRouter(prefix="/api/v1/retail", tags=["retail"])


def get_or_seed_sales(session: Session) -> Dict[str, pd.DataFrame]:
    """Helper to ensure DB is seeded and return sales grouped by SKU."""
    seed_database_if_empty(session)
    sales = session.exec(select(DailySale).order_by(DailySale.date)).all()
    if not sales:
        reset_and_seed_database(session)
        sales = session.exec(select(DailySale).order_by(DailySale.date)).all()
        
    df = pd.DataFrame([s.model_dump() for s in sales])
    sales_by_sku = {}
    for sku, group in df.groupby("sku"):
        sales_by_sku[str(sku)] = group.sort_values("date").reset_index(drop=True)
    return sales_by_sku


# ── Health & Executive Summary ───────────────────────────────────────────────

@router.get("/health")
def health() -> dict:
    return {"status": "ok", "platform": "NexStock Enterprise Supply Chain Intelligence", "version": "2.0.0"}


@router.get("/executive-summary", response_model=ExecutiveSummaryResponse)
def executive_summary(session: Session = Depends(get_session)) -> ExecutiveSummaryResponse:
    seed_database_if_empty(session)
    products = session.exec(select(Product)).all()
    sales_by_sku = get_or_seed_sales(session)
    
    health_items = evaluate_inventory_health(products, sales_by_sku, service_level=0.95)
    
    total_val = sum(p.current_stock * p.unit_cost for p in products)
    
    # Calculate daily revenue across all SKUs
    daily_rev = 0.0
    for s_df in sales_by_sku.values():
        if len(s_df) > 0:
            daily_rev += float(s_df["revenue"].tail(7).mean())
            
    critical_count = sum(1 for h in health_items if h.status == "CRITICAL")
    reorder_count = sum(1 for h in health_items if h.status == "REORDER NOW")
    healthy_count = sum(1 for h in health_items if h.status == "HEALTHY")
    overstocked_count = sum(1 for h in health_items if h.status == "OVERSTOCKED")
    
    avg_doi = float(pd.Series([h.days_of_inventory for h in health_items]).mean()) if health_items else 0.0
    
    top_critical = [
        {
            "sku": h.sku,
            "name": h.name,
            "stock": h.stock_level,
            "rop": h.reorder_point,
            "status": h.status,
            "risk_score": h.stockout_risk_score,
            "rec_order_qty": h.recommended_reorder_qty,
        }
        for h in health_items if h.status in ["CRITICAL", "REORDER NOW"]
    ][:5]
    
    # Category breakdown
    cat_stats: Dict[str, Dict[str, Any]] = {}
    for p in products:
        cat = p.category
        if cat not in cat_stats:
            cat_stats[cat] = {"category": cat, "skus": 0, "total_stock": 0, "inventory_value": 0.0}
        cat_stats[cat]["skus"] += 1
        cat_stats[cat]["total_stock"] += p.current_stock
        cat_stats[cat]["inventory_value"] += round(p.current_stock * p.unit_cost, 2)
        
    return ExecutiveSummaryResponse(
        total_skus=len(products),
        total_inventory_value=round(total_val, 2),
        total_daily_revenue=round(daily_rev, 2),
        critical_skus_count=critical_count,
        reorder_needed_count=reorder_count,
        healthy_skus_count=healthy_count,
        overstocked_count=overstocked_count,
        average_days_of_inventory=round(avg_doi, 1),
        top_critical_items=top_critical,
        category_breakdown=list(cat_stats.values()),
    )


# ── Catalog & Products ───────────────────────────────────────────────────────

@router.get("/products", response_model=List[ProductSchema])
def list_products(session: Session = Depends(get_session)) -> List[ProductSchema]:
    seed_database_if_empty(session)
    prods = session.exec(select(Product)).all()
    return [
        ProductSchema(
            sku=p.sku,
            name=p.name,
            category=p.category,
            unit_cost=p.unit_cost,
            selling_price=p.selling_price,
            holding_cost_rate=p.holding_cost_rate,
            order_cost=p.order_cost,
            lead_time_days=p.lead_time_days,
            lead_time_std=p.lead_time_std,
            min_order_qty=p.min_order_qty,
            current_stock=p.current_stock,
            on_order=p.on_order,
        )
        for p in prods
    ]


@router.get("/products/{sku}", response_model=ProductSchema)
def get_product(sku: str, session: Session = Depends(get_session)) -> ProductSchema:
    p = session.exec(select(Product).where(Product.sku == sku)).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"Product {sku} not found")
    return ProductSchema(
        sku=p.sku,
        name=p.name,
        category=p.category,
        unit_cost=p.unit_cost,
        selling_price=p.selling_price,
        holding_cost_rate=p.holding_cost_rate,
        order_cost=p.order_cost,
        lead_time_days=p.lead_time_days,
        lead_time_std=p.lead_time_std,
        min_order_qty=p.min_order_qty,
        current_stock=p.current_stock,
        on_order=p.on_order,
    )


# ── Demand Forecasting Studio ────────────────────────────────────────────────

@router.post("/forecast", response_model=ForecastResponse)
def forecast_demand(req: RetailRequest, session: Session = Depends(get_session)) -> ForecastResponse:
    seed_database_if_empty(session)
    sku = req.sku or "SKU-ELEC-01"
    
    product = session.exec(select(Product).where(Product.sku == sku)).first()
    if not product:
        product = session.exec(select(Product)).first()
        if not product:
            reset_and_seed_database(session)
            product = session.exec(select(Product)).first()
        sku = product.sku
        
    sales = session.exec(
        select(DailySale).where(DailySale.sku == sku).order_by(DailySale.date)
    ).all()
    
    if not sales:
        sales_by_sku = get_or_seed_sales(session)
        sales_df = sales_by_sku.get(sku)
    else:
        sales_df = pd.DataFrame([s.model_dump() for s in sales])
        
    if sales_df is None or len(sales_df) == 0:
        raise HTTPException(status_code=404, detail=f"No sales data found for SKU {sku}")
        
    # Trim to historical days window
    if len(sales_df) > req.days:
        sales_df = sales_df.tail(req.days).reset_index(drop=True)
        
    fcast_pts, chosen_metrics, all_metrics, chosen_model_name, drivers = generate_forecast(
        sales_df=sales_df,
        horizon=req.horizon,
        requested_model=req.model_name,
    )
    
    history_pts = [
        HistoryPoint(date=row["date"], sales=round(float(row["units_sold"]), 1))
        for _, row in sales_df.tail(60).iterrows()
    ]
    
    return ForecastResponse(
        sku=product.sku,
        product_name=product.name,
        category=product.category,
        model_used=chosen_model_name,
        horizon=req.horizon,
        metrics=chosen_metrics,
        history=history_pts,
        forecast=fcast_pts,
        models_comparison=all_metrics,
        drivers=drivers,
    )


# ── Inventory Optimization & Health ──────────────────────────────────────────

@router.post("/inventory-health", response_model=List[InventoryHealthItem])
def get_inventory_health(
    req: RetailRequest,
    session: Session = Depends(get_session)
) -> List[InventoryHealthItem]:
    seed_database_if_empty(session)
    products = session.exec(select(Product)).all()
    sales_by_sku = get_or_seed_sales(session)
    
    return evaluate_inventory_health(
        products=products,
        sales_by_sku=sales_by_sku,
        service_level=req.service_level,
    )


@router.post("/eoq", response_model=EOQItem)
def get_sku_eoq(
    req: RetailRequest,
    session: Session = Depends(get_session)
) -> EOQItem:
    seed_database_if_empty(session)
    sku = req.sku or "SKU-ELEC-01"
    product = session.exec(select(Product).where(Product.sku == sku)).first()
    if not product:
        product = session.exec(select(Product)).first()
        if not product:
            raise HTTPException(status_code=404, detail="No products available")
            
    sales_by_sku = get_or_seed_sales(session)
    sales_df = sales_by_sku.get(product.sku)
    if sales_df is not None and len(sales_df) > 0:
        annual_demand = float(sales_df["units_sold"].tail(90).mean() * 365.0)
    else:
        annual_demand = 1000.0
        
    return calculate_eoq(product, annual_demand)


# ── ABC-XYZ Portfolio Classification ─────────────────────────────────────────

@router.post("/abc-xyz", response_model=ABCXYZResponse)
def get_abc_xyz_matrix(session: Session = Depends(get_session)) -> ABCXYZResponse:
    seed_database_if_empty(session)
    products = session.exec(select(Product)).all()
    sales_by_sku = get_or_seed_sales(session)
    return compute_abc_xyz(products, sales_by_sku)


# ── Supply Chain What-If Stress Simulator ────────────────────────────────────

@router.post("/simulate", response_model=SimulationResponse)
def simulate_disruptions(
    req: SimulationRequest,
    session: Session = Depends(get_session)
) -> SimulationResponse:
    seed_database_if_empty(session)
    products = session.exec(select(Product)).all()
    sales_by_sku = get_or_seed_sales(session)
    return run_supply_chain_simulation(products, sales_by_sku, req)


# ── Purchase Order Management ────────────────────────────────────────────────

@router.get("/purchase-orders", response_model=List[PurchaseOrderResponse])
def get_purchase_orders(session: Session = Depends(get_session)) -> List[PurchaseOrderResponse]:
    seed_database_if_empty(session)
    return list_purchase_orders(session)


@router.post("/purchase-orders", response_model=PurchaseOrderResponse)
def create_po(
    order_in: PurchaseOrderCreate,
    session: Session = Depends(get_session)
) -> PurchaseOrderResponse:
    try:
        return create_purchase_order(session, order_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/purchase-orders/{po_id}/status", response_model=PurchaseOrderResponse)
def update_po_status(
    po_id: int,
    status_update: PurchaseOrderUpdate,
    session: Session = Depends(get_session)
) -> PurchaseOrderResponse:
    try:
        return update_purchase_order_status(session, po_id, status_update.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/replenishment-suggestions")
def get_replenishment_suggestions(session: Session = Depends(get_session)) -> List[Dict[str, Any]]:
    seed_database_if_empty(session)
    return generate_replenishment_suggestions(session)


# ── Data Ingestion & Database Operations ─────────────────────────────────────

@router.post("/data/seed")
def seed_catalog(days: int = 365, seed: int = 42, session: Session = Depends(get_session)) -> dict:
    reset_and_seed_database(session, days=days, seed=seed)
    return {"status": "success", "message": f"Database reset and seeded with 16 SKUs and {days} days of history."}


@router.post("/data/upload")
async def upload_sales_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
) -> dict:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV")
    file_bytes = await file.read()
    try:
        res = ingest_sales_csv(session, file_bytes)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to ingest CSV: {str(e)}")


# ── Legacy Compatibility Endpoints ───────────────────────────────────────────

@router.post("/recommendations")
def recommendations(req: RetailRequest, session: Session = Depends(get_session)) -> dict:
    df = generate_sales_data(req.days, req.seed)
    out = forecast_and_reorder(df)
    out["sample"] = df.tail(7).to_dict(orient="records")
    return out


@router.post("/top-products")
def top_products(req: RetailRequest) -> list:
    return get_top_products(req.seed)


@router.post("/inventory-status")
def inventory_status(req: RetailRequest) -> list:
    return get_inventory_status(req.seed)
