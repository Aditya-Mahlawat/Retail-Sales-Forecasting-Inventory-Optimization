from typing import List, Dict, Any
import numpy as np
import pandas as pd
from scipy.stats import norm

from backend.app.schemas.record import SimulationRequest, SimulationResponse
from backend.app.models.record import Product
from backend.app.services.inventory import calculate_safety_stock_and_rop, calculate_eoq


def run_supply_chain_simulation(
    products: List[Product],
    sales_by_sku: Dict[str, pd.DataFrame],
    req: SimulationRequest,
) -> SimulationResponse:
    """
    Stress-test the retail supply chain against:
    - Supplier lead-time disruptions (delays)
    - Macro demand shifts (surges or plunges)
    - Holding cost / interest rate shifts
    - Service level policy target changes
    """
    baseline_ss_val = 0.0
    simulated_ss_val = 0.0
    baseline_total_cost = 0.0
    simulated_total_cost = 0.0
    stockouts_baseline = 0
    stockouts_simulated = 0
    sku_impacts = []
    
    demand_multiplier = 1.0 + (req.demand_shock_pct / 100.0)
    
    for p in products:
        sales_df = sales_by_sku.get(p.sku)
        if sales_df is not None and len(sales_df) > 0:
            d_mean_base = float(sales_df["units_sold"].tail(60).mean())
            d_std_base = float(sales_df["units_sold"].tail(60).std())
        else:
            d_mean_base = 25.0
            d_std_base = 6.0
            
        # Baseline calculations
        ss_base, rop_base = calculate_safety_stock_and_rop(
            daily_demand_mean=d_mean_base,
            daily_demand_std=d_std_base,
            lead_time_days=float(p.lead_time_days),
            lead_time_std=float(p.lead_time_std),
            service_level=0.95,
        )
        eoq_base = calculate_eoq(p, d_mean_base * 365.0)
        
        # Simulated parameters
        d_mean_sim = max(0.5, d_mean_base * demand_multiplier)
        d_std_sim = max(0.2, d_std_base * np.sqrt(max(0.1, demand_multiplier)))
        lt_sim = max(1.0, float(p.lead_time_days + req.lead_time_shock_days))
        lt_std_sim = max(0.1, float(p.lead_time_std * (1.0 + max(0, req.lead_time_shock_days) * 0.1)))
        
        # Temp product with shocked holding cost
        p_sim = Product(**p.dict())
        p_sim.holding_cost_rate = max(0.05, p.holding_cost_rate + req.holding_cost_rate_shock)
        
        ss_sim, rop_sim = calculate_safety_stock_and_rop(
            daily_demand_mean=d_mean_sim,
            daily_demand_std=d_std_sim,
            lead_time_days=lt_sim,
            lead_time_std=lt_std_sim,
            service_level=req.service_level_target,
        )
        eoq_sim = calculate_eoq(p_sim, d_mean_sim * 365.0)
        
        # Working capital and costs
        base_ss_cost = ss_base * p.unit_cost
        sim_ss_cost = ss_sim * p.unit_cost
        baseline_ss_val += base_ss_cost
        simulated_ss_val += sim_ss_cost
        
        baseline_total_cost += eoq_base.total_inventory_cost
        simulated_total_cost += eoq_sim.total_inventory_cost
        
        net_stock = p.current_stock + p.on_order
        if net_stock < rop_base:
            stockouts_baseline += 1
        if net_stock < rop_sim:
            stockouts_simulated += 1
            
        sku_impacts.append({
            "sku": p.sku,
            "name": p.name,
            "category": p.category,
            "unit_cost": p.unit_cost,
            "current_stock": p.current_stock,
            "baseline_ss": ss_base,
            "simulated_ss": ss_sim,
            "ss_delta": ss_sim - ss_base,
            "baseline_rop": rop_base,
            "simulated_rop": rop_sim,
            "rop_delta": rop_sim - rop_base,
            "working_cap_delta": round(sim_ss_cost - base_ss_cost, 2),
            "simulated_risk": "HIGH" if net_stock < ss_sim else ("MEDIUM" if net_stock < rop_sim else "LOW"),
        })
        
    ss_delta = round(simulated_ss_val - baseline_ss_val, 2)
    cost_delta = round(simulated_total_cost - baseline_total_cost, 2)
    
    # Executive summary narrative
    lead_text = f"+{req.lead_time_shock_days}d supplier delay" if req.lead_time_shock_days > 0 else (
        f"{req.lead_time_shock_days}d lead time" if req.lead_time_shock_days < 0 else "nominal lead times"
    )
    demand_text = f"{req.demand_shock_pct:+.1f}% demand shift"
    summary = (
        f"Under scenario ({lead_text}, {demand_text}, target CSL {req.service_level_target*100:.1f}%), "
        f"working capital tied to safety stock shifts by ${ss_delta:,.2f} "
        f"({(ss_delta / max(1.0, baseline_ss_val)) * 100:+.1f}%). "
        f"Expected stockout exposure changes from {stockouts_baseline} to {stockouts_simulated} SKUs."
    )
    
    return SimulationResponse(
        baseline_safety_stock_val=round(baseline_ss_val, 2),
        simulated_safety_stock_val=round(simulated_ss_val, 2),
        safety_stock_val_delta=ss_delta,
        baseline_total_cost=round(baseline_total_cost, 2),
        simulated_total_cost=round(simulated_total_cost, 2),
        total_cost_delta=cost_delta,
        expected_stockouts_baseline=stockouts_baseline,
        expected_stockouts_simulated=stockouts_simulated,
        impact_summary=summary,
        sku_impacts=sku_impacts,
    )
