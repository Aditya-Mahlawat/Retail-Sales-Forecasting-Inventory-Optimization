# Run Log

## Commands
- `uvicorn backend.app.main:app --reload`
- `streamlit run frontend/app.py`
- `python -m pytest backend/tests -q`

## Expected Success Signals
- API health endpoint returns status ok
- Streamlit dashboard opens and loads generated summaries
- Pytest executes with all tests passing
