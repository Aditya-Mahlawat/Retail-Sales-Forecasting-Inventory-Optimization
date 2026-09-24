from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RetailRequest(BaseModel):
    days: int = Field(default=180, ge=30, le=730, description="Historical lookback window in days")
    seed: int = Field(default=42, description="Random seed for simulation")
    sku: Optional[str] = Field(default="SKU-ELEC-01", description="Specific SKU to analyze (or all)")
    horizon: int = Field(default=30, ge=7, le=90, description="Forecast horizon in days")
    model_name: str = Field(default="auto", description="Forecasting model: auto, gbm, ridge, holt_winters, seasonal_naive")
    service_level: float = Field(default=0.95, ge=0.80, le=0.999, description="Target cycle service level")
    lead_time_override: Optional[int] = Field(default=None, description="Lead time days override")

class ProductSchema(BaseModel):
    sku: str
    name: str
    category: str
    unit_cost: float
    selling_price: float
    holding_cost_rate: float
    order_cost: float
    lead_time_days: int
    lead_time_std: float
    min_order_qty: int
    current_stock: int
    on_order: int

class ForecastPoint(BaseModel):
    date: str
    forecast: float
    lower_80: float
    upper_80: float
    lower_95: float
    upper_95: float

class HistoryPoint(BaseModel):
    date: str
    sales: float

class ModelMetrics(BaseModel):
    model_name: str
    mae: float
    rmse: float
    mape: float
    wape: float
    r2_score: float
    tracking_signal: float

class ForecastResponse(BaseModel):
    sku: str
    product_name: str
    category: str
    model_used: str
    horizon: int
    metrics: ModelMetrics
    history: List[HistoryPoint]
    forecast: List[ForecastPoint]
    models_comparison: List[ModelMetrics]
    drivers: Optional[List[Dict[str, Any]]] = None

class ABCXYZItem(BaseModel):
    sku: str
    name: str
    category: str
    annual_revenue: float
    revenue_share: float
    cum_share: float
    abc_class: str
    demand_cv: float
    xyz_class: str
    matrix_code: str  # e.g., "AX", "BY", "CZ"
    recommended_strategy: str

class ABCXYZResponse(BaseModel):
    items: List[ABCXYZItem]
    matrix_summary: Dict[str, int]
    total_revenue: float

class InventoryHealthItem(BaseModel):
    sku: str
    name: str
    category: str
    stock_level: int
    on_order: int
    daily_demand_mean: float
    daily_demand_std: float
    lead_time_days: int
    lead_time_std: float
    safety_stock: int
    reorder_point: int
    max_stock: int
    stock_pct: float
    days_of_inventory: float
    status: str  # CRITICAL, REORDER NOW, HEALTHY, OVERSTOCKED
    stockout_risk_score: float
    recommended_reorder_qty: int
    estimated_reorder_cost: float

class EOQItem(BaseModel):
    sku: str
    name: str
    annual_demand: float
    order_setup_cost: float
    unit_cost: float
    holding_cost_per_unit_year: float
    eoq: int
    orders_per_year: float
    cycle_time_days: float
    annual_ordering_cost: float
    annual_holding_cost: float
    total_inventory_cost: float
    cost_curve: List[Dict[str, float]]

class SimulationRequest(BaseModel):
    days: int = 180
    seed: int = 42
    lead_time_shock_days: int = Field(default=0, ge=-5, le=30, description="Lead time delay delta in days")
    demand_shock_pct: float = Field(default=0.0, ge=-50.0, le=100.0, description="Demand shift percentage (+/- %)")
    holding_cost_rate_shock: float = Field(default=0.0, ge=-0.10, le=0.30, description="Holding rate delta (e.g. +0.05)")
    service_level_target: float = Field(default=0.95, ge=0.80, le=0.999)

class SimulationResponse(BaseModel):
    baseline_safety_stock_val: float
    simulated_safety_stock_val: float
    safety_stock_val_delta: float
    baseline_total_cost: float
    simulated_total_cost: float
    total_cost_delta: float
    expected_stockouts_baseline: int
    expected_stockouts_simulated: int
    impact_summary: str
    sku_impacts: List[Dict[str, Any]]

class PurchaseOrderCreate(BaseModel):
    sku: str
    order_qty: int
    priority: str = "MEDIUM"

class PurchaseOrderUpdate(BaseModel):
    status: str  # DRAFT, APPROVED, ORDERED, RECEIVED

class PurchaseOrderResponse(BaseModel):
    id: Optional[int] = None
    po_number: str
    sku: str
    product_name: str
    order_qty: int
    unit_cost: float
    total_cost: float
    status: str
    priority: str
    created_at: str
    expected_delivery: str

class ExecutiveSummaryResponse(BaseModel):
    total_skus: int
    total_inventory_value: float
    total_daily_revenue: float
    critical_skus_count: int
    reorder_needed_count: int
    healthy_skus_count: int
    overstocked_count: int
    average_days_of_inventory: float
    top_critical_items: List[Dict[str, Any]]
    category_breakdown: List[Dict[str, Any]]
