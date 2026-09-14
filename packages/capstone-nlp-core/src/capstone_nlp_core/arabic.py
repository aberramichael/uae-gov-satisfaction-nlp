"""Arabic orthographic folding — one implementation.

The capstone had two: ``preprocessing.ARABIC_CHAR_MAP`` (a ``str.maketrans``
table applied inside ``normalise``) and ``aspects._norm_ar`` (a chain of
``.replace()`` calls used to expand the seed lexicon). They agreed on the seven
letter mappings, but ``_norm_ar`` did **not** strip diacritics or tatweel while
``normalise`` did — so an Arabic seed term containing a harakat or a tatweel
could never match the normalised text it was meant to match.

Folding both onto this module fixes that latent bug. The golden tests assert
that the expanded lexicon is byte-identical to the capstone's, so Table 15 does
not move.
"""

from __future__ import annotations

import re

#: Harakat (short vowels, shadda, sukun), the superscript alef, and tatweel.
#:
#: The range deliberately stops at U+065F and lists U+0670 separately. Widening
#: it to U+064B-U+0670 would swallow the Arabic-Indic digits U+0660-U+0669 and
#: silently delete every number written in Arabic numerals -- which changes
#: ``clean_text`` for ~0.5% of the corpus. Verified against the capstone's
#: original pattern by the golden tests.
DIACRITICS = re.compile("[\u064B-\u065F\u0670\u0640]")

#: Alef, ya, ta-marbuta and waw-hamza variants folded to their bare forms.
#: Arabic reviewers spell these inconsistently, and the store keyboards differ,
#: so folding them is what makes lexicon matching work at all.
ARABIC_CHAR_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",  # alef variants
        "ى": "ي",
        "ئ": "ي",  # ya variants
        "ة": "ه",  # ta marbuta
        "ؤ": "و",  # waw hamza
    }
)

#: Matches any character in the Arabic Unicode block.
ARABIC_BLOCK = re.compile(r"[؀-ۿ]")


def has_arabic(text: str | None) -> bool:
    """True when the string contains at least one Arabic-script character."""
    return bool(ARABIC_BLOCK.search(text or ""))


def fold_arabic(text: str | None, *, strip_diacritics: bool = True) -> str:
    """Apply the canonical Arabic folding.

    ``strip_diacritics`` defaults to True so this matches what ``normalise``
    does to the text being searched. Pass False only when you deliberately want
    letter folding without diacritic removal.
    """
    t = text or ""
    if strip_diacritics:
        t = DIACRITICS.sub("", t)
    return t.translate(ARABIC_CHAR_MAP)


#: Zero-width and bidirectional control characters.
#:
#: Word and Excel inject these into exported text. They survive ``normalise``
#: harmlessly (the non-word strip removes them from ``clean_text``), but the
#: transformer tokenizes ``text_raw``, which keeps them. Strip them in the
#: *connector* layer, never inside ``normalise`` — changing ``normalise`` would
#: break the golden tests and move the thesis numbers.
BIDI_CONTROLS = re.compile(r"[​-‏‪-‮⁦-⁩﻿]")


def strip_bidi_controls(text: str | None) -> str:
    """Remove zero-width and bidi override characters from raw text."""
    return BIDI_CONTROLS.sub("", text or "")


#: Arabic-Indic and Extended Arabic-Indic digits mapped to ASCII.
#:
#: Needed for *structured* columns in uploaded spreadsheets: a rating cell
#: containing "٤" fails ``pd.to_numeric``. Do not apply this to free text.
_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def normalise_digits(text: str | None) -> str:
    """Convert Arabic-Indic digits to ASCII digits."""
    return (text or "").translate(_ARABIC_DIGITS)
