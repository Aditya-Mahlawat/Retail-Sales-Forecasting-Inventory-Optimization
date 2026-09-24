"""
Formal Corporate Design System & Style Tokens for NexStock Enterprise.
Palantir Foundry / SAP IBP / Databricks corporate analytics aesthetic.
"""

FORMAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Base page typography */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #F8FAFC;
}

/* Background */
.stApp {
    background-color: #0B0F19;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0F172A !important;
    border-right: 1px solid #1E293B !important;
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}

/* Corporate Top Header Banner */
.corp-header {
    background: linear-gradient(180deg, #111827 0%, #0F172A 100%);
    border: 1px solid #1E293B;
    border-radius: 10px;
    padding: 22px 28px;
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.corp-title {
    font-size: 1.6rem;
    font-weight: 800;
    color: #F8FAFC;
    letter-spacing: -0.025em;
    margin: 0;
    line-height: 1.2;
}

.corp-subtitle {
    font-size: 0.85rem;
    color: #94A3B8;
    margin-top: 4px;
    font-weight: 400;
}

.corp-pill {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #38BDF8;
    font-family: 'JetBrains Mono', monospace;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

/* Metric Cards */
.corp-card {
    background: #111827;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 16px 20px;
    position: relative;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
    height: 100%;
}

.corp-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 8px 8px 0 0;
    background: #2563EB;
}

.corp-card.critical::before { background: #EF4444; }
.corp-card.warning::before { background: #F59E0B; }
.corp-card.success::before { background: #10B981; }

.corp-card-label {
    font-size: 0.70rem;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}

.corp-card-value {
    font-size: 1.85rem;
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1.1;
    font-family: 'Inter', sans-serif;
    margin: 2px 0 6px 0;
}

.corp-card-sub {
    font-size: 0.75rem;
    color: #64748B;
    font-weight: 500;
}

/* Formal Badges */
.badge-critical {
    background-color: rgba(239, 68, 68, 0.12);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-reorder {
    background-color: rgba(245, 158, 11, 0.12);
    color: #FBBF24;
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-healthy {
    background-color: rgba(16, 185, 129, 0.12);
    color: #34D399;
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.badge-overstock {
    background-color: rgba(99, 102, 241, 0.12);
    color: #A5B4FC;
    border: 1px solid rgba(99, 102, 241, 0.4);
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* Formal Tab Styling */
.stTabs [data-baseweb="tab-list"] {
    background-color: #0F172A;
    border-radius: 8px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #1E293B;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    color: #94A3B8;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 8px 16px;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background-color: #1E293B !important;
    color: #38BDF8 !important;
    font-weight: 700;
    border: 1px solid #334155 !important;
}

/* Formal Buttons */
.stButton > button {
    background: #2563EB;
    color: #FFFFFF;
    border: 1px solid #3B82F6;
    border-radius: 6px;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 8px 18px;
    transition: all 0.15s ease;
}

.stButton > button:hover {
    background: #1D4ED8;
    border-color: #60A5FA;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}

/* Dataframe & Tables */
div[data-testid="stDataFrame"] {
    border: 1px solid #1E293B;
    border-radius: 8px;
    overflow: hidden;
}

/* Sidebar section header */
.sidebar-header {
    font-size: 0.70rem;
    font-weight: 800;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 16px 0 8px 0;
}

/* Alert Container */
.alert-container {
    background-color: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.35);
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.alert-title {
    font-weight: 700;
    font-size: 0.88rem;
    color: #F87171;
}

.alert-desc {
    font-size: 0.78rem;
    color: #CBD5E1;
    margin-top: 2px;
}
</style>
"""

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#0F172A",
    font=dict(color="#94A3B8", family="Inter, sans-serif", size=11),
    margin=dict(l=20, r=20, t=40, b=20),
    legend=dict(
        bgcolor="rgba(15, 23, 42, 0.8)",
        bordercolor="#1E293B",
        borderwidth=1,
        font=dict(color="#CBD5E1", size=10),
    ),
)

AXIS_LAYOUT = dict(
    gridcolor="#1E293B",
    linecolor="#334155",
    tickfont=dict(color="#94A3B8", size=10),
    zerolinecolor="#334155",
)
