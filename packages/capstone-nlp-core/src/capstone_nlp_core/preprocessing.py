"""Text cleaning, Arabic normalisation, language detection and the
pre-registered filtering funnel.

Two text columns leave this module:
    review_text  - raw text, untouched (consumed by the transformer models)
    clean_text   - normalised text (consumed by the TF-IDF baselines and the
                   aspect lexicon)

Every filtering step records the rows before and after so the funnel can be
reported verbatim in the Methods chapter.
"""

from __future__ import annotations

import re

import pandas as pd

from .arabic import ARABIC_CHAR_MAP, DIACRITICS
from .constants import (DISSATISFIED_LABEL, LANGUAGES, LENGTH_BAND_EDGES,
                        LENGTH_BAND_LABELS, MIN_WORDS, MIXED_THRESHOLD,
                        NEUTRAL_STAR, SATISFIED_LABEL, STAR_TO_LABEL)
from .labels import label_from_stars

# ---------------------------------------------------------------------------
# Regular expressions
# ---------------------------------------------------------------------------
ARABIC = re.compile(r"[؀-ۿ]")
LATIN = re.compile(r"[A-Za-z]")
URL = re.compile(r"https?://\S+|www\.\S+")
USERNAME = re.compile(r"@\w+")
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿]", flags=re.UNICODE)
LONG_ID = re.compile(r"\b\d{6,}\b")                           # phone / reference numbers
ELONGATION = re.compile(r"(.)\1{2,}")                         # "sooooo" -> "soo"



# ---------------------------------------------------------------------------
# Row-level functions
# ---------------------------------------------------------------------------
def detect_language(text: str | None) -> str:
    """Script-ratio language detection.

    General-purpose language identifiers behave poorly on very short store
    reviews, so the rule here is deliberately simple: count Arabic-script
    and Latin-script characters and call the review 'mixed' only when the
    minority script carries a real share of the text.
    """
    text = text or ""
    ar = len(ARABIC.findall(text))
    la = len(LATIN.findall(text))
    if ar + la == 0:
        return "unknown"
    if min(ar, la) / (ar + la) >= MIXED_THRESHOLD:
        return "mixed"
    return "Arabic" if ar > la else "English"


def normalise(text: str | None) -> str:
    """Deterministic cleaning used for the classical models.

    Order matters: URLs and usernames go first so their characters do not
    leak into the token stream, then Arabic orthography is unified, then
    everything that is not a word character is dropped.
    """
    t = URL.sub(" ", text or "")
    t = USERNAME.sub(" ", t)
    t = EMOJI.sub(" ", t)
    t = LONG_ID.sub(" ", t)
    t = DIACRITICS.sub("", t)
    t = t.translate(ARABIC_CHAR_MAP)
    t = ELONGATION.sub(r"\1\1", t)
    t = re.sub(r"[^\w\s؀-ۿ]", " ", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def word_count(text: str | None) -> int:
    return len((text or "").split())




# ---------------------------------------------------------------------------
# Frame-level pipeline
# ---------------------------------------------------------------------------
def clean_frame(raw: pd.DataFrame) -> pd.DataFrame:
    """Recompute every derived column from the raw text and stars.

    The scraper already wrote clean_text / language / label, but I recompute
    them here so the notebook is the single source of truth for the rules.
    """
    df = raw.copy()
    df["review_text"] = df["review_text"].fillna("").astype(str).str.strip()
    df["star_rating"] = pd.to_numeric(df["star_rating"], errors="coerce").astype("Int64")
    df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    df["language"] = df["review_text"].map(detect_language)
    df["clean_text"] = df["review_text"].map(normalise)
    df["word_count"] = df["review_text"].map(word_count)
    df["satisfaction_label"] = df["star_rating"].map(label_from_stars)
    df["is_neutral"] = df["star_rating"] == NEUTRAL_STAR
    return df


def length_band(n: pd.Series) -> pd.Series:
    return pd.cut(n, [-1, 2, 5, 10, 25, 10**9],
                  labels=["0-2", "3-5", "6-10", "11-25", "26+"])


def apply_funnel(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply the pre-registered inclusion criteria in order.

    Returns the modelling set and a funnel table with rows kept / removed at
    each step (this is the table reported in the Methods chapter).
    """
    steps = []

    def record(name, before, after):
        steps.append({"step": name, "rows_before": before, "rows_after": after,
                      "removed": before - after})

    n0 = len(df)
    d = df[df["review_text"].str.len() > 0]
    record("Remove empty review text", n0, len(d))

    n1 = len(d)
    d = d.drop_duplicates(subset="review_id")
    d = d[~d["clean_text"].duplicated(keep="first") | (d["clean_text"] == "")]
    record("Remove exact duplicate reviews", n1, len(d))

    n2 = len(d)
    d = d[d["word_count"] >= MIN_WORDS]
    record(f"Keep substantive reviews (>= {MIN_WORDS} words)", n2, len(d))

    n3 = len(d)
    d = d[~d["is_neutral"] & d["star_rating"].notna()]
    record("Remove neutral band (3-star) and missing stars", n3, len(d))

    n4 = len(d)
    d = d[d["language"].isin(LANGUAGES)]
    record("Restrict to Arabic or English (drop mixed / other)", n4, len(d))

    d = d[d["satisfaction_label"].isin([SATISFIED_LABEL, DISSATISFIED_LABEL])]
    funnel = pd.DataFrame(steps)
    funnel["retention_pct"] = (funnel["rows_after"] / n0 * 100).round(1)
    return d.reset_index(drop=True), funnel
