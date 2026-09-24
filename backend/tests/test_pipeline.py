import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.app.main import app
from backend.app.core.database import engine, init_db
from backend.app.models.record import Product, DailySale, PurchaseOrder
from backend.app.services.data_generator import (
    reset_and_seed_database, seed_database_if_empty, generate_sku_timeseries, INITIAL_PRODUCTS
)
from backend.app.services.forecasting import (
    compute_metrics, HoltWintersAdditive, build_feature_matrix, run_model_tournament, generate_forecast
)
from backend.app.services.inventory import (
    calculate_safety_stock_and_rop, calculate_eoq, evaluate_inventory_health, compute_abc_xyz
)
from backend.app.services.simulation import run_supply_chain_simulation
from backend.app.schemas.record import SimulationRequest, PurchaseOrderCreate, PurchaseOrderUpdate
from backend.app.services.order_service import (
    create_purchase_order, update_purchase_order_status, list_purchase_orders
)
from backend.app.services.pipeline import generate_sales_data, forecast_and_reorder


client = TestClient(app)


def test_legacy_retail_pipeline():
    """Verify legacy test compatibility."""
    df = generate_sales_data(120, 1)
    out = forecast_and_reorder(df)
    assert df.shape[0] == 120
    assert "reorder_point" in out
    assert "avg_daily_demand" in out
    assert "safety_stock" in out


def test_database_seeding():
    """Verify that catalog and daily sales seed cleanly into SQLite."""
    init_db()
    with Session(engine) as session:
        reset_and_seed_database(session, days=90, seed=42)
        products = session.exec(select(Product)).all()
        assert len(products) == len(INITIAL_PRODUCTS)
        
        sales = session.exec(select(DailySale)).all()
        assert len(sales) == len(INITIAL_PRODUCTS) * 90
        
        pos = session.exec(select(PurchaseOrder)).all()
        assert len(pos) >= 3


def test_forecasting_metrics_and_tournament():
    """Test forecasting algorithms, metrics (WAPE, RMSE, MAE, R2), and tournament."""
    # Generate time series
    p = INITIAL_PRODUCTS[0]
    df = generate_sku_timeseries(p, days=120, seed=42)
    
    # Test feature builder
    df_feat, cols = build_feature_matrix(df)
    assert "lag_1" in cols
    assert "rolling_mean_7" in cols
    assert "dayofweek" in cols
    
    # Test Holt-Winters
    hw = HoltWintersAdditive(season_length=7)
    hw.fit(df["units_sold"].values)
    preds = hw.predict(14)
    assert len(preds) == 14
    assert all(p >= 0 for p in preds)
    
    # Test tournament
    models, metrics, best_name = run_model_tournament(df, test_days=20)
    assert len(metrics) == 4
    for m in metrics:
        assert m.wape >= 0.0
        assert m.rmse >= 0.0
        assert m.mae >= 0.0
        
    # Test full forecast generation
    fcast_pts, chosen_m, all_m, name, drivers = generate_forecast(df, horizon=30, requested_model="auto")
    assert len(fcast_pts) == 30
    assert len(drivers) > 0
    # Check 95% CI bounds enclose forecast point
    for pt in fcast_pts:
        assert pt.lower_95 <= pt.forecast <= pt.upper_95


def test_inventory_stochastic_safety_stock_and_eoq():
    """Test safety stock with joint demand/lead time variance and EOQ formulas."""
    # Safety stock
    ss, rop = calculate_safety_stock_and_rop(
        daily_demand_mean=30.0,
        daily_demand_std=5.0,
        lead_time_days=7.0,
        lead_time_std=1.5,
        service_level=0.95,
    )
    assert ss > 0
    assert rop > ss
    assert rop > (30.0 * 7.0) # ROP must exceed expected lead-time demand
    
    # Higher service level must require higher safety stock
    ss_99, _ = calculate_safety_stock_and_rop(
        daily_demand_mean=30.0,
        daily_demand_std=5.0,
        lead_time_days=7.0,
        lead_time_std=1.5,
        service_level=0.99,
    )
    assert ss_99 > ss
    
    # EOQ calculation
    p = Product(
        sku="TEST-SKU",
        name="Test Item",
        category="Test",
        unit_cost=50.0,
        selling_price=100.0,
        order_cost=100.0,
        holding_cost_rate=0.20,
        lead_time_days=7,
        lead_time_std=1.0,
        min_order_qty=15,
        current_stock=50,
        on_order=0,
    )
    eoq_item = calculate_eoq(p, annual_demand=3650.0)
    assert eoq_item.eoq >= 15
    assert eoq_item.total_inventory_cost > 0
    assert len(eoq_item.cost_curve) > 0


def test_abc_xyz_portfolio_analysis():
    """Verify 9-box ABC-XYZ classification matrix logic."""
    with Session(engine) as session:
        products = session.exec(select(Product)).all()
        sales_by_sku = {}
        for p in products:
            sales = session.exec(select(DailySale).where(DailySale.sku == p.sku)).all()
            if sales:
                import pandas as pd
                sales_by_sku[p.sku] = pd.DataFrame([s.model_dump() for s in sales])
                
        abc_res = compute_abc_xyz(products, sales_by_sku)
        assert len(abc_res.items) == len(products)
        assert abc_res.total_revenue > 0
        
        # Verify valid matrix codes
        valid_codes = {"AX", "AY", "AZ", "BX", "BY", "BZ", "CX", "CY", "CZ"}
        for it in abc_res.items:
            assert it.matrix_code in valid_codes
            assert it.abc_class in ["A", "B", "C"]
            assert it.xyz_class in ["X", "Y", "Z"]


def test_supply_chain_stress_simulation():
    """Verify what-if simulation response with lead time and demand shocks."""
    with Session(engine) as session:
        products = session.exec(select(Product)).all()
        sales_by_sku = {}
        for p in products:
            sales = session.exec(select(DailySale).where(DailySale.sku == p.sku)).all()
            if sales:
                import pandas as pd
                sales_by_sku[p.sku] = pd.DataFrame([s.model_dump() for s in sales])
                
        sim_req = SimulationRequest(
            lead_time_shock_days=5,
            demand_shock_pct=25.0,
            holding_cost_rate_shock=0.05,
            service_level_target=0.98,
        )
        sim_res = run_supply_chain_simulation(products, sales_by_sku, sim_req)
        assert sim_res.simulated_safety_stock_val > sim_res.baseline_safety_stock_val
        assert sim_res.safety_stock_val_delta > 0
        assert len(sim_res.sku_impacts) == len(products)
        assert len(sim_res.impact_summary) > 20


def test_purchase_order_lifecycle():
    """Test PO creation, status transition, and inventory increment on RECEIVED."""
    with Session(engine) as session:
        p = session.exec(select(Product)).first()
        initial_stock = p.current_stock
        initial_on_order = p.on_order
        
        # Create PO
        po = create_purchase_order(
            session,
            PurchaseOrderCreate(sku=p.sku, order_qty=40, priority="HIGH"),
        )
        assert po.status == "DRAFT"
        assert po.order_qty == 40
        
        # Verify product on_order updated
        session.refresh(p)
        assert p.on_order == initial_on_order + 40
        
        # Advance to RECEIVED
        updated_po = update_purchase_order_status(session, po.id, "RECEIVED")
        assert updated_po.status == "RECEIVED"
        
        # Verify product current_stock incremented and on_order restored
        session.refresh(p)
        assert p.current_stock == initial_stock + 40
        assert p.on_order == initial_on_order


def test_api_endpoints():
    """Test core FastAPI endpoints."""
    # Health
    r = client.get("/api/v1/retail/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    
    # Executive Summary
    r = client.get("/api/v1/retail/executive-summary")
    assert r.status_code == 200
    body = r.json()
    assert "total_skus" in body
    assert "total_inventory_value" in body
    assert "category_breakdown" in body
    
    # Products
    r = client.get("/api/v1/retail/products")
    assert r.status_code == 200
    assert len(r.json()) > 0
    first_sku = r.json()[0]["sku"]
    
    # Demand Forecast
    r = client.post("/api/v1/retail/forecast", json={"sku": first_sku, "horizon": 14, "model_name": "auto"})
    assert r.status_code == 200
    f_body = r.json()
    assert f_body["sku"] == first_sku
    assert len(f_body["forecast"]) == 14
    assert len(f_body["models_comparison"]) == 4
    
    # Inventory Health
    r = client.post("/api/v1/retail/inventory-health", json={"service_level": 0.95})
    assert r.status_code == 200
    assert len(r.json()) > 0
    
    # EOQ
    r = client.post("/api/v1/retail/eoq", json={"sku": first_sku})
    assert r.status_code == 200
    assert "cost_curve" in r.json()
    
    # ABC-XYZ
    r = client.post("/api/v1/retail/abc-xyz", json={})
    assert r.status_code == 200
    assert "matrix_summary" in r.json()
    
    # Simulation
    r = client.post("/api/v1/retail/simulate", json={"lead_time_shock_days": 3, "demand_shock_pct": 10.0})
    assert r.status_code == 200
    assert "safety_stock_val_delta" in r.json()
    
    # Purchase Orders
    r = client.get("/api/v1/retail/purchase-orders")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
