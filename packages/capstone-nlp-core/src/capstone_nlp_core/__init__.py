"""Shared NLP core for the UAE government satisfaction work.

This package is the single source of truth for the text processing that the
thesis reported and that the Mirsad platform serves. Both install it pinned to
the same tag, so the product's numbers cannot drift away from the report's.

The row-level functions are pure and dependency-free, and are safe to call from
a request handler:

    >>> from capstone_nlp_core import normalise, detect_language, tag_aspects
    >>> clean = normalise(raw)
    >>> tag_aspects(clean, raw)

Any change that alters the output of ``normalise``, ``detect_language``,
``tag_aspects`` or ``label_from_stars`` on the golden set is a MAJOR version
bump and requires a documented re-scoring plan.
"""

from __future__ import annotations

__version__ = "0.3.0"

from .arabic import (fold_arabic, has_arabic, normalise_digits,
                     strip_bidi_controls)
from .aspects import (ASPECT_DISPLAY, ASPECTS, LEXICON_VERSION, tag_aspects,
                      tag_aspects_detailed)
from .constants import (ABSTAIN_HIGH, ABSTAIN_LOW, DISSATISFIED_LABEL, LABELS,
                        MIN_WORDS, POSITIVE_CLASS, RANDOM_SEED,
                        REFERENCE_TEST_MACRO_F1, SATISFIED_LABEL,
                        TRANSFORMER_INPUT_FIELD, TRANSFORMER_MAX_LEN)
from .labels import label_from_stars
from .preprocessing import detect_language, normalise, word_count

__all__ = [
    "__version__",
    # text
    "normalise", "detect_language", "word_count",
    # labels
    "label_from_stars",
    # aspects
    "tag_aspects", "tag_aspects_detailed", "ASPECTS", "ASPECT_DISPLAY",
    "LEXICON_VERSION",
    # arabic helpers
    "fold_arabic", "has_arabic", "strip_bidi_controls", "normalise_digits",
    # constants
    "LABELS", "POSITIVE_CLASS", "SATISFIED_LABEL", "DISSATISFIED_LABEL",
    "MIN_WORDS", "RANDOM_SEED", "ABSTAIN_LOW", "ABSTAIN_HIGH",
    "TRANSFORMER_INPUT_FIELD", "TRANSFORMER_MAX_LEN",
    "REFERENCE_TEST_MACRO_F1",
]
