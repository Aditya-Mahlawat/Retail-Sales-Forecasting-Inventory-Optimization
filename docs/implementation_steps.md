# Implementation Steps (Strictly Doc-Aligned)

## What this file does
This checklist maps directly to the project prompt and is meant to be executed phase by phase.

## Phase 1: Setup
- Create virtual environment
- Install requirements
- Verify imports

## Phase 2: Data creation/loading
- Load public CSV or generate synthetic dataset
- Save to `data/raw/`

## Phase 3: Cleaning
- Null handling, type conversions, deduplication
- Save cleaned dataset to `data/processed/`

## Phase 4: EDA
- Univariate and bivariate checks
- Baseline summary tables in `outputs/`

## Phase 5: Feature engineering
- Time/date, rolling, category encodings, aggregations

## Phase 6-8: Core pipeline + insights
- Implement `forecast + reorder recommendation`
- Generate charts and actionable insights

## Phase 9: Testing
- Run `pytest backend/tests -q`

## Phase 10: GitHub publishing
- Push project with screenshot artifacts and interview notes
