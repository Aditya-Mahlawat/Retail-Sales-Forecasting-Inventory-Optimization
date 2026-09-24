# NexStock Enterprise · Retail Sales Forecasting & Multi-Echelon Inventory Optimization Suite

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-2.0.0-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.64-FF4B4B?logo=streamlit)](https://streamlit.io)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-ML%20Tournament-F7931E?logo=scikitlearn)](https://scikit-learn.org)
[![Tests](https://img.shields.io/badge/Tests-8%20Passed%20(100%25)-success?logo=pytest)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An **enterprise-grade, production-style retail supply chain analytics platform** bridging **predictive time-series machine learning** and **prescriptive operations research**. 

Engineered with a high-performance **FastAPI** backend, persistent **SQLModel (SQLite)** database, and an executive-tier **Streamlit** corporate decision-support console with dark-themed **Plotly** visualizations.

---

## 🌟 Key Capabilities

### 1. Multi-Model Demand Forecasting Tournament
- **Competitive Algorithmic Arena**:
  - **Histogram Gradient Boosting (HistGBM)**: Captures complex non-linear lag interactions and marketing promotion lifts.
  - **Regularized Ridge Regression**: Robust L2-penalized linear model with standardized feature scalers.
  - **Holt-Winters Additive Exponential Smoothing**: Pure time-series decomposition modeling level, trend, and 7-day cyclical seasonality.
  - **Seasonal Naive Benchmark**: Baseline tracking 7-day persistence.
- **30-Day Walk-Forward Backtesting**:
  - Calculates **WAPE** (Weighted Absolute Percentage Error - retail gold standard), **RMSE**, **MAE**, **MAPE**, **$R^2$ Score**, and **Tracking Signal** (monitoring forecast bias).
  - Auto-selects the winning model with lowest out-of-sample error while presenting a transparent leaderboard.
- **Uncertainty Quantification**:
  - Projects future demand with expanding **80% and 95% confidence intervals**.
  - Feature driver attribution (7-day seasonality, recent momentum, baseline trend, marketing promotions).

### 2. Operations Research & Stochastic Inventory Optimization
- **Joint Demand and Lead-Time Variance Safety Stock**:
  $$\sigma_{DL} = \sqrt{L \cdot \sigma_d^2 + d^2 \cdot \sigma_{LT}^2}$$
  $$SS = Z \times \sigma_{DL}$$
  $$ROP = (d \times L) + SS$$
  Where $d$ is mean daily demand, $\sigma_d$ is demand standard deviation, $L$ is supplier lead time, $\sigma_{LT}$ is lead-time variance, and $Z$ is normal distribution quantile mapped to target **Cycle Service Levels (CSL: 90%, 95%, 98%, 99%)**.
- **Days of Inventory (DOI) & Stockout Risk Scoring**:
  - Real-time stockout probability calculation: $P(\text{Stockout}) = 1 - \Phi(Z_{\text{actual}})$.
  - Multi-tier classification: `CRITICAL` ($Stock \le 0.5 \times SS$), `REORDER NOW` ($Stock \le ROP$), `HEALTHY`, and `OVERSTOCKED` ($DOI > 65$ days).

### 3. Economic Order Quantity (EOQ) Cost Optimization
- **Wilson EOQ Formulation**:
  $$EOQ = \sqrt{\frac{2 \cdot D \cdot S}{H}}$$
  Where $D$ is annual demand, $S$ is fixed order setup cost, and $H$ is unit annual carrying cost ($h \times \text{unit cost}$).
- **Interactive Cost Trade-Off Curves**:
  - Visualizes Annual Ordering Cost vs. Annual Holding Cost vs. Total Cost convex curve.
  - Highlights optimal batch size ($Q^*$) and evaluates supplier Minimum Order Quantity (MOQ) penalties.

### 4. 9-Quadrant ABC-XYZ Inventory Portfolio Matrix
- **ABC Classification**: Cumulative annual revenue Pareto analysis (Class A: top 80%, Class B: next 15%, Class C: bottom 5%).
- **XYZ Classification**: Demand variability based on Coefficient of Variation ($CV = \sigma_d / \mu_d$):
  - **Class X** ($CV \le 0.40$): Smooth, highly predictable.
  - **Class Y** ($0.40 < CV \le 0.75$): Moderately fluctuating.
  - **Class Z** ($CV > 0.75$): Erratic, sporadic demand.
- **Interactive 9-Cell Matrix**:
  - Dynamic heatmap and Pareto curve mapping every SKU to operational replenishment policies (e.g., `AX` = Automated JIT, `CZ` = Dropship / Make-to-Order / SKU Rationalization).

### 5. Supply Chain Resilience & Stress Testing Lab (What-If Simulator)
- Real-time scenario simulation:
  - **Supplier Lead Time Delays** ($\Delta L$ from -3 to +21 days)
  - **Market Demand Shocks** ($\Delta D$ from -40% to +80%)
  - **Cost of Capital / Holding Rate Shifts** ($\Delta h$ from -5% to +15%)
  - **Service Level Policy Shifts** (85% to 99.9%)
- Quantifies financial impact: Safety stock working capital delta ($\Delta \$$), total inventory carrying cost delta, and at-risk stockout count.

### 6. End-to-End Purchase Order Lifecycle Manager
- **Automated Replenishment Engine**: Flags SKUs below ROP and calculates optimal order quantities factoring EOQ and MOQ constraints.
- **Full PO Lifecycle**: Create POs $\to$ `DRAFT` $\to$ `APPROVED` $\to$ `ORDERED` $\to$ `RECEIVED`.
- **Database Inventory Synchronization**: Receiving a purchase order automatically increments physical stock in SQLite and decrements on-order counters.
- **Exporting**: One-click CSV export of all purchase orders.

### 7. Data Operations & Custom CSV Ingestion
- Upload custom retail sales CSV files (`date`, `sku`, `units_sold`).
- 1-click database catalog re-seeder (pre-populated with 16 realistic SKUs across Electronics, Apparel, Groceries, Home Goods, Beauty with 365+ days of daily transactional history).

---

## 🏗️ Architecture & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NexStock Executive UI                           │
│                (Streamlit · Slate/Navy Theme · Plotly)                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST
┌───────────────────────────────────▼────────────────────────────────────┐
│                       FastAPI Backend Service                          │
│                         (Uvicorn · Port 8001)                          │
├──────────────────┬──────────────────┬─────────────────┬────────────────┤
│ Forecasting      │ Inventory        │ Stress          │ Order          │
│ Tournament       │ Optimization     │ Simulator       │ Lifecycle      │
│ (HistGBM/Ridge/  │ (Safety Stock/   │ (What-If Delays/│ (PO Creation/  │
│  Holt-Winters)   │  EOQ / ABC-XYZ)  │  Demand Shocks) │  Stock Sync)   │
└──────────────────┴─────────┬────────┴─────────────────┴────────────────┘
                             │ SQLModel ORM
┌────────────────────────────▼───────────────────────────────────────────┐
│                     Persistent SQLite Database                         │
│                             (app.db)                                   │
│  - Products (16 SKUs across 5 Retail Categories)                       │
│  - Daily Sales History (5,840+ Daily Records with Trend & Promos)      │
│  - Purchase Orders (Audit Trail & Status Tracking)                     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/Aditya-Mahlawat/Retail-Sales-Forecasting-Inventory-Optimization.git
cd Retail-Sales-Forecasting-Inventory-Optimization

# Create and activate virtual environment
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start the Backend API (Port 8001)

```bash
# Windows / Linux / macOS
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```
Interactive OpenAPI documentation will be accessible at:  
👉 **http://127.0.0.1:8001/docs**

### 3. Launch the Executive Dashboard (Port 8501)

In a second terminal window:

```bash
# Windows / Linux / macOS
streamlit run frontend/app.py --server.port 8501
```
Open your browser at:  
👉 **http://localhost:8501**

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/api/v1/retail/health` | Healthcheck and engine version status |
| `GET` | `/api/v1/retail/executive-summary` | Aggregated corporate KPIs, inventory valuation, category breakdown |
| `GET` | `/api/v1/retail/products` | Retrieve all 16 catalog products with costs and lead times |
| `GET` | `/api/v1/retail/products/{sku}` | Detailed SKU metadata and inventory status |
| `POST` | `/api/v1/retail/forecast` | Multi-model tournament forecast with backtest metrics & 80/95% CI |
| `POST` | `/api/v1/retail/inventory-health` | Safety stocks, ROPs, DOI, and stockout risk scores for all SKUs |
| `POST` | `/api/v1/retail/eoq` | Economic Order Quantity metrics and cost trade-off curves |
| `POST` | `/api/v1/retail/abc-xyz` | 9-box portfolio matrix distribution and strategic playbooks |
| `POST` | `/api/v1/retail/simulate` | Supply chain what-if disruption stress testing |
| `GET` | `/api/v1/retail/purchase-orders` | List all historical and active purchase orders |
| `POST` | `/api/v1/retail/purchase-orders` | Create a new purchase order |
| `PATCH`| `/api/v1/retail/purchase-orders/{id}/status` | Update PO status (DRAFT/APPROVED/ORDERED/RECEIVED) |
| `GET` | `/api/v1/retail/replenishment-suggestions` | Automated replenishment queue for items below ROP |
| `POST` | `/api/v1/retail/data/seed` | Reset & reseed database with fresh 1-year catalog |
| `POST` | `/api/v1/retail/data/upload` | Ingest external retail sales CSV file |

---

## 🧪 Automated Testing

Execute the complete pytest test suite:

```bash
pytest backend/tests -v
```

Output:
```
============================= test session starts =============================
backend/tests/test_pipeline.py::test_legacy_retail_pipeline PASSED       [ 12%]
backend/tests/test_pipeline.py::test_database_seeding PASSED             [ 25%]
backend/tests/test_pipeline.py::test_forecasting_metrics_and_tournament PASSED [ 37%]
backend/tests/test_pipeline.py::test_inventory_stochastic_safety_stock_and_eoq PASSED [ 50%]
backend/tests/test_pipeline.py::test_abc_xyz_portfolio_analysis PASSED   [ 62%]
backend/tests/test_pipeline.py::test_supply_chain_stress_simulation PASSED [ 75%]
backend/tests/test_pipeline.py::test_purchase_order_lifecycle PASSED     [ 87%]
backend/tests/test_pipeline.py::test_api_endpoints PASSED                [100%]

======================== 8 passed, 1 warning in 3.36s =========================
```

---

## 📂 Project Organization

```
Retail-Sales-Forecasting-Inventory-Optimization/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   └── routes.py           # 15+ REST API endpoints
│   │   ├── core/
│   │   │   ├── config.py           # Application settings
│   │   │   └── database.py         # SQLModel database engine & session dependency
│   │   ├── models/
│   │   │   └── record.py           # Product, DailySale, PurchaseOrder, ForecastRun
│   │   ├── schemas/
│   │   │   └── record.py           # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── data_generator.py   # 16-SKU catalog & synthetic history seeder
│   │   │   ├── forecasting.py      # HistGBM, Ridge, Holt-Winters, Seasonal Naive
│   │   │   ├── inventory.py        # Stochastic Safety Stock, EOQ, ABC-XYZ
│   │   │   ├── simulation.py       # What-if supply chain stress tester
│   │   │   ├── order_service.py    # Purchase order lifecycle & inventory sync
│   │   │   └── pipeline.py         # Backward compatibility layer
│   │   └── main.py                 # FastAPI application & startup lifecycle
│   └── tests/
│       └── test_pipeline.py        # Comprehensive unit & integration tests
├── frontend/
│   ├── app.py                      # 8-module executive Streamlit dashboard
│   └── styles.py                   # Corporate dark theme tokens & Plotly layouts
├── app.db                          # Persistent SQLite database
├── requirements.txt                # Pinned production dependencies
├── run_windows.ps1                 # Windows PowerShell launcher
├── run_unix.sh                     # Unix/macOS launcher
└── README.md                       # Comprehensive platform documentation
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
