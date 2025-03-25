# GitHub Publishing Strategy

## Recommended Repository Name
- `Retail-Sales-Forecasting-Inventory-Optimization`

## Commit Flow
- `feat: setup project skeleton`
- `feat: add data pipeline and analysis module`
- `feat: add api endpoints and validation`
- `feat: add unique frontend dashboard`
- `docs: add runbook, proof artifacts, and interview notes`

## Push Steps
```bash
git init
git add .
git commit --trailer "Made-with: Cursor" -m "feat: initial Retail Sales Forecasting & Inventory Optimization System implementation"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

## README Must Include
- Problem statement and business value
- Tech stack and architecture
- Step-by-step run instructions
- Results with screenshots
- Future improvements
