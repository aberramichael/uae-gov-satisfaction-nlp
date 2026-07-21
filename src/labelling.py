"""Weak supervision labelling and gold-set loading.

Satisfaction labels are derived from star ratings by weak supervision:
4-5 stars map to "Satisfied", 1-2 stars map to "Dissatisfied", and 3-star
reviews are treated as neutral and excluded from the binary modelling set.
"""

from __future__ import annotations

import pandas as pd

from src.config import STAR_TO_LABEL


def weak_label_from_stars(stars: int) -> str | None:
    """Map a star rating to a binary satisfaction label.

    Args:
        stars: Star rating from 1 to 5.

    Returns:
        ``"Satisfied"`` for 4-5 stars, ``"Dissatisfied"`` for 1-2 stars, and
        ``None`` for 3-star (neutral) reviews, which are excluded from the
        binary modelling set.
    """
    return STAR_TO_LABEL.get(stars)


def load_annotations(path: str) -> pd.DataFrame:
    """Load the hand-labelled gold set used to validate weak labels.

    Args:
        path: Path to the annotation file (see ``data/annotations/``).

    Returns:
        A DataFrame of human-annotated reviews with their gold labels.
    """
    raise NotImplementedError
