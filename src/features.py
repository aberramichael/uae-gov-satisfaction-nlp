"""Feature construction: TF-IDF vectorisation and aspect lexicon matching.

TF-IDF features feed the classical baselines. The aspect lexicon maps reviews
to service aspects (see ``docs/aspect_lexicon.md``) for aspect-level analysis.
"""

from __future__ import annotations

import pandas as pd


def build_tfidf(texts, **vectoriser_kwargs):
    """Fit a TF-IDF vectoriser over cleaned review text.

    Args:
        texts: Iterable of cleaned review strings (classical pipeline input).
        **vectoriser_kwargs: Keyword arguments forwarded to the vectoriser
            (e.g. ``ngram_range``, ``min_df``, ``max_features``).

    Returns:
        A tuple of the fitted vectoriser and the transformed feature matrix.
    """
    raise NotImplementedError


def load_aspect_lexicon(path: str) -> dict:
    """Load the aspect seed lexicon.

    Args:
        path: Path to the lexicon source (see ``docs/aspect_lexicon.md``).

    Returns:
        A mapping of aspect name to its English and Arabic seed keywords.
    """
    raise NotImplementedError


def tag_aspects(df: pd.DataFrame, lexicon: dict) -> pd.DataFrame:
    """Tag each review with the aspects it mentions using the seed lexicon.

    Args:
        df: DataFrame of reviews.
        lexicon: Aspect lexicon as returned by ``load_aspect_lexicon``.

    Returns:
        The DataFrame with an added column of matched aspect tags per review.
    """
    raise NotImplementedError
