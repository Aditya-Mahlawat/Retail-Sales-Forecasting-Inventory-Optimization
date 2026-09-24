from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.stats import norm

from backend.app.schemas.record import (
    InventoryHealthItem, EOQItem, ABCXYZItem, ABCXYZResponse
)
from backend.app.models.record import Product


SERVICE_LEVEL_Z = {
    0.80: 0.8416,
    0.85: 1.0364,
    0.90: 1.2816,
    0.95: 1.6449,
    0.98: 2.0537,
    0.99: 2.3263,
    0.999: 3.0902,
}


def get_z_factor(service_level: float) -> float:
    """Return standard normal quantile for service level."""
    # Snap to nearest or compute directly
    try:
        return float(norm.ppf(service_level))
    except Exception:
        return 1.6449


def calculate_safety_stock_and_rop(
    daily_demand_mean: float,
    daily_demand_std: float,
    lead_time_days: float,
    lead_time_std: float,
    service_level: float = 0.95,
) -> Tuple[int, int]:
    """
    Stochastic Safety Stock incorporating BOTH demand uncertainty and lead-time uncertainty:
    SS = Z * sqrt( L * sigma_d^2 + d^2 * sigma_LT^2 )
    ROP = (d * L) + SS
    """
    z = get_z_factor(service_level)
    d = max(0.1, daily_demand_mean)
    sigma_d = max(0.1, daily_demand_std)
    L = max(1.0, lead_time_days)
    sigma_lt = max(0.0, lead_time_std)
    
    lead_time_demand_variance = (L * (sigma_d ** 2)) + ((d ** 2) * (sigma_lt ** 2))
    lead_time_demand_std = np.sqrt(max(0.1, lead_time_demand_variance))
    
    safety_stock = int(np.ceil(z * lead_time_demand_std))
    reorder_point = int(np.ceil((d * L) + safety_stock))
    
    return safety_stock, reorder_point


def calculate_eoq(
    product: Product,
    annual_demand: float,
) -> EOQItem:
    """
    Calculate Economic Order Quantity (EOQ) and total cost trade-off curve:
    EOQ = sqrt( (2 * D * S) / H )
    """
    D = max(10.0, annual_demand)
    S = max(10.0, product.order_cost)
    h_rate = max(0.05, product.holding_cost_rate)
    H = max(0.5, h_rate * product.unit_cost)
    
    raw_eoq = np.sqrt((2.0 * D * S) / H)
    moq = getattr(product, "min_order_qty", 10)
    eoq = int(max(moq, round(raw_eoq)))
    
    orders_per_year = round(D / eoq, 1)
    cycle_time_days = round(365.0 / max(0.1, orders_per_year), 1)
    annual_ordering_cost = round((D / eoq) * S, 2)
    annual_holding_cost = round((eoq / 2.0) * H, 2)
    total_cost = round(annual_ordering_cost + annual_holding_cost, 2)
    
    # Generate cost curve points
    q_min = max(5, int(eoq * 0.25))
    q_max = int(eoq * 2.5)
    quantities = np.linspace(q_min, q_max, 25, dtype=int)
    
    cost_curve = []
    for q in quantities:
        if q <= 0:
            continue
        c_ord = (D / q) * S
        c_hold = (q / 2.0) * H
        cost_curve.append({
            "order_qty": int(q),
            "ordering_cost": round(float(c_ord), 2),
            "holding_cost": round(float(c_hold), 2),
            "total_cost": round(float(c_ord + c_hold), 2),
        })
        
    return EOQItem(
        sku=product.sku,
        name=product.name,
        annual_demand=round(D, 1),
        order_setup_cost=round(S, 2),
        unit_cost=round(product.unit_cost, 2),
        holding_cost_per_unit_year=round(H, 2),
        eoq=eoq,
        orders_per_year=orders_per_year,
        cycle_time_days=cycle_time_days,
        annual_ordering_cost=annual_ordering_cost,
        annual_holding_cost=annual_holding_cost,
        total_inventory_cost=total_cost,
        cost_curve=cost_curve,
    )


def evaluate_inventory_health(
    products: List[Product],
    sales_by_sku: Dict[str, pd.DataFrame],
    service_level: float = 0.95,
) -> List[InventoryHealthItem]:
    """
    Evaluate inventory health, safety stocks, ROPs, stockout risk scores,
    and recommended replenishment quantities for all SKUs.
    """
    health_items = []
    
    for p in products:
        sales_df = sales_by_sku.get(p.sku)
        if sales_df is not None and len(sales_df) > 0:
            d_mean = float(sales_df["units_sold"].tail(60).mean())
            d_std = float(sales_df["units_sold"].tail(60).std())
        else:
            d_mean = 25.0
            d_std = 6.0
            
        ss, rop = calculate_safety_stock_and_rop(
            daily_demand_mean=d_mean,
            daily_demand_std=d_std,
            lead_time_days=float(p.lead_time_days),
            lead_time_std=float(p.lead_time_std),
            service_level=service_level,
        )
        
        stock = p.current_stock
        on_order = p.on_order
        net_stock = stock + on_order
        max_stock = rop + ss
        
        stock_pct = round((stock / max(1, rop)) * 100.0, 1)
        doi = round(stock / max(0.1, d_mean), 1)
        
        # Calculate stockout risk probability over lead time
        L = float(p.lead_time_days)
        sigma_lt = float(p.lead_time_std)
        lt_std = np.sqrt((L * (d_std ** 2)) + ((d_mean ** 2) * (sigma_lt ** 2)))
        lt_demand_expected = d_mean * L
        
        if lt_std > 0:
            z_val = (net_stock - lt_demand_expected) / lt_std
            stockout_risk_score = round(float((1.0 - norm.cdf(z_val)) * 100.0), 1)
        else:
            stockout_risk_score = 90.0 if net_stock < lt_demand_expected else 5.0
            
        # Determine status
        if stock <= ss * 0.5:
            status = "CRITICAL"
        elif net_stock <= rop:
            status = "REORDER NOW"
        elif doi > 65.0:
            status = "OVERSTOCKED"
        else:
            status = "HEALTHY"
            
        # Recommended order quantity
        annual_demand = d_mean * 365.0
        eoq_calc = calculate_eoq(p, annual_demand)
        
        if net_stock <= rop:
            deficit = max(0, rop + ss - net_stock)
            rec_qty = int(max(p.min_order_qty, eoq_calc.eoq, deficit))
        else:
            rec_qty = 0
            
        est_cost = round(rec_qty * p.unit_cost, 2)
        
        health_items.append(
            InventoryHealthItem(
                sku=p.sku,
                name=p.name,
                category=p.category,
                stock_level=stock,
                on_order=on_order,
                daily_demand_mean=round(d_mean, 1),
                daily_demand_std=round(d_std, 1),
                lead_time_days=p.lead_time_days,
                lead_time_std=round(p.lead_time_std, 1),
                safety_stock=ss,
                reorder_point=rop,
                max_stock=max_stock,
                stock_pct=stock_pct,
                days_of_inventory=doi,
                status=status,
                stockout_risk_score=stockout_risk_score,
                recommended_reorder_qty=rec_qty,
                estimated_reorder_cost=est_cost,
            )
        )
        
    # Sort with critical and reorder items first
    order_map = {"CRITICAL": 0, "REORDER NOW": 1, "OVERSTOCKED": 2, "HEALTHY": 3}
    health_items.sort(key=lambda x: (order_map.get(x.status, 4), x.stock_pct))
    return health_items


def compute_abc_xyz(
    products: List[Product],
    sales_by_sku: Dict[str, pd.DataFrame],
) -> ABCXYZResponse:
    """
    Perform 9-box ABC-XYZ portfolio classification:
    - ABC: Cumulative Revenue Pareto (A: 0-80%, B: 80-95%, C: 95-100%)
    - XYZ: Demand CV (X: CV <= 0.40, Y: 0.40 < CV <= 0.75, Z: CV > 0.75)
    """
    STRATEGY_MAP = {
        "AX": "Automated JIT Replenishment — High revenue, low risk. Maintain lean safety buffer and automate continuous replenishment.",
        "AY": "MRP Dynamic Forecasting — High revenue, moderate variation. Dynamic safety stock + weekly supplier capacity review.",
        "AZ": "Vendor Collaborative Buffering — High revenue, erratic demand. High safety buffer, collaborative forecasting, buffer high-margin stock.",
        "BX": "Standard Periodic EOQ — Moderate revenue, steady demand. Automated batch reordering via calculated EOQ.",
        "BY": "Safety Stock Buffering — Moderate revenue, variable demand. Reorder points with moderate safety stock to guard against stockouts.",
        "BZ": "Agile / Consignment Replenishment — Moderate revenue, volatile. Minimize holding, negotiate short lead times with suppliers.",
        "CX": "Bulk Order / Low Priority — Low revenue, stable demand. Large infrequent EOQ batches to minimize ordering admin overhead.",
        "CY": "Consolidated Batch Ordering — Low revenue, fluctuating demand. Combine orders with other SKUs from the same vendor.",
        "CZ": "Make-to-Order or Rationalize — Low revenue, highly sporadic. Consider dropship, strict minimum stock, or SKU rationalization.",
    }
    
    sku_stats = []
    total_rev = 0.0
    
    for p in products:
        sales_df = sales_by_sku.get(p.sku)
        if sales_df is not None and len(sales_df) > 0:
            ann_rev = float(sales_df["revenue"].sum())
            units = sales_df["units_sold"].values
            mean_u = float(np.mean(units))
            std_u = float(np.std(units))
            cv = float(std_u / max(0.1, mean_u))
        else:
            ann_rev = p.unit_cost * 100.0
            cv = 0.5
            
        total_rev += ann_rev
        sku_stats.append({
            "product": p,
            "annual_revenue": ann_rev,
            "demand_cv": round(cv, 2),
        })
        
    # Sort by revenue descending for ABC Pareto
    sku_stats.sort(key=lambda x: x["annual_revenue"], reverse=True)
    
    cum_share = 0.0
    items: List[ABCXYZItem] = []
    matrix_counts = {k: 0 for k in STRATEGY_MAP.keys()}
    
    for i, item in enumerate(sku_stats):
        p = item["product"]
        rev = item["annual_revenue"]
        rev_share = (rev / max(1.0, total_rev)) * 100.0
        cum_share += rev_share
        
        # ABC Classification
        if cum_share <= 80.0 or i == 0:
            abc_class = "A"
        elif cum_share <= 95.0:
            abc_class = "B"
        else:
            abc_class = "C"
            
        # XYZ Classification
        cv = item["demand_cv"]
        if cv <= 0.40:
            xyz_class = "X"
        elif cv <= 0.75:
            xyz_class = "Y"
        else:
            xyz_class = "Z"
            
        matrix_code = f"{abc_class}{xyz_class}"
        matrix_counts[matrix_code] = matrix_counts.get(matrix_code, 0) + 1
        
        strategy = STRATEGY_MAP.get(matrix_code, "Standard Inventory Policy")
        
        items.append(
            ABCXYZItem(
                sku=p.sku,
                name=p.name,
                category=p.category,
                annual_revenue=round(rev, 2),
                revenue_share=round(rev_share, 2),
                cum_share=round(min(100.0, cum_share), 2),
                abc_class=abc_class,
                demand_cv=round(cv, 2),
                xyz_class=xyz_class,
                matrix_code=matrix_code,
                recommended_strategy=strategy,
            )
        )
        
    return ABCXYZResponse(
        items=items,
        matrix_summary=matrix_counts,
        total_revenue=round(total_rev, 2),
    )
