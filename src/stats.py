"""Statistical tests for model comparison and label agreement.

Reporting policy:
    Every significance test must be reported together with an effect size.
    A p-value alone is not sufficient; pair it with the corresponding effect
    size so the practical magnitude of a difference is always visible.
"""

from __future__ import annotations


def mcnemar_test(y_true, pred_a, pred_b) -> dict:
    """Compare two classifiers on the same test set with McNemar's test.

    Args:
        y_true: Ground-truth labels.
        pred_a: Predictions from model A.
        pred_b: Predictions from model B.

    Returns:
        A dict with the test statistic, p-value, and the discordant-pair
        contingency counts. Report the p-value together with an effect size.
    """
    raise NotImplementedError


def cohens_kappa(labels_a, labels_b) -> float:
    """Compute Cohen's kappa inter-rater / weak-vs-gold agreement.

    Args:
        labels_a: First set of labels (e.g. weak labels).
        labels_b: Second set of labels (e.g. gold annotations).

    Returns:
        Cohen's kappa. When reported as a significance-adjacent statistic, pair
        it with the relevant effect size for interpretation.
    """
    raise NotImplementedError


def cramers_v(x, y) -> float:
    """Compute Cramer's V as an effect size for a contingency table.

    Args:
        x: First categorical variable.
        y: Second categorical variable.

    Returns:
        Cramer's V effect size. This is the effect-size companion required
        alongside any chi-square style significance test.
    """
    raise NotImplementedError
