"""Classical baseline models.

Each builder returns an sklearn Pipeline that takes clean_text and outputs a
label, plus a score for the dissatisfied class for ROC curves.
"""

from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .config import RANDOM_SEED
from .features import word_char_features, word_only_features


def build_baselines() -> dict[str, Pipeline]:
    return {
        "tfidf_lr": Pipeline([
            ("features", word_char_features()),
            ("clf", LogisticRegression(C=4.0, class_weight="balanced", max_iter=2000,
                                       solver="liblinear", random_state=RANDOM_SEED)),
        ]),
        "tfidf_svm": Pipeline([
            ("features", word_char_features()),
            # calibrated so the SVM can also produce a probability for the ROC curve
            ("clf", CalibratedClassifierCV(
                LinearSVC(C=0.5, class_weight="balanced", random_state=RANDOM_SEED), cv=3)),
        ]),
        "tfidf_nb": Pipeline([
            ("features", word_only_features()),
            ("clf", MultinomialNB(alpha=0.3)),
        ]),
    }


def positive_score(pipe: Pipeline, texts, positive_class: str):
    """Probability of the positive (dissatisfied) class."""
    proba = pipe.predict_proba(texts)
    idx = list(pipe.classes_).index(positive_class)
    return proba[:, idx]
