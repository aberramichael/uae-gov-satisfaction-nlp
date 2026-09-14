"""Small helpers for reading and writing pipeline artefacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .config import (FIGURES_DIR, METRICS_FILE, PREDICTIONS_DIR, RAW_FILE,
                     TABLES_DIR)


def ensure_dirs():
    for d in (FIGURES_DIR, TABLES_DIR, PREDICTIONS_DIR, RAW_FILE.parent):
        d.mkdir(parents=True, exist_ok=True)


def load_raw(path: Path = RAW_FILE) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", dtype=str)


def save_table(df: pd.DataFrame, name: str, index: bool = False) -> Path:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    p = TABLES_DIR / f"{name}.csv"
    df.to_csv(p, index=index)
    return p


def update_metrics(section: str, payload: dict) -> None:
    """Merge a section into results/metrics.json (the report reads this file)."""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(METRICS_FILE.read_text()) if METRICS_FILE.exists() else {}
    data[section] = payload
    METRICS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=_jsonable))


def read_metrics() -> dict:
    return json.loads(METRICS_FILE.read_text()) if METRICS_FILE.exists() else {}


def _jsonable(o):
    try:
        import numpy as np
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.bool_,)):
            return bool(o)
    except ImportError:
        pass
    if isinstance(o, pd.Timestamp):
        return o.isoformat()
    return str(o)


def save_predictions(model_key: str, df: pd.DataFrame) -> Path:
    """Write review_id, y_true, y_pred, p_dissat so models can be paired later."""
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    p = PREDICTIONS_DIR / f"{model_key}_test.csv"
    df[["review_id", "y_true", "y_pred", "p_dissat"]].to_csv(p, index=False)
    return p


def load_predictions() -> dict[str, pd.DataFrame]:
    out = {}
    for p in sorted(PREDICTIONS_DIR.glob("*_test.csv")):
        out[p.name.replace("_test.csv", "")] = pd.read_csv(p, dtype={"review_id": str})
    return out
