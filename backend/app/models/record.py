from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field

def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

class Product(SQLModel, table=True):
    __tablename__ = "products"
    
    sku: str = Field(primary_key=True, index=True)
    name: str
    category: str = Field(index=True)
    unit_cost: float
    selling_price: float
    holding_cost_rate: float = 0.20  # 20% annual holding cost rate
    order_cost: float = 120.0        # Fixed setup/order cost ($)
    lead_time_days: int = 7          # Average supplier lead time
    lead_time_std: float = 1.5       # Supplier lead time std dev (days)
    min_order_qty: int = 10          # Supplier MOQ
    current_stock: int = 100
    on_order: int = 0
    created_at: str = Field(default_factory=utc_now_str)

class DailySale(SQLModel, table=True):
    __tablename__ = "daily_sales"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)
    sku: str = Field(index=True)
    units_sold: float
    revenue: float
    stock_level: float
    is_promo: bool = False

class PurchaseOrder(SQLModel, table=True):
    __tablename__ = "purchase_orders"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    po_number: str = Field(index=True, unique=True)
    sku: str = Field(index=True)
    order_qty: int
    unit_cost: float
    total_cost: float
    status: str = Field(default="DRAFT")  # DRAFT, APPROVED, ORDERED, RECEIVED
    priority: str = Field(default="MEDIUM") # CRITICAL, HIGH, MEDIUM, LOW
    created_at: str
    expected_delivery: str

class ForecastRun(SQLModel, table=True):
    __tablename__ = "forecast_runs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    sku: str = Field(index=True)
    model_name: str
    run_date: str
    horizon: int
    wape: float
    rmse: float
    mae: float
    r2_score: float
