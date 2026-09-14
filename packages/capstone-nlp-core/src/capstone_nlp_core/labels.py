"""Star-rating to weak label — one implementation.

The capstone had three, and they disagreed on every edge case:

===========================================  ========  ===========  ============
Location                                     3 stars   missing/0    non-numeric
===========================================  ========  ===========  ============
``preprocessing.label_from_stars``           ``None``  ``None``     ``None``
``scraping.label_from_stars``                Neutral   ``""``       raises
``labelling.weak_label_from_stars``          ``None``  raises       raises
===========================================  ========  ===========  ============

The divergence was not accidental — the scraper genuinely wants ``"Neutral"``
for 3 stars so the raw file keeps them, while the modelling funnel wants
``None`` so they drop out. That intent is preserved here as an explicit
keyword, and the crash-on-bad-input behaviour is removed: a scraper must never
die because one store returned a malformed rating.
"""

from __future__ import annotations

from .constants import NEUTRAL_LABEL, STAR_TO_LABEL


def label_from_stars(stars, *, neutral: str = "drop") -> str | None:
    """Map a star rating to a weak satisfaction label.

    Parameters
    ----------
    stars:
        Anything coercible to an int. Values outside 1-5, ``None``, empty
        strings and unparseable input all return ``None``.
    neutral:
        ``"drop"`` (default) returns ``None`` for 3 stars — the modelling path,
        matching the capstone's ``preprocessing.label_from_stars``.
        ``"label"`` returns ``"Neutral"`` — the ingestion path, matching
        ``scraping.label_from_stars``, so nothing is silently discarded at
        collection time.

    Never raises.
    """
    if neutral not in ("drop", "label"):
        raise ValueError(f"neutral must be 'drop' or 'label', got {neutral!r}")

    try:
        value = int(stars)
    except (TypeError, ValueError):
        return None

    if value == 3:
        return NEUTRAL_LABEL if neutral == "label" else None

    return STAR_TO_LABEL.get(value)


def weak_label_from_stars(star_rating):
    """Deprecated alias for the modelling-path behaviour.

    Kept so the capstone's ``labelling`` module can re-export it unchanged.
    """
    return label_from_stars(star_rating, neutral="drop")
