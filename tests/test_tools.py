import pytest

import tools


@pytest.fixture
def df():
    return tools.load_sales()


def test_total_sales(df):
    assert tools.compute_sales_stats(df)["total_sales"] == 7845.0


def test_average_and_median(df):
    s = tools.compute_sales_stats(df)
    assert s["average_sales"] == 784.5
    assert s["median_sales"] == 510.0


def test_records_and_quantity(df):
    s = tools.compute_sales_stats(df)
    assert s["total_records"] == 10
    assert s["total_quantity"] == 44


def test_best_products(df):
    s = tools.compute_sales_stats(df)
    assert s["top_product_by_revenue"] == "Laptop"
    assert s["top_product_by_quantity"] == "Mouse"


def test_analyze_sales_tool():
    r = tools.analyze_sales()
    assert r["status"] == "ok" and r["total_sales"] == 7845.0


def test_missing_columns(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError):
        tools.load_sales(bad)


def test_create_task_ok():
    store = []
    r = tools.create_task(store, "Buy milk")
    assert r["status"] == "ok" and len(store) == 1


def test_create_task_empty():
    store = []
    assert tools.create_task(store, "   ")["status"] == "error"
    assert store == []