import io
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sqlmodel import Session, select, delete

from backend.app.models.record import Product, DailySale, PurchaseOrder, ForecastRun

INITIAL_PRODUCTS: List[Dict[str, Any]] = [
    # Electronics
    {
        "sku": "SKU-ELEC-01",
        "name": "Wireless Noise-Cancelling Headphones Pro",
        "category": "Electronics",
        "unit_cost": 85.0,
        "selling_price": 199.99,
        "holding_cost_rate": 0.22,
        "order_cost": 150.0,
        "lead_time_days": 10,
        "lead_time_std": 2.0,
        "min_order_qty": 25,
        "current_stock": 42,
        "on_order": 50,
        "base_demand": 24.0,
    },
    {
        "sku": "SKU-ELEC-02",
        "name": "Ultra HD 4K Smart TV 55-inch",
        "category": "Electronics",
        "unit_cost": 260.0,
        "selling_price": 549.99,
        "holding_cost_rate": 0.25,
        "order_cost": 250.0,
        "lead_time_days": 14,
        "lead_time_std": 3.5,
        "min_order_qty": 10,
        "current_stock": 16,
        "on_order": 0,
        "base_demand": 9.5,
    },
    {
        "sku": "SKU-ELEC-03",
        "name": "Ergonomic Mechanical Keyboard RGB",
        "category": "Electronics",
        "unit_cost": 38.0,
        "selling_price": 89.99,
        "holding_cost_rate": 0.18,
        "order_cost": 100.0,
        "lead_time_days": 7,
        "lead_time_std": 1.2,
        "min_order_qty": 30,
        "current_stock": 94,
        "on_order": 0,
        "base_demand": 32.0,
    },
    {
        "sku": "SKU-ELEC-04",
        "name": "Smart Health & Fitness Tracker Watch",
        "category": "Electronics",
        "unit_cost": 45.0,
        "selling_price": 129.99,
        "holding_cost_rate": 0.20,
        "order_cost": 120.0,
        "lead_time_days": 9,
        "lead_time_std": 1.8,
        "min_order_qty": 20,
        "current_stock": 20,
        "on_order": 30,
        "base_demand": 28.0,
    },
    # Apparel
    {
        "sku": "SKU-APPR-01",
        "name": "Classic Vintage Denim Trucker Jacket",
        "category": "Apparel",
        "unit_cost": 32.0,
        "selling_price": 79.99,
        "holding_cost_rate": 0.20,
        "order_cost": 110.0,
        "lead_time_days": 12,
        "lead_time_std": 2.5,
        "min_order_qty": 40,
        "current_stock": 30,
        "on_order": 0,
        "base_demand": 18.0,
    },
    {
        "sku": "SKU-APPR-02",
        "name": "Organic Heavyweight Cotton Hoodie",
        "category": "Apparel",
        "unit_cost": 22.0,
        "selling_price": 59.99,
        "holding_cost_rate": 0.18,
        "order_cost": 90.0,
        "lead_time_days": 8,
        "lead_time_std": 1.5,
        "min_order_qty": 50,
        "current_stock": 165,
        "on_order": 0,
        "base_demand": 45.0,
    },
    {
        "sku": "SKU-APPR-03",
        "name": "High-Performance Breathable Running Shoes",
        "category": "Apparel",
        "unit_cost": 42.0,
        "selling_price": 119.99,
        "holding_cost_rate": 0.22,
        "order_cost": 130.0,
        "lead_time_days": 11,
        "lead_time_std": 2.2,
        "min_order_qty": 35,
        "current_stock": 26,
        "on_order": 40,
        "base_demand": 22.0,
    },
    # Groceries
    {
        "sku": "SKU-GROC-01",
        "name": "Single-Origin Arabica Whole Bean Coffee 1kg",
        "category": "Groceries",
        "unit_cost": 9.5,
        "selling_price": 24.99,
        "holding_cost_rate": 0.25,
        "order_cost": 60.0,
        "lead_time_days": 5,
        "lead_time_std": 0.8,
        "min_order_qty": 60,
        "current_stock": 210,
        "on_order": 0,
        "base_demand": 65.0,
    },
    {
        "sku": "SKU-GROC-02",
        "name": "Cold-Pressed Organic Extra Virgin Olive Oil 750ml",
        "category": "Groceries",
        "unit_cost": 7.8,
        "selling_price": 18.99,
        "holding_cost_rate": 0.20,
        "order_cost": 65.0,
        "lead_time_days": 6,
        "lead_time_std": 1.0,
        "min_order_qty": 48,
        "current_stock": 110,
        "on_order": 0,
        "base_demand": 42.0,
    },
    {
        "sku": "SKU-GROC-03",
        "name": "Artisanal Creamy Almond Butter 500g",
        "category": "Groceries",
        "unit_cost": 5.2,
        "selling_price": 12.99,
        "holding_cost_rate": 0.22,
        "order_cost": 50.0,
        "lead_time_days": 4,
        "lead_time_std": 0.6,
        "min_order_qty": 72,
        "current_stock": 18,
        "on_order": 80,
        "base_demand": 38.0,
    },
    # Home Goods
    {
        "sku": "SKU-HOME-01",
        "name": "Tri-Ply Stainless Steel Cookware 10-Piece Set",
        "category": "Home Goods",
        "unit_cost": 110.0,
        "selling_price": 279.99,
        "holding_cost_rate": 0.22,
        "order_cost": 200.0,
        "lead_time_days": 15,
        "lead_time_std": 3.0,
        "min_order_qty": 12,
        "current_stock": 12,
        "on_order": 0,
        "base_demand": 8.0,
    },
    {
        "sku": "SKU-HOME-02",
        "name": "Precision Ceramic Electric Gooseneck Kettle",
        "category": "Home Goods",
        "unit_cost": 28.0,
        "selling_price": 69.99,
        "holding_cost_rate": 0.18,
        "order_cost": 95.0,
        "lead_time_days": 7,
        "lead_time_std": 1.1,
        "min_order_qty": 25,
        "current_stock": 65,
        "on_order": 0,
        "base_demand": 26.0,
    },
    {
        "sku": "SKU-HOME-03",
        "name": "Organic Cooling Bamboo Luxury Sheet Set",
        "category": "Home Goods",
        "unit_cost": 36.0,
        "selling_price": 94.99,
        "holding_cost_rate": 0.20,
        "order_cost": 105.0,
        "lead_time_days": 10,
        "lead_time_std": 2.0,
        "min_order_qty": 20,
        "current_stock": 18,
        "on_order": 25,
        "base_demand": 16.0,
    },
    # Beauty
    {
        "sku": "SKU-BEAU-01",
        "name": "Multi-Molecular Hyaluronic Acid Serum 50ml",
        "category": "Beauty",
        "unit_cost": 12.0,
        "selling_price": 34.99,
        "holding_cost_rate": 0.20,
        "order_cost": 75.0,
        "lead_time_days": 6,
        "lead_time_std": 1.0,
        "min_order_qty": 50,
        "current_stock": 130,
        "on_order": 0,
        "base_demand": 50.0,
    },
    {
        "sku": "SKU-BEAU-02",
        "name": "Botanical Gentle Foaming Face Cleanser 200ml",
        "category": "Beauty",
        "unit_cost": 8.5,
        "selling_price": 22.99,
        "holding_cost_rate": 0.18,
        "order_cost": 65.0,
        "lead_time_days": 5,
        "lead_time_std": 0.9,
        "min_order_qty": 60,
        "current_stock": 96,
        "on_order": 0,
        "base_demand": 40.0,
    },
    {
        "sku": "SKU-BEAU-03",
        "name": "Broad Spectrum Invisible Mineral Sunscreen SPF 50",
        "category": "Beauty",
        "unit_cost": 11.5,
        "selling_price": 29.99,
        "holding_cost_rate": 0.20,
        "order_cost": 80.0,
        "lead_time_days": 7,
        "lead_time_std": 1.2,
        "min_order_qty": 45,
        "current_stock": 22,
        "on_order": 45,
        "base_demand": 34.0,
    },
]


def generate_sku_timeseries(
    product_dict: Dict[str, Any],
    days: int = 365,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate realistic retail time-series for a single SKU:
    - Base demand + subtle upward growth trend
    - Weekly cyclicality (weekend shopping boost)
    - Monthly/seasonal sine wave
    - Random promotional campaigns
    - Realistic variance & stock trajectory
    """
    rng = np.random.default_rng(seed + abs(hash(product_dict["sku"])) % 10000)
    end_date = pd.Timestamp.today().normalize()
    dates = pd.date_range(end=end_date, periods=days, freq="D")
    
    base = product_dict.get("base_demand", 25.0)
    trend = np.linspace(0, base * 0.15, days)  # 15% growth over the period
    
    # Weekly seasonality: Saturday & Sunday higher demand
    day_of_week = dates.dayofweek
    weekly_factors = np.array([0.92, 0.95, 0.97, 1.02, 1.15, 1.32, 1.25])
    weekly_multiplier = weekly_factors[day_of_week]
    
    # Annual/quarterly seasonality (60-day cycle)
    seasonal_cycle = 1.0 + 0.12 * np.sin(np.linspace(0, (days / 60) * 2 * np.pi, days))
    
    # Random promotional lift: roughly 2-3 promo days per month
    promo_prob = 0.08
    is_promo = rng.random(days) < promo_prob
    promo_multiplier = np.where(is_promo, rng.uniform(1.35, 1.70, days), 1.0)
    
    # Composite expected demand
    expected_sales = (base + trend) * weekly_multiplier * seasonal_cycle * promo_multiplier
    
    # Add Gaussian noise
    noise_std = max(2.0, base * 0.12)
    sales = np.maximum(1.0, rng.normal(expected_sales, noise_std)).round(1)
    
    # Simulated stock trajectory
    stock = np.zeros(days)
    curr_s = product_dict.get("current_stock", 100)
    reorder_trigger = base * product_dict.get("lead_time_days", 7)
    
    # Backward simulate stock levels for realistic records
    for i in range(days - 1, -1, -1):
        stock[i] = curr_s
        # Simulate inventory depletion backwards
        curr_s = curr_s + sales[i]
        if curr_s > reorder_trigger * 2.5:
            curr_s = curr_s * 0.45  # simulate arrival of past batch
            
    selling_price = product_dict.get("selling_price", 49.99)
    revenue = (sales * selling_price).round(2)
    
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "sku": product_dict["sku"],
        "units_sold": sales,
        "revenue": revenue,
        "stock_level": np.maximum(0, stock).round(1),
        "is_promo": is_promo,
    })
    return df


def seed_database_if_empty(session: Session, days: int = 365, seed: int = 42) -> None:
    """Populate database with initial catalog and history if currently empty."""
    existing_count = len(session.exec(select(Product)).all())
    if existing_count > 0:
        return
    
    reset_and_seed_database(session, days=days, seed=seed)


def reset_and_seed_database(session: Session, days: int = 365, seed: int = 42) -> None:
    """Clear all records and reseed clean rich synthetic retail catalog."""
    # Delete existing records
    session.exec(delete(DailySale))
    session.exec(delete(PurchaseOrder))
    session.exec(delete(ForecastRun))
    session.exec(delete(Product))
    session.commit()
    
    # Create products
    for p_data in INITIAL_PRODUCTS:
        prod = Product(
            sku=p_data["sku"],
            name=p_data["name"],
            category=p_data["category"],
            unit_cost=p_data["unit_cost"],
            selling_price=p_data["selling_price"],
            holding_cost_rate=p_data["holding_cost_rate"],
            order_cost=p_data["order_cost"],
            lead_time_days=p_data["lead_time_days"],
            lead_time_std=p_data["lead_time_std"],
            min_order_qty=p_data["min_order_qty"],
            current_stock=p_data["current_stock"],
            on_order=p_data["on_order"],
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
        )
        session.add(prod)
        
        # Generate time series
        ts_df = generate_sku_timeseries(p_data, days=days, seed=seed)
        for _, row in ts_df.iterrows():
            sale = DailySale(
                date=row["date"],
                sku=row["sku"],
                units_sold=float(row["units_sold"]),
                revenue=float(row["revenue"]),
                stock_level=float(row["stock_level"]),
                is_promo=bool(row["is_promo"]),
            )
            session.add(sale)
            
    # Add initial seed Purchase Orders for operational demonstration
    sample_pos = [
        PurchaseOrder(
            po_number="PO-2026-001",
            sku="SKU-ELEC-01",
            order_qty=50,
            unit_cost=85.0,
            total_cost=4250.0,
            status="ORDERED",
            priority="CRITICAL",
            created_at=(datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%d"),
            expected_delivery=(datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
        ),
        PurchaseOrder(
            po_number="PO-2026-002",
            sku="SKU-GROC-03",
            order_qty=80,
            unit_cost=5.2,
            total_cost=416.0,
            status="ORDERED",
            priority="HIGH",
            created_at=(datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d"),
            expected_delivery=(datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d"),
        ),
        PurchaseOrder(
            po_number="PO-2026-003",
            sku="SKU-HOME-03",
            order_qty=25,
            unit_cost=36.0,
            total_cost=900.0,
            status="APPROVED",
            priority="MEDIUM",
            created_at=(datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d"),
            expected_delivery=(datetime.now(timezone.utc) + timedelta(days=9)).strftime("%Y-%m-%d"),
        ),
    ]
    for po in sample_pos:
        session.add(po)
        
    session.commit()


def ingest_sales_csv(session: Session, file_bytes: bytes) -> Dict[str, Any]:
    """Ingest external CSV dataset into SQLite database."""
    content = file_bytes.decode("utf-8")
    df = pd.read_csv(io.StringIO(content))
    
    # Required columns check: date, sku, units_sold
    required_cols = {"date", "sku", "units_sold"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV must contain columns: {required_cols}. Found: {list(df.columns)}")
        
    # Standardize types
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce").fillna(0.0)
    
    # Auto-fill missing fields if not provided
    if "revenue" not in df.columns:
        df["revenue"] = df["units_sold"] * 25.0
    if "stock_level" not in df.columns:
        df["stock_level"] = 100.0
    if "is_promo" not in df.columns:
        df["is_promo"] = False
        
    inserted_sales = 0
    skus_found = df["sku"].unique()
    
    # Auto-create products if they don't exist
    for sku in skus_found:
        existing = session.exec(select(Product).where(Product.sku == sku)).first()
        if not existing:
            new_prod = Product(
                sku=str(sku),
                name=f"Product {sku}",
                category="General",
                unit_cost=15.0,
                selling_price=30.0,
                holding_cost_rate=0.20,
                order_cost=100.0,
                lead_time_days=7,
                lead_time_std=1.5,
                min_order_qty=20,
                current_stock=100,
                on_order=0,
                created_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
            )
            session.add(new_prod)
            
    for _, row in df.iterrows():
        sale = DailySale(
            date=row["date"],
            sku=str(row["sku"]),
            units_sold=float(row["units_sold"]),
            revenue=float(row["revenue"]),
            stock_level=float(row["stock_level"]),
            is_promo=bool(row["is_promo"]),
        )
        session.add(sale)
        inserted_sales += 1
        
    session.commit()
    return {
        "status": "success",
        "rows_inserted": inserted_sales,
        "unique_skus": len(skus_found),
        "date_range": [df["date"].min(), df["date"].max()],
    }
