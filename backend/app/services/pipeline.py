import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

PRODUCTS = ["SKU-Alpha", "SKU-Beta", "SKU-Gamma", "SKU-Delta", "SKU-Epsilon",
            "SKU-Zeta", "SKU-Theta", "SKU-Lambda"]
CATEGORIES = ["Electronics", "Apparel", "Groceries", "Hardware", "Cosmetics"]


def generate_sales_data(days: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days, freq="D")
    seasonal = 20 * np.sin(np.linspace(0, 6.28, days))
    sales = 120 + seasonal + rng.normal(0, 10, days)
    stock = 180 + rng.normal(0, 12, days)
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "sales": sales.clip(20).round(2),
        "stock": stock.clip(30).round(2),
    })
    return df


def forecast_and_reorder(df: pd.DataFrame, lead_time_days: int = 7, service_factor: float = 1.65) -> dict:
    recent = df.tail(30)
    avg_demand = recent["sales"].mean()
    std_demand = recent["sales"].std()
    safety_stock = service_factor * std_demand * (lead_time_days ** 0.5)
    reorder_point = avg_demand * lead_time_days + safety_stock
    latest_stock = float(df["stock"].iloc[-1])
    recommendation = "REORDER" if latest_stock < reorder_point else "SUFFICIENT"
    return {
        "avg_daily_demand": round(float(avg_demand), 2),
        "safety_stock": round(float(safety_stock), 2),
        "reorder_point": round(float(reorder_point), 2),
        "latest_stock": round(latest_stock, 2),
        "recommendation": recommendation,
    }


def get_demand_forecast(df: pd.DataFrame, horizon: int = 30) -> dict:
    """Generate next N-day demand forecast using linear regression."""
    X = np.arange(len(df)).reshape(-1, 1)
    y = df["sales"].values
    model = LinearRegression().fit(X, y)
    future_X = np.arange(len(df), len(df) + horizon).reshape(-1, 1)
    preds = model.predict(future_X).clip(10)
    residual_std = float(np.std(y - model.predict(X)))
    future_dates = pd.date_range(
        start=pd.Timestamp.today() + pd.Timedelta(days=1), periods=horizon, freq="D"
    )
    history = [{"date": d, "sales": round(float(s), 2)} for d, s in zip(df["date"].tail(30), df["sales"].tail(30))]
    forecast = [
        {
            "date": d.strftime("%Y-%m-%d"),
            "forecast": round(float(p), 2),
            "lower": round(float(p - 1.96 * residual_std), 2),
            "upper": round(float(p + 1.96 * residual_std), 2),
        }
        for d, p in zip(future_dates, preds)
    ]
    return {
        "history": history,
        "forecast": forecast,
        "trend_slope": round(float(model.coef_[0]), 4),
        "r2_score": round(float(model.score(X, y)), 4),
    }


def get_top_products(seed: int, n_skus: int = 8) -> list:
    """Simulate top-N product sales ranking."""
    rng = np.random.default_rng(seed)
    skus = PRODUCTS[:n_skus]
    revenue = rng.integers(50000, 300000, n_skus)
    units = rng.integers(400, 3000, n_skus)
    margin = rng.uniform(0.12, 0.45, n_skus).round(3)
    idx = np.argsort(revenue)[::-1]
    return [
        {
            "sku": skus[i],
            "revenue": int(revenue[i]),
            "units_sold": int(units[i]),
            "margin_pct": round(float(margin[i]) * 100, 1),
            "rank": rank + 1,
        }
        for rank, i in enumerate(idx)
    ]


def get_inventory_status(seed: int, n_skus: int = 8) -> list:
    """Simulate per-SKU inventory health."""
    rng = np.random.default_rng(seed + 100)
    skus = PRODUCTS[:n_skus]
    stock_levels = rng.integers(10, 500, n_skus)
    reorder_pts = rng.integers(80, 200, n_skus)
    statuses = []
    for i, sku in enumerate(skus):
        sl = int(stock_levels[i])
        rp = int(reorder_pts[i])
        pct = round(sl / (rp * 2) * 100, 1)
        status = "CRITICAL" if sl < rp * 0.5 else ("LOW" if sl < rp else "OK")
        statuses.append({
            "sku": sku,
            "stock_level": sl,
            "reorder_point": rp,
            "stock_pct": pct,
            "status": status,
        })
    return sorted(statuses, key=lambda x: x["stock_level"])
