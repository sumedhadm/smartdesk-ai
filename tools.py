from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "sales.csv"
REQUIRED_COLUMNS = {"date", "product", "quantity", "sales"}


def load_sales(source=DATA_PATH) -> pd.DataFrame:
    """Load and validate sales data from a file path or an uploaded file."""
    df = pd.read_csv(source)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    df = df.dropna(subset=["date", "quantity", "sales"])

    if df.empty:
        raise ValueError("CSV has no valid rows after cleaning.")
    return df


def compute_sales_stats(df: pd.DataFrame) -> dict:
    """Pure-Python/Pandas statistics. The LLM never calculates numbers."""
    by_product = df.groupby("product")["sales"].sum().sort_values(ascending=False)
    qty_by_product = df.groupby("product")["quantity"].sum().sort_values(ascending=False)
    by_month = df.groupby(df["date"].dt.to_period("M").astype(str))["sales"].sum()

    # float()/int()/str() convert NumPy types so the result is JSON-serializable
    return {
        "total_sales": round(float(df["sales"].sum()), 2),
        "average_sales": round(float(np.mean(df["sales"])), 2),
        "median_sales": round(float(np.median(df["sales"])), 2),
        "total_records": int(len(df)),
        "total_quantity": int(df["quantity"].sum()),
        "top_product_by_revenue": str(by_product.index[0]),
        "top_product_revenue": round(float(by_product.iloc[0]), 2),
        "top_product_by_quantity": str(qty_by_product.index[0]),
        "sales_by_product": {str(k): round(float(v), 2) for k, v in by_product.items()},
        "sales_by_month": {str(k): round(float(v), 2) for k, v in by_month.items()},
    }


# ---------- Tools the AI is allowed to call ----------

def analyze_sales() -> dict:
    """Tool: compute statistics from the sample CSV."""
    try:
        return {"status": "ok", **compute_sales_stats(load_sales())}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_task(task_store: list, task_description) -> dict:
    """Tool: add a task to the session's task list."""
    if not isinstance(task_description, str) or not task_description.strip():
        return {"status": "error", "message": "Task description is empty."}
    desc = task_description.strip()
    if len(desc) > 200:
        return {"status": "error", "message": "Task description too long (max 200 chars)."}
    task = {"id": len(task_store) + 1, "description": desc, "done": False}
    task_store.append(task)
    return {"status": "ok", "task": task}