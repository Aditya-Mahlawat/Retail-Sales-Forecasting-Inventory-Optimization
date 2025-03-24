import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InventIQ · Retail Intelligence",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Background */
.stApp { background: #020b18; }
.stSidebar > div:first-child { background: #030d1f; border-right: 1px solid #0e2a4a; }

/* Header banner */
.hero-banner {
    background: linear-gradient(135deg, #061528 0%, #0a2540 40%, #062240 100%);
    border: 1px solid #0e3a6b;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(0,200,255,0.06) 0%, transparent 70%);
}
.hero-title { font-size: 2.2rem; font-weight: 900; color: #00c8ff;
    letter-spacing: -0.5px; margin: 0; line-height: 1.1; }
.hero-sub { font-size: 0.9rem; color: #4a7fa5; margin-top: 6px; font-weight: 400; }

/* Metric cards */
.metric-card {
    background: linear-gradient(145deg, #061c30, #0a2843);
    border: 1px solid #0e3a6b;
    border-radius: 14px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
}
.metric-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00c8ff, #0066cc);
}
.metric-label { font-size: 0.72rem; font-weight: 600; color: #4a7fa5;
    text-transform: uppercase; letter-spacing: 1.2px; }
.metric-value { font-size: 2rem; font-weight: 800; color: #00c8ff; line-height: 1.2; margin: 4px 0; }
.metric-delta { font-size: 0.78rem; }

/* Status badges */
.badge-ok { background: #0a2a1a; color: #00e676; border: 1px solid #00e676;
    border-radius: 20px; padding: 2px 12px; font-size: 0.75rem; font-weight: 600; }
.badge-warn { background: #2a1a00; color: #ffab00; border: 1px solid #ffab00;
    border-radius: 20px; padding: 2px 12px; font-size: 0.75rem; font-weight: 600; }
.badge-crit { background: #2a0a0a; color: #ff3d3d; border: 1px solid #ff3d3d;
    border-radius: 20px; padding: 2px 12px; font-size: 0.75rem; font-weight: 600; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #030d1f; border-radius: 12px;
    padding: 4px; gap: 4px; border: 1px solid #0e2a4a; }
.stTabs [data-baseweb="tab"] { border-radius: 8px; color: #4a7fa5;
    font-weight: 500; font-size: 0.85rem; padding: 8px 18px; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #003d66, #0057a8) !important;
    color: #00c8ff !important; font-weight: 700; }

/* Sidebar */
.sidebar-section { background: #061c30; border: 1px solid #0e2a4a;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; }
.sidebar-title { font-size: 0.7rem; font-weight: 700; color: #00c8ff;
    text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 10px; }
[data-testid="stSlider"] .stSlider > div { color: #00c8ff; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid #0e2a4a; border-radius: 10px; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #004a80, #0066cc);
    color: #00c8ff; border: 1px solid #0066cc; border-radius: 10px;
    font-weight: 700; font-size: 0.85rem; padding: 10px 24px;
    transition: all 0.2s ease; letter-spacing: 0.5px;
}
.stButton > button:hover { background: linear-gradient(135deg, #0057a0, #007aed);
    transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,200,255,0.2); }

/* Plotly charts background */
.js-plotly-plot { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙ Configuration</div>', unsafe_allow_html=True)
    api = st.text_input("API Base URL", "http://localhost:8001", label_visibility="collapsed")
    st.markdown('<div class="sidebar-title">📅 History Window</div>', unsafe_allow_html=True)
    days = st.slider("Days of history", 60, 365, 180, 10)
    st.markdown('<div class="sidebar-title">🎲 Simulation Seed</div>', unsafe_allow_html=True)
    seed = st.slider("Seed", 1, 100, 42)
    st.markdown('<div class="sidebar-title">⏱ Forecast Horizon</div>', unsafe_allow_html=True)
    st.markdown('<span style="color:#4a7fa5;font-size:0.8rem;">30-day demand forecast</span>', unsafe_allow_html=True)
    run = st.button("🚀 Run Full Analysis", use_container_width=True)

# ── Hero Banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <div class="hero-title">📦 InventIQ</div>
  <div class="hero-sub">Real-time Retail Intelligence · Demand Forecasting · Inventory Optimization</div>
</div>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.session_state.data = None

if run:
    with st.spinner("Fetching analytics..."):
        payload = {"days": days, "seed": seed}
        try:
            rec  = requests.post(f"{api}/api/v1/retail/recommendations", json=payload, timeout=30).json()
            fore = requests.post(f"{api}/api/v1/retail/forecast",         json=payload, timeout=30).json()
            tops = requests.post(f"{api}/api/v1/retail/top-products",     json=payload, timeout=30).json()
            inv  = requests.post(f"{api}/api/v1/retail/inventory-status", json=payload, timeout=30).json()
            st.session_state.data = {"rec": rec, "fore": fore, "tops": tops, "inv": inv}
        except Exception as e:
            st.error(f"API Error: {e}")

data = st.session_state.data

if data is None:
    st.markdown("""
    <div style="text-align:center; padding: 80px 0; color: #4a7fa5;">
      <div style="font-size:4rem; margin-bottom:16px;">📦</div>
      <div style="font-size:1.2rem; font-weight:600; color:#00c8ff;">Configure your parameters and click Run Full Analysis</div>
      <div style="font-size:0.85rem; margin-top:8px;">Demand forecasting • Inventory health • Product rankings</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

rec, fore, tops, inv = data["rec"], data["fore"], data["tops"], data["inv"]

# ── KPI Row ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
status_color = "#ff3d3d" if rec["recommendation"] == "REORDER" else "#00e676"
with c1:
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Decision</div>
      <div class="metric-value" style="color:{status_color};font-size:1.4rem;">{rec["recommendation"]}</div>
      <div class="metric-delta" style="color:#4a7fa5;">Current Inventory Status</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Avg Daily Demand</div>
      <div class="metric-value">{rec["avg_daily_demand"]}</div>
      <div class="metric-delta" style="color:#4a7fa5;">Units / day</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Reorder Point</div>
      <div class="metric-value">{rec["reorder_point"]}</div>
      <div class="metric-delta" style="color:#4a7fa5;">Safety stock: {rec['safety_stock']}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    trend_arrow = "▲" if fore["trend_slope"] > 0 else "▼"
    trend_color = "#00e676" if fore["trend_slope"] > 0 else "#ff3d3d"
    st.markdown(f"""<div class="metric-card">
      <div class="metric-label">Demand Trend</div>
      <div class="metric-value" style="color:{trend_color};">{trend_arrow} {abs(fore['trend_slope']):.3f}</div>
      <div class="metric-delta" style="color:#4a7fa5;">Units/day slope · R²={fore['r2_score']}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Demand Forecast", "📦 Inventory Status", "🏆 Top Products", "📋 Raw Data"
])

PLOT_CFG = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(3,13,31,0.8)",
    font=dict(color="#4a7fa5", family="Inter"),
    margin=dict(l=10, r=10, t=40, b=10),
)
AXES_CFG = dict(gridcolor="#0e2a4a", linecolor="#0e2a4a")

# Tab 1: Forecast
with tab1:
    hist = pd.DataFrame(fore["history"])
    fcast = pd.DataFrame(fore["forecast"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist["date"], y=hist["sales"], name="Historical",
        line=dict(color="#00c8ff", width=2), mode="lines",
    ))
    fig.add_trace(go.Scatter(
        x=fcast["date"], y=fcast["upper"],
        fill=None, mode="lines", line=dict(width=0), showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=fcast["date"], y=fcast["lower"],
        fill="tonexty", mode="lines", line=dict(width=0),
        fillcolor="rgba(0,200,255,0.08)", name="95% CI",
    ))
    fig.add_trace(go.Scatter(
        x=fcast["date"], y=fcast["forecast"], name="Forecast",
        line=dict(color="#ff9900", width=2.5, dash="dash"), mode="lines",
    ))
    fig.add_vline(x=fcast["date"].iloc[0], line_dash="dot", line_color="#4a7fa5", line_width=1)
    fig.update_layout(title="30-Day Demand Forecast", height=380, **PLOT_CFG,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#a0c4d8")))
    fig.update_xaxes(**AXES_CFG)
    fig.update_yaxes(**AXES_CFG)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="metric-card">
          <div class="metric-label">Trend Slope</div>
          <div class="metric-value" style="font-size:1.3rem;">{fore['trend_slope']:+.4f} units/day</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card">
          <div class="metric-label">Model Fit (R²)</div>
          <div class="metric-value" style="font-size:1.3rem;">{fore['r2_score']:.4f}</div>
        </div>""", unsafe_allow_html=True)

# Tab 2: Inventory
with tab2:
    st.markdown("### 🔴 SKU Inventory Health")
    for item in inv:
        pct = min(item["stock_pct"], 100)
        color = "#ff3d3d" if item["status"] == "CRITICAL" else ("#ffab00" if item["status"] == "LOW" else "#00e676")
        badge = f'<span class="badge-crit">CRITICAL</span>' if item["status"] == "CRITICAL" else \
                (f'<span class="badge-warn">LOW</span>' if item["status"] == "LOW" else
                 f'<span class="badge-ok">OK</span>')
        bar_bg = f"linear-gradient(90deg, {color}33, {color}11)"
        fill = f"linear-gradient(90deg, {color}, {color}aa)"
        st.markdown(f"""
        <div style="background:{bar_bg}; border:1px solid {color}33; border-radius:10px; padding:14px 18px; margin-bottom:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="color:#e0f0ff; font-weight:700; font-size:0.95rem;">📦 {item['sku']}</span>
            {badge}
          </div>
          <div style="display:flex; gap:20px; font-size:0.8rem; color:#4a7fa5; margin-bottom:8px;">
            <span>Stock: <b style="color:#e0f0ff;">{item['stock_level']}</b></span>
            <span>Reorder at: <b style="color:#e0f0ff;">{item['reorder_point']}</b></span>
            <span>Coverage: <b style="color:{color};">{item['stock_pct']}%</b></span>
          </div>
          <div style="background:#0a1828; border-radius:4px; height:6px; overflow:hidden;">
            <div style="width:{min(pct,100)}%; height:100%; background:{fill}; border-radius:4px;"></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    critical = [i for i in inv if i["status"] == "CRITICAL"]
    low = [i for i in inv if i["status"] == "LOW"]
    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Critical", len(critical))
    c2.metric("🟡 Low Stock", len(low))
    c3.metric("🟢 Healthy", len(inv) - len(critical) - len(low))

# Tab 3: Top Products
with tab3:
    tops_df = pd.DataFrame(tops)
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        y=tops_df["sku"], x=tops_df["revenue"],
        orientation="h", marker=dict(
            color=tops_df["revenue"],
            colorscale=[[0,"#003366"],[0.5,"#0066cc"],[1,"#00c8ff"]],
            showscale=False,
        ), text=[f"${v:,}" for v in tops_df["revenue"]],
        textposition="outside", textfont=dict(color="#00c8ff"),
        name="Revenue",
    ))
    fig2.update_layout(title="Revenue by SKU", height=360, **PLOT_CFG)
    fig2.update_xaxes(**AXES_CFG)
    fig2.update_yaxes(autorange="reversed", **AXES_CFG)
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=tops_df["units_sold"], y=tops_df["margin_pct"],
        mode="markers+text",
        marker=dict(size=16, color=tops_df["revenue"],
            colorscale=[[0,"#003366"],[1,"#00c8ff"]], showscale=True,
            colorbar=dict(title="Revenue", tickfont=dict(color="#4a7fa5")),
            line=dict(color="#00c8ff", width=1)),
        text=tops_df["sku"], textposition="top center",
        textfont=dict(color="#a0c4d8", size=9),
    ))
    fig3.update_layout(title="Units Sold vs Margin %", height=360, **PLOT_CFG,
        xaxis_title="Units Sold", yaxis_title="Margin %")
    fig3.update_xaxes(**AXES_CFG)
    fig3.update_yaxes(**AXES_CFG)
    st.plotly_chart(fig3, use_container_width=True)

# Tab 4: Raw Data
with tab4:
    sample_df = pd.DataFrame(rec.get("sample", []))
    st.markdown("#### Recent Sales Data")
    st.dataframe(sample_df.style.set_properties(**{
        "background-color": "#061c30", "color": "#a0c4d8",
        "border-color": "#0e2a4a",
    }), use_container_width=True)
    st.markdown("#### Top Products Table")
    st.dataframe(pd.DataFrame(tops), use_container_width=True)
    st.markdown("#### Inventory Table")
    st.dataframe(pd.DataFrame(inv), use_container_width=True)
