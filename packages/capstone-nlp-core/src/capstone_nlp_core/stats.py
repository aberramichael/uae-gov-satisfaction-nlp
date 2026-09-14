"""Statistical tests used across the notebooks.

Every significance test in this project is reported together with an effect
size, so each function returns both in one dictionary.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sps
from sklearn.metrics import cohen_kappa_score, f1_score
from statsmodels.stats.contingency_tables import mcnemar as sm_mcnemar
from statsmodels.stats.multitest import multipletests

from .config import ALPHA, N_BOOT, RANDOM_SEED


# ---------------------------------------------------------------------------
# Paired model comparison
# ---------------------------------------------------------------------------
def mcnemar_test(y_true, pred_a, pred_b) -> dict:
    """McNemar's test on instance-paired predictions (Dietterich, 1998).

    b = instances A got right and B got wrong, c = the reverse. The chi-square
    statistic uses the continuity correction; exact binomial p is also given
    for small discordant counts.
    """
    y_true, pred_a, pred_b = map(np.asarray, (y_true, pred_a, pred_b))
    a_ok, b_ok = pred_a == y_true, pred_b == y_true
    b = int((a_ok & ~b_ok).sum())
    c = int((~a_ok & b_ok).sum())
    both = int((a_ok & b_ok).sum())
    neither = int((~a_ok & ~b_ok).sum())
    table = [[both, b], [c, neither]]
    chi = sm_mcnemar(table, exact=False, correction=True)
    exact = sm_mcnemar(table, exact=True)
    return {"b": b, "c": c, "chi2": float(chi.statistic), "p": float(chi.pvalue),
            "p_exact": float(exact.pvalue), "n": int(len(y_true)),
            "odds_ratio_discordant": (b / c) if c else float("inf")}


# ---------------------------------------------------------------------------
# Agreement
# ---------------------------------------------------------------------------
def landis_koch(kappa: float) -> str:
    if kappa < 0:
        return "Poor"
    if kappa <= 0.20:
        return "Slight"
    if kappa <= 0.40:
        return "Fair"
    if kappa <= 0.60:
        return "Moderate"
    if kappa <= 0.80:
        return "Substantial"
    return "Almost perfect"


def cohens_kappa(labels_a, labels_b, n_boot: int = N_BOOT, seed: int = RANDOM_SEED) -> dict:
    """Cohen's kappa with observed agreement, bootstrap 95% CI and L&K band."""
    a, b = np.asarray(labels_a), np.asarray(labels_b)
    k = cohen_kappa_score(a, b)
    agree = float((a == b).mean())
    rng = np.random.RandomState(seed)
    boots = []
    n = len(a)
    for _ in range(n_boot):
        idx = rng.randint(0, n, n)
        if len(set(a[idx])) < 2 and len(set(b[idx])) < 2:
            continue
        boots.append(cohen_kappa_score(a[idx], b[idx]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n": int(n), "observed_agreement": agree, "kappa": float(k),
            "ci_low": float(lo), "ci_high": float(hi), "band": landis_koch(k)}


# ---------------------------------------------------------------------------
# Contingency tests and effect sizes
# ---------------------------------------------------------------------------
def cramers_v(x, y) -> float:
    table = pd.crosstab(pd.Series(x), pd.Series(y))
    chi2 = sps.chi2_contingency(table, correction=False)[0]
    n = table.values.sum()
    r, k = table.shape
    return float(np.sqrt(chi2 / (n * (min(r, k) - 1))))


def two_proportion_comparison(succ_a: int, n_a: int, succ_b: int, n_b: int) -> dict:
    """Compare one rate across two groups (A is the reference group).

    Returns Pearson chi-square with Yates's correction, phi, Cohen's h, the
    odds ratio, and a Wald 95% CI on the percentage-point difference.
    """
    table = np.array([[succ_a, n_a - succ_a], [succ_b, n_b - succ_b]])
    chi2, p, _, _ = sps.chi2_contingency(table, correction=True)
    chi2_raw = sps.chi2_contingency(table, correction=False)[0]
    n = table.sum()
    pa, pb = succ_a / n_a, succ_b / n_b
    phi = float(np.sqrt(chi2_raw / n))
    h = float(2 * np.arcsin(np.sqrt(pa)) - 2 * np.arcsin(np.sqrt(pb)))
    odds_a = pa / (1 - pa)
    odds_b = pb / (1 - pb)
    se = np.sqrt(pa * (1 - pa) / n_a + pb * (1 - pb) / n_b)
    diff = pa - pb
    return {"rate_a": pa, "rate_b": pb, "n_a": n_a, "n_b": n_b,
            "diff_pp": diff * 100, "diff_ci_low_pp": (diff - 1.96 * se) * 100,
            "diff_ci_high_pp": (diff + 1.96 * se) * 100,
            "chi2_yates": float(chi2), "p": float(p), "phi": phi, "cohens_h": h,
            "odds_ratio": float(odds_a / odds_b), "n": int(n)}


def aspect_association(df: pd.DataFrame, aspect_cols: list[str], label_col: str,
                       positive: str, alpha: float = ALPHA) -> pd.DataFrame:
    """Per-aspect chi-square with Benjamini-Hochberg adjustment and risk ratio.

    Risk ratio = P(mentions aspect | dissatisfied) / P(mentions aspect | satisfied).
    Ranking is by risk ratio, not by p-value.
    """
    pos = df[label_col] == positive
    rows = []
    for col in aspect_cols:
        m = df[col].astype(bool)
        a = int((m & pos).sum()); b = int((m & ~pos).sum())
        c = int((~m & pos).sum()); d = int((~m & ~pos).sum())
        p_pos = a / max(a + c, 1)
        p_neg = b / max(b + d, 1)
        if a + b == 0 or c + d == 0:
            # aspect never (or always) mentioned in this segment: no test possible
            chi2, p = np.nan, np.nan
        else:
            chi2, p, _, _ = sps.chi2_contingency([[a, b], [c, d]], correction=True)
        # log RR CI
        with np.errstate(divide="ignore", invalid="ignore"):
            rr = p_pos / p_neg if p_neg > 0 else np.nan
            se = np.sqrt(1 / max(a, 0.5) - 1 / max(a + c, 1) + 1 / max(b, 0.5) - 1 / max(b + d, 1))
            lo, hi = np.exp(np.log(rr) - 1.96 * se), np.exp(np.log(rr) + 1.96 * se)
        rows.append({"aspect": col, "n_mentions": a + b,
                     "pct_dissatisfied_mentioning": p_pos * 100,
                     "pct_satisfied_mentioning": p_neg * 100,
                     "risk_ratio": rr, "rr_ci_low": lo, "rr_ci_high": hi,
                     "chi2": chi2, "p": p})
    out = pd.DataFrame(rows)
    out["p_adj"] = np.nan
    ok = out["p"].notna()
    if ok.any():
        out.loc[ok, "p_adj"] = multipletests(out.loc[ok, "p"], alpha=alpha, method="fdr_bh")[1]
    out["significant"] = out["p_adj"] < alpha
    return out.sort_values("risk_ratio", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Bootstrap and binomial tests for classification metrics
# ---------------------------------------------------------------------------
def bootstrap_macro_f1(y_true, y_pred, n_boot: int = N_BOOT, seed: int = RANDOM_SEED) -> dict:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    rng = np.random.RandomState(seed)
    n = len(y_true)
    point = f1_score(y_true, y_pred, average="macro")
    boots = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.randint(0, n, n)
        boots[i] = f1_score(y_true[idx], y_pred[idx], average="macro")
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"macro_f1": float(point), "ci_low": float(lo), "ci_high": float(hi), "n": int(n)}


def binomial_vs_baseline(y_true, y_pred, baseline_rate: float) -> dict:
    """Exact binomial test of accuracy against a no-information rate."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    k = int((y_true == y_pred).sum())
    n = len(y_true)
    res = sps.binomtest(k, n, baseline_rate, alternative="greater")
    return {"correct": k, "n": n, "accuracy": k / n, "baseline_rate": baseline_rate,
            "p": float(res.pvalue)}


def aspect_association_from_counts(counts, alpha: float = ALPHA) -> pd.DataFrame:
    """Aspect association from pre-aggregated 2x2 counts.

    :func:`aspect_association` takes a whole DataFrame of reviews, which is the
    right shape for a notebook but the wrong shape for a web service: the
    platform must not ship 50,000 rows to the ML service just to compute ten
    chi-squares. Postgres aggregates the contingency table (10 aspects x 4
    integers) and only those 40 numbers travel.

    The arithmetic is identical to :func:`aspect_association` -- same Yates
    correction, same Benjamini-Hochberg adjustment across the family, same
    log-RR confidence interval, same ranking by risk ratio rather than by
    p-value. Ranking by effect size is deliberate: it is what a ministry can
    act on.

    Parameters
    ----------
    counts:
        Iterable of dicts with keys ``aspect``, ``a``, ``b``, ``c``, ``d``:

        =========================  =================  ===================
        ..                         mentions aspect    does not mention
        =========================  =================  ===================
        positive class (dissat.)   ``a``              ``c``
        other class (satisfied)    ``b``              ``d``
        =========================  =================  ===================

    Returns a DataFrame with the same columns as :func:`aspect_association`.
    """
    rows = []
    for rec in counts:
        a = int(rec["a"]); b = int(rec["b"])
        c = int(rec["c"]); d = int(rec["d"])
        n_pos, n_neg = a + c, b + d

        if n_pos == 0 or n_neg == 0:
            continue

        pct_pos = 100.0 * a / n_pos
        pct_neg = 100.0 * b / n_neg

        table = np.array([[a, c], [b, d]])
        if table.min() < 0 or table.sum() == 0:
            continue
        try:
            chi2, p, _, _ = sps.chi2_contingency(table, correction=True)
        except ValueError:
            chi2, p = np.nan, 1.0

        # Haldane-Anscombe correction keeps the log-RR finite on a zero cell.
        if a == 0 or b == 0:
            a_, b_ = a + 0.5, b + 0.5
            n_pos_, n_neg_ = n_pos + 1, n_neg + 1
        else:
            a_, b_, n_pos_, n_neg_ = a, b, n_pos, n_neg

        rr = (a_ / n_pos_) / (b_ / n_neg_)
        se_log = np.sqrt(1 / a_ - 1 / n_pos_ + 1 / b_ - 1 / n_neg_)
        lo = float(np.exp(np.log(rr) - 1.96 * se_log))
        hi = float(np.exp(np.log(rr) + 1.96 * se_log))

        rows.append({
            "aspect": rec["aspect"],
            "n_mentions": a + b,
            "pct_dissatisfied_mentioning": pct_pos,
            "pct_satisfied_mentioning": pct_neg,
            "risk_ratio": float(rr),
            "rr_ci_low": lo,
            "rr_ci_high": hi,
            "chi2": float(chi2),
            "p": float(p),
        })

    if not rows:
        return pd.DataFrame(columns=[
            "rank", "aspect", "n_mentions", "pct_dissatisfied_mentioning",
            "pct_satisfied_mentioning", "risk_ratio", "rr_ci_low", "rr_ci_high",
            "chi2", "p", "p_adj", "significant",
        ])

    out = pd.DataFrame(rows)
    # One BH family per call. The platform must never fold tenant-defined
    # categories into this family -- a data-dependent family makes the adjusted
    # p-values uninterpretable.
    reject, p_adj, _, _ = multipletests(out["p"], alpha=alpha, method="fdr_bh")
    out["p_adj"] = p_adj
    out["significant"] = reject

    out = out.sort_values("risk_ratio", ascending=False).reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out
