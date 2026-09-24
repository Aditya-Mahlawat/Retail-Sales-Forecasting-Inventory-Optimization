import os
from datetime import datetime
import io
import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from frontend.styles import FORMAL_CSS, PLOT_LAYOUT, AXIS_LAYOUT

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NexStock Enterprise · Retail Intelligence Suite",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(FORMAL_CSS, unsafe_allow_html=True)

# ── State Management ──────────────────────────────────────────────────────────
if "api_url" not in st.session_state:
    st.session_state.api_url = os.getenv("API_BASE_URL", "http://localhost:8001")
if "selected_sku" not in st.session_state:
    st.session_state.selected_sku = "SKU-ELEC-01"
if "service_level" not in st.session_state:
    st.session_state.service_level = 0.95
if "history_days" not in st.session_state:
    st.session_state.history_days = 180

API = st.session_state.api_url

# ── Helper API Functions ──────────────────────────────────────────────────────
@st.cache_data(ttl=15)
def fetch_api(endpoint: str, method: str = "GET", payload: dict = None):
    url = f"{API}/api/v1/retail/{endpoint.lstrip('/')}"
    try:
        if method == "POST":
            r = requests.post(url, json=payload or {}, timeout=25)
        elif method == "PATCH":
            r = requests.patch(url, json=payload or {}, timeout=25)
        else:
            r = requests.get(url, timeout=25)
        if r.status_code == 200:
            return r.json(), None
        return None, f"HTTP {r.status_code}: {r.text}"
    except Exception as e:
        return None, str(e)


# ── Sidebar Controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:1.1rem; font-weight:800; color:#F8FAFC; margin-bottom:2px;">🏢 NexStock Enterprise</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.75rem; color:#64748B; margin-bottom:18px;">Retail Supply Chain Intelligence v2.0</div>', unsafe_allow_html=True)
    
    # System connectivity check
    health_data, health_err = fetch_api("/health")
    if not health_err:
        st.markdown('<div class="corp-pill" style="color:#34D399; border-color:#065F46; background:#064E3B22;">● API ONLINE · DB ACTIVE</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="corp-pill" style="color:#F87171; border-color:#7F1D1D; background:#7F1D1D22;">● API OFFLINE</div>', unsafe_allow_html=True)
        st.caption(f"Error: {health_err}. Make sure backend is running on port 8001.")

    st.markdown('<div class="sidebar-header">Global Policy Controls</div>', unsafe_allow_html=True)
    csl = st.select_slider(
        "Target Cycle Service Level (CSL)",
        options=[0.90, 0.95, 0.98, 0.99, 0.999],
        value=st.session_state.service_level,
        format_func=lambda x: f"{x*100:.1f}% Service Level",
    )
    st.session_state.service_level = csl
    
    lookback = st.slider(
        "Historical Sales Lookback Window",
        min_value=60, max_value=365, value=st.session_state.history_days, step=30,
        help="Number of past days used to fit forecasting models and estimate demand distributions."
    )
    st.session_state.history_days = lookback
    
    st.markdown('<div class="sidebar-header">System Operations</div>', unsafe_allow_html=True)
    if st.button("🔄 Refresh Analytics State", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
        
    if st.button("⚡ Reset & Re-Seed Catalog", use_container_width=True):
        with st.spinner("Re-seeding database catalog..."):
            res, err = fetch_api("/data/seed?days=365&seed=42", method="POST")
            if not err:
                st.cache_data.clear()
                st.success("Catalog reseeded successfully!")
                st.rerun()
            else:
                st.error(f"Failed to seed: {err}")

    st.markdown('<div style="font-size:0.72rem; color:#475569; margin-top:30px;">NexStock IBP Engine · Production Release</div>', unsafe_allow_html=True)


# ── Top Corporate Banner ──────────────────────────────────────────────────────
st.markdown("""
<div class="corp-header">
    <div>
        <div class="corp-title">NexStock Intelligence Suite</div>
        <div class="corp-sub">Multi-Echelon Demand Forecasting · Stochastic Inventory Optimization · Supply Chain Resilience</div>
    </div>
    <div>
        <span class="corp-pill">ENTERPRISE EDITION · 16 SKUs · SQLITE PERSISTENT</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Fetch Common Data ─────────────────────────────────────────────────────────
exec_data, exec_err = fetch_api("/executive-summary")
products_data, prod_err = fetch_api("/products")

if exec_err or prod_err:
    st.error(f"Cannot connect to NexStock API backend ({API}). Please start the backend service:\n`uvicorn backend.app.main:app --port 8001`")
    st.stop()

sku_list = [p["sku"] for p in products_data]
sku_names = {p["sku"]: f"{p['sku']} · {p['name']}" for p in products_data}


# ── Main Corporate Navigation Tabs ───────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🏛️ Executive Overview",
    "📈 Demand Forecasting Studio",
    "📦 Inventory Health & Optimization",
    "📐 EOQ Cost Optimizer",
    "🧩 ABC-XYZ Portfolio Matrix",
    "⚡ Supply Chain Stress Lab",
    "📝 Purchase Order Manager",
    "💾 Data Operations & CSV Hub",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="corp-card">
            <div class="corp-card-label">Total Inventory Valuation</div>
            <div class="corp-card-value">${exec_data['total_inventory_value']:,.2f}</div>
            <div class="corp-card-sub">Working capital tied in {exec_data['total_skus']} SKUs</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="corp-card success">
            <div class="corp-card-label">Daily Revenue Run-Rate</div>
            <div class="corp-card-value">${exec_data['total_daily_revenue']:,.2f}</div>
            <div class="corp-card-sub">Trailing 7-day average sales</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        crit_class = "critical" if exec_data['critical_skus_count'] > 0 else "success"
        st.markdown(f"""
        <div class="corp-card {crit_class}">
            <div class="corp-card-label">Stockout Risk Exposure</div>
            <div class="corp-card-value" style="color:{'#F87171' if exec_data['critical_skus_count'] > 0 else '#34D399'};">{exec_data['critical_skus_count']} SKUs</div>
            <div class="corp-card-sub">{exec_data['reorder_needed_count']} additional items below ROP</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="corp-card">
            <div class="corp-card-label">Mean Days of Inventory (DOI)</div>
            <div class="corp-card-value">{exec_data['average_days_of_inventory']:.1f} Days</div>
            <div class="corp-card-sub">Catalog average forward coverage</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Critical Alert Banner if items need immediate action
    if exec_data["critical_skus_count"] > 0:
        crit_names = ", ".join([f"{item['sku']} ({item['name']})" for item in exec_data["top_critical_items"] if item["status"] == "CRITICAL"])
        st.markdown(f"""
        <div class="alert-container">
            <div style="font-size:1.4rem;">⚠️</div>
            <div>
                <div class="alert-title">Immediate Stockout Warning: {exec_data['critical_skus_count']} SKUs Breached Safety Threshold</div>
                <div class="alert-desc">The following items have stock levels below 50% of their safety buffer: <b>{crit_names}</b>. Replenishment purchase orders are required immediately to prevent stockout losses.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Visual Analytics Row
    row1_c1, row1_c2 = st.columns([3, 2])
    
    with row1_c1:
        st.markdown("##### 📊 Inventory Valuation by Department")
        cat_df = pd.DataFrame(exec_data["category_breakdown"])
        fig_cat = go.Figure()
        fig_cat.add_trace(go.Bar(
            x=cat_df["category"],
            y=cat_df["inventory_value"],
            marker_color="#2563EB",
            text=[f"${v:,.0f}" for v in cat_df["inventory_value"]],
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Valuation: $%{y:,.2f}<extra></extra>",
        ))
        fig_cat.update_layout(height=290, yaxis_title="Valuation ($)", **PLOT_LAYOUT)
        fig_cat.update_xaxes(**AXIS_LAYOUT)
        fig_cat.update_yaxes(**AXIS_LAYOUT)
        st.plotly_chart(fig_cat, use_container_width=True)

    with row1_c2:
        st.markdown("##### 🎯 Catalog Health Breakdown")
        health_labels = ["Critical Risk", "Reorder Required", "Healthy Coverage", "Overstocked"]
        health_values = [
            exec_data["critical_skus_count"],
            exec_data["reorder_needed_count"],
            exec_data["healthy_skus_count"],
            exec_data["overstocked_count"],
        ]
        health_colors = ["#EF4444", "#F59E0B", "#10B981", "#6366F1"]
        fig_donut = go.Figure(data=[go.Pie(
            labels=health_labels,
            values=health_values,
            hole=0.62,
            marker_colors=health_colors,
            textinfo="value+percent",
            hovertemplate="<b>%{label}</b><br>SKUs: %{value} (%{percent})<extra></extra>",
        )])
        fig_donut.update_layout(
            height=290,
            **PLOT_LAYOUT,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    # Actionable Replenishment Preview Table
    st.markdown("##### 🚨 Urgent Replenishment Action Queue")
    if exec_data["top_critical_items"]:
        crit_table_df = pd.DataFrame(exec_data["top_critical_items"])
        crit_table_df.columns = ["SKU", "Product Name", "Current Stock", "Reorder Point", "Status", "Stockout Risk (%)", "Rec. Order Qty"]
        st.dataframe(crit_table_df, use_container_width=True, hide_index=True)
    else:
        st.info("All catalog SKUs currently have sufficient stock coverage above reorder points.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: DEMAND FORECASTING STUDIO
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### 📈 Multi-Model Demand Forecasting Tournament")
    st.caption("Walk-forward backtesting across 4 competitive algorithms with automated model selection and 80%/95% confidence intervals.")

    f_col1, f_col2, f_col3 = st.columns([3, 2, 2])
    with f_col1:
        selected_sku = st.selectbox(
            "Select Product SKU",
            options=sku_list,
            format_func=lambda x: sku_names.get(x, x),
            key="forecast_sku_select",
        )
    with f_col2:
        model_choice = st.selectbox(
            "Forecasting Algorithm",
            options=["auto", "gbm", "ridge", "holt_winters", "seasonal_naive"],
            format_func=lambda x: {
                "auto": "⚡ Auto-Select (Lowest WAPE)",
                "gbm": "Gradient Boosting (HistGBM)",
                "ridge": "Ridge L2 Regression",
                "holt_winters": "Holt-Winters (Exponential)",
                "seasonal_naive": "Seasonal Naive (Benchmark)",
            }[x],
        )
    with f_col3:
        horizon_days = st.slider("Forecast Horizon (Days)", min_value=7, max_value=60, value=30, step=7)

    with st.spinner("Running walk-forward backtest & fitting forecast models..."):
        f_payload = {
            "sku": selected_sku,
            "horizon": horizon_days,
            "model_name": model_choice,
            "days": st.session_state.history_days,
            "service_level": st.session_state.service_level,
        }
        f_resp, f_err = fetch_api("/forecast", method="POST", payload=f_payload)

    if f_err or not f_resp:
        st.error(f"Error fetching demand forecast: {f_err}")
    else:
        hist_df = pd.DataFrame(f_resp["history"])
        fcast_df = pd.DataFrame(f_resp["forecast"])

        # Main Time Series Chart
        fig_ts = go.Figure()
        
        # Historical Sales
        fig_ts.add_trace(go.Scatter(
            x=hist_df["date"],
            y=hist_df["sales"],
            name="Actual Sales (Historical)",
            mode="lines",
            line=dict(color="#3B82F6", width=2),
            hovertemplate="<b>Historical</b><br>Date: %{x}<br>Units: %{y}<extra></extra>",
        ))
        
        # 95% Confidence Band (Upper and Lower)
        fig_ts.add_trace(go.Scatter(
            x=fcast_df["date"],
            y=fcast_df["upper_95"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig_ts.add_trace(go.Scatter(
            x=fcast_df["date"],
            y=fcast_df["lower_95"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(59, 130, 246, 0.08)",
            name="95% Confidence Band",
            hovertemplate="95% CI: [%{y:.1f} - %{text:.1f}]<extra></extra>",
            text=fcast_df["upper_95"],
        ))
        
        # 80% Confidence Band
        fig_ts.add_trace(go.Scatter(
            x=fcast_df["date"],
            y=fcast_df["upper_80"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig_ts.add_trace(go.Scatter(
            x=fcast_df["date"],
            y=fcast_df["lower_80"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(245, 158, 11, 0.15)",
            name="80% Confidence Band",
            hovertemplate="80% CI: [%{y:.1f} - %{text:.1f}]<extra></extra>",
            text=fcast_df["upper_80"],
        ))
        
        # Point Forecast
        fig_ts.add_trace(go.Scatter(
            x=fcast_df["date"],
            y=fcast_df["forecast"],
            name=f"Forecast ({f_resp['model_used']})",
            mode="lines+markers",
            marker=dict(size=4, color="#F59E0B"),
            line=dict(color="#F59E0B", width=2.5, dash="dash"),
            hovertemplate="<b>Forecast</b><br>Date: %{x}<br>Projected: %{y:.1f} units<extra></extra>",
        ))
        
        # Vertical Demarcation Line
        split_date = fcast_df["date"].iloc[0]
        fig_ts.add_vline(x=split_date, line_dash="dot", line_color="#64748B", line_width=1.5)
        
        fig_ts.update_layout(
            title=f"Demand Projection for {f_resp['sku']} ({f_resp['product_name']}) — Horizon: {f_resp['horizon']} Days",
            height=420,
            yaxis_title="Units Sold / Day",
            **PLOT_LAYOUT,
        )
        fig_ts.update_xaxes(**AXIS_LAYOUT)
        fig_ts.update_yaxes(**AXIS_LAYOUT)
        st.plotly_chart(fig_ts, use_container_width=True)

        # Metrics & Tournament Row
        m_col1, m_col2 = st.columns([3, 2])
        
        with m_col1:
            st.markdown("##### 🏆 Backtesting Tournament Leaderboard (Holdout Test Set)")
            comp_df = pd.DataFrame([m for m in f_resp["models_comparison"]])
            # Highlight selected model
            comp_df["Winner"] = comp_df["model_name"].apply(lambda n: "★ ACTIVE" if n == f_resp["model_used"] else "")
            comp_df.columns = ["Algorithm", "MAE", "RMSE", "MAPE (%)", "WAPE (%)", "R² Score", "Tracking Signal", "Status"]
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
            st.caption("WAPE (Weighted Absolute Percentage Error) is the supply chain retail benchmark. Tracking signal checks for forecast bias.")

        with m_col2:
            st.markdown("##### 🔍 Demand Driver Attribution")
            if f_resp.get("drivers"):
                drv_df = pd.DataFrame(f_resp["drivers"])
                fig_drv = go.Figure(go.Bar(
                    x=drv_df["importance"],
                    y=drv_df["feature"],
                    orientation="h",
                    marker_color="#3B82F6",
                    text=[f"{v*100:.0f}%" for v in drv_df["importance"]],
                    textposition="auto",
                ))
                fig_drv.update_layout(height=240, margin=dict(l=10, r=10, t=10, b=10), **PLOT_LAYOUT)
                fig_drv.update_xaxes(**AXIS_LAYOUT)
                fig_drv.update_yaxes(autorange="reversed", **AXIS_LAYOUT)
                st.plotly_chart(fig_drv, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: INVENTORY HEALTH & OPTIMIZATION
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### 📦 Multi-SKU Inventory Optimization & Stock Health")
    st.caption("Stochastic safety stock formulation incorporating joint demand uncertainty (σ_d) and supplier lead-time variance (σ_LT).")

    with st.spinner("Calculating stochastic safety stocks & stockout probabilities..."):
        h_payload = {
            "service_level": st.session_state.service_level,
            "days": st.session_state.history_days,
        }
        health_list, h_err = fetch_api("/inventory-health", method="POST", payload=h_payload)

    if h_err or not health_list:
        st.error(f"Error fetching inventory health: {h_err}")
    else:
        h_df = pd.DataFrame(health_list)

        # Visual Stock Health Bar Chart
        st.markdown("##### 📊 Stock Level vs. Reorder Point (ROP) & Safety Stock")
        fig_health = go.Figure()
        fig_health.add_trace(go.Bar(
            y=h_df["sku"],
            x=h_df["stock_level"],
            name="Current Stock",
            orientation="h",
            marker=dict(color=h_df["status"].map({
                "CRITICAL": "#EF4444",
                "REORDER NOW": "#F59E0B",
                "HEALTHY": "#10B981",
                "OVERSTOCKED": "#6366F1",
            })),
            text=h_df["stock_level"],
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Stock: %{x} units<extra></extra>",
        ))
        fig_health.add_trace(go.Scatter(
            y=h_df["sku"],
            x=h_df["reorder_point"],
            name="Reorder Point (ROP)",
            mode="markers",
            marker=dict(symbol="line-ns", size=14, color="#F8FAFC", line=dict(width=2, color="#F8FAFC")),
            hovertemplate="<b>ROP</b>: %{x} units<extra></extra>",
        ))
        fig_health.add_trace(go.Scatter(
            y=h_df["sku"],
            x=h_df["safety_stock"],
            name="Safety Stock (SS)",
            mode="markers",
            marker=dict(symbol="triangle-right", size=8, color="#F59E0B"),
            hovertemplate="<b>Safety Stock</b>: %{x} units<extra></extra>",
        ))
        fig_health.update_layout(
            height=460,
            barmode="overlay",
            xaxis_title="Units",
            **PLOT_LAYOUT,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_health.update_xaxes(**AXIS_LAYOUT)
        fig_health.update_yaxes(autorange="reversed", **AXIS_LAYOUT)
        st.plotly_chart(fig_health, use_container_width=True)

        # Status Filter Buttons
        st.markdown("##### 📋 Master Inventory Optimization Grid")
        f_status = st.radio(
            "Filter Status",
            options=["ALL", "CRITICAL", "REORDER NOW", "HEALTHY", "OVERSTOCKED"],
            horizontal=True,
            label_visibility="collapsed",
        )
        filtered_df = h_df if f_status == "ALL" else h_df[h_df["status"] == f_status]

        display_cols = [
            "sku", "name", "category", "stock_level", "on_order", "daily_demand_mean",
            "lead_time_days", "safety_stock", "reorder_point", "days_of_inventory",
            "stockout_risk_score", "status", "recommended_reorder_qty", "estimated_reorder_cost"
        ]
        grid_df = filtered_df[display_cols].copy()
        grid_df.columns = [
            "SKU", "Product Name", "Category", "Current Stock", "On Order", "Daily Demand",
            "Lead Time (d)", "Safety Stock", "ROP", "DOI (Days)",
            "Stockout Risk (%)", "Status", "Rec. Order Qty", "Order Cost ($)"
        ]
        st.dataframe(grid_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: EOQ COST OPTIMIZER
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### 📐 Economic Order Quantity (EOQ) Cost Trade-Off Studio")
    st.caption("Minimizing the sum of annual ordering setup costs and inventory carrying costs under Wilson EOQ theory.")

    eoq_sku = st.selectbox(
        "Select SKU to Analyze EOQ Cost Curve",
        options=sku_list,
        format_func=lambda x: sku_names.get(x, x),
        key="eoq_sku_select",
    )

    with st.spinner("Calculating EOQ cost curves..."):
        eoq_data, eoq_err = fetch_api("/eoq", method="POST", payload={"sku": eoq_sku})

    if eoq_err or not eoq_data:
        st.error(f"Error fetching EOQ data: {eoq_err}")
    else:
        # EOQ Metric Cards
        e1, e2, e3, e4, e5 = st.columns(5)
        with e1:
            st.markdown(f"""
            <div class="corp-card success">
                <div class="corp-card-label">Optimal EOQ (Q*)</div>
                <div class="corp-card-value">{eoq_data['eoq']} Units</div>
                <div class="corp-card-sub">Per order batch</div>
            </div>
            """, unsafe_allow_html=True)
        with e2:
            st.markdown(f"""
            <div class="corp-card">
                <div class="corp-card-label">Annual Demand (D)</div>
                <div class="corp-card-value">{eoq_data['annual_demand']:,.0f}</div>
                <div class="corp-card-sub">Units / year</div>
            </div>
            """, unsafe_allow_html=True)
        with e3:
            st.markdown(f"""
            <div class="corp-card">
                <div class="corp-card-label">Order Frequency</div>
                <div class="corp-card-value">{eoq_data['orders_per_year']} / yr</div>
                <div class="corp-card-sub">Every {eoq_data['cycle_time_days']} days</div>
            </div>
            """, unsafe_allow_html=True)
        with e4:
            st.markdown(f"""
            <div class="corp-card">
                <div class="corp-card-label">Unit Carrying Cost (H)</div>
                <div class="corp-card-value">${eoq_data['holding_cost_per_unit_year']:.2f}</div>
                <div class="corp-card-sub">Per unit / year</div>
            </div>
            """, unsafe_allow_html=True)
        with e5:
            st.markdown(f"""
            <div class="corp-card">
                <div class="corp-card-label">Min Total Annual Cost</div>
                <div class="corp-card-value">${eoq_data['total_inventory_cost']:,.2f}</div>
                <div class="corp-card-sub">Hold + Setup</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Interactive Cost Trade-off Curve
        curve_df = pd.DataFrame(eoq_data["cost_curve"])
        fig_eoq = go.Figure()
        
        # Ordering Cost Curve
        fig_eoq.add_trace(go.Scatter(
            x=curve_df["order_qty"],
            y=curve_df["ordering_cost"],
            name="Annual Ordering Setup Cost (D/Q * S)",
            mode="lines",
            line=dict(color="#EF4444", width=2, dash="dot"),
        ))
        
        # Holding Cost Curve
        fig_eoq.add_trace(go.Scatter(
            x=curve_df["order_qty"],
            y=curve_df["holding_cost"],
            name="Annual Holding Cost (Q/2 * H)",
            mode="lines",
            line=dict(color="#3B82F6", width=2, dash="dash"),
        ))
        
        # Total Cost Curve
        fig_eoq.add_trace(go.Scatter(
            x=curve_df["order_qty"],
            y=curve_df["total_cost"],
            name="Total Annual Inventory Cost (Holding + Setup)",
            mode="lines",
            line=dict(color="#10B981", width=3),
        ))
        
        # Optimal Q* Vertical Line
        fig_eoq.add_vline(
            x=eoq_data["eoq"],
            line_dash="dash",
            line_color="#F59E0B",
            annotation_text=f"EOQ Q* = {eoq_data['eoq']} units",
            annotation_position="top right",
            annotation_font_color="#F59E0B",
        )
        
        fig_eoq.update_layout(
            title=f"Total Cost Curve Trade-Off for {eoq_data['sku']} ({eoq_data['name']})",
            height=420,
            xaxis_title="Order Quantity (Units per Order)",
            yaxis_title="Annual Cost ($)",
            **PLOT_LAYOUT,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_eoq.update_xaxes(**AXIS_LAYOUT)
        fig_eoq.update_yaxes(**AXIS_LAYOUT)
        st.plotly_chart(fig_eoq, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: ABC-XYZ PORTFOLIO MATRIX
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("#### 🧩 9-Quadrant ABC-XYZ Inventory Portfolio Matrix")
    st.caption("Classifying products by Revenue Significance (ABC Pareto: 80/15/5%) and Demand Predictability (XYZ Coefficient of Variation CV).")

    with st.spinner("Generating ABC-XYZ classification matrix..."):
        abc_data, abc_err = fetch_api("/abc-xyz", method="POST", payload={})

    if abc_err or not abc_data:
        st.error(f"Error computing ABC-XYZ matrix: {abc_err}")
    else:
        abc_items = pd.DataFrame(abc_data["items"])
        matrix_counts = abc_data["matrix_summary"]

        p_col1, p_col2 = st.columns([1, 1])

        with p_col1:
            st.markdown("##### 🔲 9-Box Distribution Heatmap")
            z_matrix = [
                [matrix_counts.get("AX", 0), matrix_counts.get("AY", 0), matrix_counts.get("AZ", 0)],
                [matrix_counts.get("BX", 0), matrix_counts.get("BY", 0), matrix_counts.get("BZ", 0)],
                [matrix_counts.get("CX", 0), matrix_counts.get("CY", 0), matrix_counts.get("CZ", 0)],
            ]
            fig_heat = px.imshow(
                z_matrix,
                labels=dict(x="Demand Predictability (XYZ)", y="Revenue Significance (ABC)", color="SKU Count"),
                x=["X (Stable: CV≤0.4)", "Y (Variable: 0.4<CV≤0.75)", "Z (Erratic: CV>0.75)"],
                y=["Class A (Top 80% Rev)", "Class B (Next 15% Rev)", "Class C (Bottom 5% Rev)"],
                color_continuous_scale=[[0, "#0F172A"], [0.5, "#1E3A8A"], [1, "#2563EB"]],
                text_auto=True,
            )
            fig_heat.update_layout(height=340, **PLOT_LAYOUT)
            fig_heat.update_xaxes(**AXIS_LAYOUT)
            fig_heat.update_yaxes(**AXIS_LAYOUT)
            st.plotly_chart(fig_heat, use_container_width=True)

        with p_col2:
            st.markdown("##### 📈 Cumulative Revenue Pareto Curve (ABC)")
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Scatter(
                x=list(range(1, len(abc_items) + 1)),
                y=abc_items["cum_share"],
                mode="lines+markers",
                line=dict(color="#10B981", width=2.5),
                name="Cumulative Revenue %",
                fill="tozeroy",
                fillcolor="rgba(16, 185, 129, 0.08)",
            ))
            fig_pareto.add_hline(y=80, line_dash="dash", line_color="#F59E0B", annotation_text="Class A Cutoff (80%)")
            fig_pareto.add_hline(y=95, line_dash="dot", line_color="#EF4444", annotation_text="Class B Cutoff (95%)")
            fig_pareto.update_layout(
                height=340,
                xaxis_title="Number of SKUs (Ranked by Revenue)",
                yaxis_title="Cumulative Revenue (%)",
                **PLOT_LAYOUT,
            )
            fig_pareto.update_xaxes(**AXIS_LAYOUT)
            fig_pareto.update_yaxes(**AXIS_LAYOUT)
            st.plotly_chart(fig_pareto, use_container_width=True)

        # Quadrant Explorer
        st.markdown("##### 🎯 Recommended Replenishment Policies by Quadrant")
        q_sel = st.selectbox(
            "Select Quadrant to Inspect Strategy",
            options=["AX", "AY", "AZ", "BX", "BY", "BZ", "CX", "CY", "CZ"],
        )
        q_items = abc_items[abc_items["matrix_code"] == q_sel]
        
        if len(q_items) > 0:
            rec_strategy = q_items["recommended_strategy"].iloc[0]
            st.markdown(f"""
            <div style="background:#111827; border:1px solid #1E293B; border-left:4px solid #2563EB; border-radius:6px; padding:12px 16px; margin-bottom:14px;">
                <span style="font-weight:700; color:#38BDF8; font-size:0.88rem;">Policy Playbook for {q_sel}: </span>
                <span style="color:#CBD5E1; font-size:0.85rem;">{rec_strategy}</span>
            </div>
            """, unsafe_allow_html=True)
            
            show_q = q_items[["sku", "name", "category", "annual_revenue", "revenue_share", "demand_cv", "matrix_code"]].copy()
            show_q.columns = ["SKU", "Product Name", "Category", "Annual Revenue ($)", "Rev Share (%)", "Demand CV", "Matrix Code"]
            st.dataframe(show_q, use_container_width=True, hide_index=True)
        else:
            st.info(f"No SKUs currently fall under quadrant {q_sel}.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: SUPPLY CHAIN STRESS LAB
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("#### ⚡ Supply Chain Resilience & Stress Testing Lab")
    st.caption("Simulate supplier disruptions, demand surge/plunge shocks, and interest rate fluctuations to measure working capital and stockout impacts.")

    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    with s_col1:
        lt_shock = st.slider("Supplier Lead Time Shock (Δ Days)", min_value=-3, max_value=21, value=5, step=1,
                             help="Simulates port congestion, supplier factory delays, or supply disruptions.")
    with s_col2:
        dem_shock = st.slider("Market Demand Shock (Δ %)", min_value=-40.0, max_value=80.0, value=20.0, step=5.0,
                              help="Simulates sudden viral demand spikes or economic downturns.")
    with s_col3:
        cost_shock = st.slider("Holding Cost Rate Shift (Δ %)", min_value=-0.05, max_value=0.15, value=0.03, step=0.01,
                               format="%.2f", help="Simulates rising cost of capital or warehouse storage rent.")
    with s_col4:
        sim_csl = st.select_slider(
            "Simulated Target CSL",
            options=[0.90, 0.95, 0.98, 0.99, 0.999],
            value=0.98,
            format_func=lambda x: f"{x*100:.1f}% CSL",
        )

    with st.spinner("Simulating supply chain shock scenarios..."):
        sim_payload = {
            "lead_time_shock_days": lt_shock,
            "demand_shock_pct": dem_shock,
            "holding_cost_rate_shock": cost_shock,
            "service_level_target": sim_csl,
            "days": st.session_state.history_days,
        }
        sim_res, sim_err = fetch_api("/simulate", method="POST", payload=sim_payload)

    if sim_err or not sim_res:
        st.error(f"Error running simulation: {sim_err}")
    else:
        # Impact KPIs
        i1, i2, i3 = st.columns(3)
        delta_color = "#EF4444" if sim_res["safety_stock_val_delta"] > 0 else "#10B981"
        with i1:
            st.markdown(f"""
            <div class="corp-card">
                <div class="corp-card-label">Working Capital Delta (Safety Stock)</div>
                <div class="corp-card-value" style="color:{delta_color};">${sim_res['safety_stock_val_delta']:+,.2f}</div>
                <div class="corp-card-sub">Baseline: ${sim_res['baseline_safety_stock_val']:,.0f} → Sim: ${sim_res['simulated_safety_stock_val']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        with i2:
            st.markdown(f"""
            <div class="corp-card">
                <div class="corp-card-label">Total Annual Inventory Cost Delta</div>
                <div class="corp-card-value">${sim_res['total_cost_delta']:+,.2f}</div>
                <div class="corp-card-sub">Holding + Ordering expense shift</div>
            </div>
            """, unsafe_allow_html=True)
        with i3:
            st.markdown(f"""
            <div class="corp-card critical">
                <div class="corp-card-label">Expected Stockout Exposure</div>
                <div class="corp-card-value" style="color:#F87171;">{sim_res['expected_stockouts_simulated']} SKUs</div>
                <div class="corp-card-sub">Baseline was {sim_res['expected_stockouts_baseline']} vulnerable items</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Impact Narrative Card
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #1E293B; border-left:4px solid #F59E0B; border-radius:8px; padding:16px 20px; margin-bottom:20px;">
            <div style="font-weight:700; color:#FBBF24; font-size:0.92rem; margin-bottom:4px;">Executive Stress Test Assessment</div>
            <div style="color:#E2E8F0; font-size:0.85rem; line-height:1.5;">{sim_res['impact_summary']}</div>
        </div>
        """, unsafe_allow_html=True)

        # SKU-Level Impact Table
        st.markdown("##### 🔍 SKU-Level Disruption Impact Matrix")
        impacts_df = pd.DataFrame(sim_res["sku_impacts"])
        impacts_df_disp = impacts_df[[
            "sku", "name", "category", "current_stock", "baseline_ss", "simulated_ss",
            "ss_delta", "baseline_rop", "simulated_rop", "working_cap_delta", "simulated_risk"
        ]].copy()
        impacts_df_disp.columns = [
            "SKU", "Product Name", "Category", "Current Stock", "Base SS", "Simulated SS",
            "SS Delta", "Base ROP", "Simulated ROP", "Capital Delta ($)", "Risk Tier"
        ]
        st.dataframe(impacts_df_disp, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7: PURCHASE ORDER MANAGER
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown("#### 📝 Purchase Order & Replenishment Lifecycle Manager")
    st.caption("Manage automated replenishment orders, track statuses in SQLite, and synchronize on-order inventory.")

    po_list, po_err = fetch_api("/purchase-orders")
    sugg_list, sugg_err = fetch_api("/replenishment-suggestions")

    # Replenishment Suggestions Banner
    if sugg_list:
        st.markdown("##### 🚨 Automated Replenishment Recommendations")
        sugg_df = pd.DataFrame(sugg_list)
        sugg_disp = sugg_df[["sku", "name", "category", "current_stock", "reorder_point", "recommended_order_qty", "estimated_cost", "priority"]].copy()
        sugg_disp.columns = ["SKU", "Product Name", "Category", "Current Stock", "ROP", "Suggested Qty", "Est. Cost ($)", "Priority"]
        st.dataframe(sugg_disp, use_container_width=True, hide_index=True)
    else:
        st.info("No immediate replenishment orders required under current stock levels.")

    st.markdown("---")

    # Create New PO Form & Status Advance Form
    po_col1, po_col2 = st.columns([1, 1])

    with po_col1:
        st.markdown("##### ➕ Create New Purchase Order")
        with st.form("create_po_form"):
            new_po_sku = st.selectbox("Product SKU", options=sku_list, format_func=lambda x: sku_names.get(x, x))
            new_po_qty = st.number_input("Order Quantity", min_value=1, max_value=5000, value=50, step=10)
            new_po_priority = st.selectbox("Order Priority", options=["CRITICAL", "HIGH", "MEDIUM", "LOW"])
            po_submit = st.form_submit_button("Generate Purchase Order", use_container_width=True)

            if po_submit:
                with st.spinner("Submitting purchase order to database..."):
                    po_payload = {
                        "sku": new_po_sku,
                        "order_qty": int(new_po_qty),
                        "priority": new_po_priority,
                    }
                    new_po_res, new_po_err = fetch_api("/purchase-orders", method="POST", payload=po_payload)
                    if not new_po_err:
                        st.success(f"Created purchase order {new_po_res['po_number']} successfully!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Error creating PO: {new_po_err}")

    with po_col2:
        st.markdown("##### 🔄 Advance Purchase Order Lifecycle")
        if po_list:
            po_options = {p["id"]: f"{p['po_number']} · {p['sku']} (Qty: {p['order_qty']}, Status: {p['status']})" for p in po_list if p.get("id")}
            if po_options:
                with st.form("update_po_form"):
                    sel_po_id = st.selectbox("Select Purchase Order", options=list(po_options.keys()), format_func=lambda x: po_options[x])
                    new_status = st.selectbox("Set New Status", options=["DRAFT", "APPROVED", "ORDERED", "RECEIVED", "CANCELLED"])
                    po_update_submit = st.form_submit_button("Update Status & Sync Inventory", use_container_width=True)

                    if po_update_submit:
                        with st.spinner("Updating PO status..."):
                            up_res, up_err = fetch_api(f"/purchase-orders/{sel_po_id}/status", method="PATCH", payload={"status": new_status})
                            if not up_err:
                                st.success(f"PO status updated to {new_status}! Inventory adjusted on RECEIPT.")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"Error updating status: {up_err}")
            else:
                st.info("No purchase orders found.")
        else:
            st.info("No purchase orders available.")

    # Master PO Registry Table
    st.markdown("##### 📋 Master Purchase Order Registry")
    if po_list:
        pos_df = pd.DataFrame(po_list)
        pos_disp = pos_df[["po_number", "sku", "product_name", "order_qty", "unit_cost", "total_cost", "status", "priority", "created_at", "expected_delivery"]].copy()
        pos_disp.columns = ["PO Number", "SKU", "Product Name", "Qty", "Unit Cost ($)", "Total Cost ($)", "Status", "Priority", "Created Date", "Expected Delivery"]
        st.dataframe(pos_disp, use_container_width=True, hide_index=True)

        # CSV Download Button
        csv_buffer = io.StringIO()
        pos_disp.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Export Purchase Orders to CSV",
            data=csv_buffer.getvalue(),
            file_name=f"nexstock_purchase_orders_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8: DATA OPERATIONS & CSV HUB
# ══════════════════════════════════════════════════════════════════════════════
with tab8:
    st.markdown("#### 💾 Data Operations & CSV Dataset Ingestion Hub")
    st.caption("Inspect persistent SQLite records, ingest custom enterprise sales CSVs, and reset the catalog benchmark.")

    # Database Summary Card
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown(f"""
        <div class="corp-card">
            <div class="corp-card-label">Active Products in Catalog</div>
            <div class="corp-card-value">{len(products_data)} SKUs</div>
            <div class="corp-card-sub">5 Retail Departments</div>
        </div>
        """, unsafe_allow_html=True)
    with d2:
        st.markdown(f"""
        <div class="corp-card">
            <div class="corp-card-label">Persistent Database Engine</div>
            <div class="corp-card-value">SQLite (app.db)</div>
            <div class="corp-card-sub">Managed via SQLModel ORM</div>
        </div>
        """, unsafe_allow_html=True)
    with d3:
        st.markdown(f"""
        <div class="corp-card">
            <div class="corp-card-label">Purchase Orders Logged</div>
            <div class="corp-card-value">{len(po_list) if po_list else 0} Orders</div>
            <div class="corp-card-sub">Full audit trail stored</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Custom CSV Ingestion
    st.markdown("##### 📤 Ingest Custom Retail Sales CSV")
    st.markdown("""
    You can upload your own transactional sales dataset. The CSV must contain at minimum:
    `date` (YYYY-MM-DD), `sku` (string identifier), and `units_sold` (numeric).
    Optional columns: `revenue`, `stock_level`, `is_promo`.
    """)

    uploaded_file = st.file_uploader("Upload Sales CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            preview_df = pd.read_csv(uploaded_file)
            st.markdown("###### File Preview (First 5 Rows):")
            st.dataframe(preview_df.head(), use_container_width=True)
            
            if st.button("🚀 Process & Ingest Into Database", use_container_width=True):
                with st.spinner("Ingesting dataset into SQLite..."):
                    uploaded_file.seek(0)
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                    up_url = f"{API}/api/v1/retail/data/upload"
                    up_r = requests.post(up_url, files=files, timeout=60)
                    if up_r.status_code == 200:
                        st.success(f"Dataset ingested successfully! {up_r.json().get('rows_inserted')} records saved.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Ingestion failed: {up_r.text}")
        except Exception as e:
            st.error(f"Failed to read CSV: {e}")

    st.markdown("---")

    # Current Catalog Master Table
    st.markdown("##### 📦 Active Catalog Master Table")
    cat_master_df = pd.DataFrame(products_data)
    cat_master_df.columns = [
        "SKU", "Product Name", "Category", "Unit Cost ($)", "Selling Price ($)",
        "Holding Rate", "Setup Cost ($)", "Lead Time (d)", "Lead Time Std",
        "MOQ", "Current Stock", "On Order"
    ]
    st.dataframe(cat_master_df, use_container_width=True, hide_index=True)
