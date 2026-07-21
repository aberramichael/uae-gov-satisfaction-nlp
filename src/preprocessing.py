"""Text preprocessing: language detection, Arabic normalisation, cleaning, filtering.

Note on model inputs:
    Transformer models consume raw (uncleaned) review text so that their
    tokenisers and pretrained representations see the original surface form.
    Classical models (TF-IDF baselines) consume cleaned and normalised text.
    Keep the two pipelines separate downstream.
"""

from __future__ import annotations

import pandas as pd


def detect_language(text: str) -> str:
    """Detect the dominant language of a review.

    Args:
        text: Raw review text.

    Returns:
        The detected language, expected to be one of ``config.LANGUAGES``
        (``"Arabic"`` or ``"English"``). Other detections should be routed to
        an "other" bucket by the caller and excluded from the modelling set.
    """
    raise NotImplementedError


def normalise_arabic(text: str) -> str:
    """Normalise Arabic orthography (for classical baselines only).

    Applies standard Arabic normalisation such as unifying alef and hamza
    variants, normalising taa marbuta and alef maqsura, and stripping
    diacritics and tatweel.

    Note:
        This is intended for the classical (TF-IDF) pipeline only. Do NOT
        apply it before feeding text to transformer models — they consume raw
        text so that their pretrained tokenisers see the original form.

    Args:
        text: Arabic review text.

    Returns:
        The normalised Arabic text.
    """
    raise NotImplementedError


def clean_text(text: str) -> str:
    """Clean review text for the classical pipeline.

    Typical steps include lowercasing (for Latin script), removing URLs,
    stray markup, and excess whitespace, and handling emoji and punctuation.

    Args:
        text: Raw review text.

    Returns:
        The cleaned text used as input to classical models.
    """
    raise NotImplementedError


def filter_substantive(df: pd.DataFrame, min_words: int = 6) -> pd.DataFrame:
    """Keep only reviews that are substantive enough to model.

    Drops reviews shorter than ``min_words`` whitespace-separated tokens.

    Args:
        df: DataFrame of reviews.
        min_words: Minimum token count to retain a review (see ``config.MIN_WORDS``).

    Returns:
        The filtered DataFrame containing only substantive reviews.
    """
    raise NotImplementedError
