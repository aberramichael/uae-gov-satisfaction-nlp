"""Evaluation metrics and stratified reporting.

Macro-F1 is the headline metric; recall on the dissatisfied class is the
operationally critical secondary. Accuracy is reported but flagged as
inflated by the majority class.
"""

from __future__ import annotations

import pandas as pd
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_recall_fscore_support, roc_auc_score)

from .config import DISSATISFIED_LABEL, LANGUAGES, POSITIVE_CLASS, SATISFIED_LABEL

CLASSES = [DISSATISFIED_LABEL, SATISFIED_LABEL]


def macro_f1_report(y_true, y_pred, y_score=None) -> dict:
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=CLASSES, zero_division=0)
    out = {"n": int(len(y_true)),
           "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
           "accuracy_secondary": float(accuracy_score(y_true, y_pred))}
    for i, c in enumerate(CLASSES):
        out[f"precision_{c}"] = float(p[i])
        out[f"recall_{c}"] = float(r[i])
        out[f"f1_{c}"] = float(f[i])
        out[f"support_{c}"] = int(s[i])
    if y_score is not None:
        try:
            out["auc"] = float(roc_auc_score((pd.Series(y_true) == POSITIVE_CLASS).astype(int), y_score))
        except ValueError:
            out["auc"] = float("nan")
    return out


def confusion(y_true, y_pred) -> pd.DataFrame:
    cm = confusion_matrix(y_true, y_pred, labels=CLASSES)
    return pd.DataFrame(cm, index=[f"true_{c}" for c in CLASSES],
                        columns=[f"pred_{c}" for c in CLASSES])


def per_segment_metrics(df: pd.DataFrame, y_true, y_pred, segment_col: str) -> pd.DataFrame:
    rows = []
    yt, yp = pd.Series(list(y_true), index=df.index), pd.Series(list(y_pred), index=df.index)
    for seg, idx in df.groupby(segment_col).groups.items():
        if len(idx) == 0:
            continue
        rep = macro_f1_report(yt.loc[idx], yp.loc[idx])
        rep[segment_col] = seg
        rows.append(rep)
    cols = [segment_col, "n", "macro_f1", f"recall_{DISSATISFIED_LABEL}", f"recall_{SATISFIED_LABEL}",
            "accuracy_secondary"]
    return pd.DataFrame(rows)[cols]


def per_language_metrics(df: pd.DataFrame, y_true, y_pred) -> pd.DataFrame:
    out = per_segment_metrics(df, y_true, y_pred, "language")
    return out[out["language"].isin(LANGUAGES)].reset_index(drop=True)
