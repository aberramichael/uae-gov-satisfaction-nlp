"""Evaluation metrics and stratified reporting.

Metric policy:
    Macro-F1 is the primary metric because the satisfaction classes are
    imbalanced. Accuracy is reported only as a secondary metric and must be
    flagged as inflated by the majority class.
"""

from __future__ import annotations

import pandas as pd


def macro_f1_report(y_true, y_pred) -> dict:
    """Compute the primary macro-F1 report.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.

    Returns:
        A dict with macro-F1 (primary) and per-class precision, recall, and F1.
        Accuracy, if included, must be labelled as a secondary, inflated metric.
    """
    raise NotImplementedError


def per_language_metrics(df: pd.DataFrame, y_true, y_pred) -> pd.DataFrame:
    """Report metrics separately for Arabic and English reviews.

    Args:
        df: DataFrame carrying a language column aligned with the labels.
        y_true: Ground-truth labels.
        y_pred: Predicted labels.

    Returns:
        A DataFrame of metrics (macro-F1 primary) per language.
    """
    raise NotImplementedError


def per_segment_metrics(df: pd.DataFrame, y_true, y_pred, segment_col: str) -> pd.DataFrame:
    """Report metrics for each value of an arbitrary segment column.

    Args:
        df: DataFrame carrying the segment column (e.g. platform, entity).
        y_true: Ground-truth labels.
        y_pred: Predicted labels.
        segment_col: Column to stratify the report by.

    Returns:
        A DataFrame of metrics (macro-F1 primary) per segment value.
    """
    raise NotImplementedError
