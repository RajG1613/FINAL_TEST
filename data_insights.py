import io
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any

def insights_from_excel(content: bytes, query: str) -> Dict[str, Any]:
    """Simple baseline: load the first sheet, detect 'date' & 'incident' columns,
    filter last 30 days and aggregate recurring incidents."""
    df = pd.read_excel(io.BytesIO(content))
    # Try to find date & incident-like columns
    col_lower = {c.lower(): c for c in df.columns}
    date_col = next((col_lower[c] for c in col_lower if "date" in c or "created" in c), None)
    incident_col = next((col_lower[c] for c in col_lower if "incident" in c or "issue" in c or "error" in c or "category" in c), None)

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        since = datetime.now() - timedelta(days=30)
        df = df[df[date_col] >= since]

    summary = {}
    if incident_col:
        top = df[incident_col].fillna("UNKNOWN").value_counts().head(10)
        summary["top_recurring"] = top.to_dict()
        summary["total_incidents"] = int(top.sum())
    else:
        summary["note"] = "Could not detect an incident/category column."

    # Quick trend by day if date exists
    if date_col:
        trend = df.groupby(df[date_col].dt.date).size().to_dict()
        summary["trend_daily"] = {str(k): int(v) for k, v in trend.items()}

    summary["query"] = query
    return {"summary": summary}
