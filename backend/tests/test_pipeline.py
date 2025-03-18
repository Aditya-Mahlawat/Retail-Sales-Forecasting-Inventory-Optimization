from backend.app.services.pipeline import generate_sales_data, forecast_and_reorder

def test_retail_pipeline():
    df = generate_sales_data(120, 1)
    out = forecast_and_reorder(df)
    assert df.shape[0] == 120
    assert "reorder_point" in out
