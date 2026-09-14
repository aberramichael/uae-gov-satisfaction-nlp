"""Backwards-compatible alias for :mod:`constants`.

The capstone's modules import ``from .config import ...``. Keeping this shim
means those files can be vendored verbatim, which is what the golden tests
check. New code should import from :mod:`capstone_nlp_core.constants`.
"""

from __future__ import annotations

from .constants import *  # noqa: F401,F403
from .constants import (  # noqa: F401  explicit re-exports for linters
    ALPHA,
    DISSATISFIED_LABEL,
    LANGUAGES,
    LENGTH_BANDS,
    MIN_WORDS,
    MIXED_THRESHOLD,
    N_BOOT,
    NEUTRAL_LABEL,
    NEUTRAL_STAR,
    POSITIVE_CLASS,
    RANDOM_SEED,
    SATISFIED_LABEL,
    STAR_TO_LABEL,
)
