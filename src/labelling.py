"""Weak supervision, gold-set sampling and the stratified split."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .config import (ANNOTATION_FILE, LANGUAGES, RANDOM_SEED, REANNOTATION_FILE,
                     SPLIT_FRACTIONS, STAR_TO_LABEL)


def weak_label_from_stars(star_rating: int):
    """Map a 1-5 star rating to the binary satisfaction label (None for 3)."""
    return STAR_TO_LABEL.get(int(star_rating))


def stratified_split(df: pd.DataFrame, seed: int = RANDOM_SEED) -> dict[str, pd.DataFrame]:
    """70/15/15 split stratified jointly on label and language.

    Duplicates are removed upstream (apply_funnel) so no text can appear on
    both sides of a split. The split key is the review_id so that transformer
    predictions produced elsewhere can be paired back instance by instance.
    """
    strata = df["satisfaction_label"] + "|" + df["language"]
    train, rest = train_test_split(
        df, test_size=1 - SPLIT_FRACTIONS["train"], stratify=strata, random_state=seed)
    rest_strata = rest["satisfaction_label"] + "|" + rest["language"]
    val_share = SPLIT_FRACTIONS["val"] / (SPLIT_FRACTIONS["val"] + SPLIT_FRACTIONS["test"])
    val, test = train_test_split(
        rest, test_size=1 - val_share, stratify=rest_strata, random_state=seed)
    out = {"train": train, "val": val, "test": test}
    for k, v in out.items():
        out[k] = v.assign(split=k).reset_index(drop=True)
    return out


def check_split_leakage(splits: dict[str, pd.DataFrame]) -> dict:
    """Assert that no review_id or clean_text crosses partitions."""
    ids = {k: set(v["review_id"]) for k, v in splits.items()}
    texts = {k: set(v["clean_text"]) for k, v in splits.items()}
    report = {}
    keys = list(splits)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            report[f"{a}-{b}_id_overlap"] = len(ids[a] & ids[b])
            report[f"{a}-{b}_text_overlap"] = len(texts[a] & texts[b])
    return report


def sample_for_annotation(df: pd.DataFrame, per_language: int = 200,
                          seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Draw the gold-set sample: n per language, balanced across the two labels.

    Star rating and weak label are withheld from the annotation sheet so the
    annotator sees only the text.
    """
    rng = np.random.RandomState(seed)
    parts = []
    for lang in LANGUAGES:
        sub = df[df["language"] == lang]
        for label, grp in sub.groupby("satisfaction_label"):
            k = per_language // 2
            parts.append(grp.sample(n=min(k, len(grp)), random_state=rng))
    sample = pd.concat(parts).sample(frac=1, random_state=seed).reset_index(drop=True)
    sample["annotation_order"] = np.arange(1, len(sample) + 1)
    return sample


def load_annotations(path=ANNOTATION_FILE) -> pd.DataFrame:
    """Load the completed gold annotations.

    Expected columns: review_id, gold_label (Satisfied / Dissatisfied / Unclear).
    Reviews marked Unclear are excluded from the agreement statistic, and the
    count of exclusions is reported.
    """
    ann = pd.read_csv(path)
    required = {"review_id", "gold_label"}
    missing = required - set(ann.columns)
    if missing:
        raise ValueError(f"annotation file is missing columns: {missing}")
    return ann


def load_reannotations(path=REANNOTATION_FILE) -> pd.DataFrame:
    return pd.read_csv(path)
