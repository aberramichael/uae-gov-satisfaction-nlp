"""Characterisation tests that pin the text pipeline to the thesis.

The fixtures in ``normalise_cases.jsonl`` were generated from the capstone's
original ``src/`` code before any refactoring, over a stratified sample of real
store reviews covering both scripts, every star rating and every length band.

If any of these fail, the platform's numbers have drifted away from the
report's. That is a MAJOR version bump and a re-scoring event, never a quiet
fixture regeneration.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from capstone_nlp_core import (detect_language, label_from_stars, normalise,
                               tag_aspects, word_count)
from capstone_nlp_core.arabic import DIACRITICS, fold_arabic

HERE = pathlib.Path(__file__).parent
CASES = [json.loads(line) for line in
         (HERE / "normalise_cases.jsonl").read_text(encoding="utf-8").splitlines()]
CHECKSUM = (HERE / "CHECKSUM").read_text().strip()


def test_fixture_file_is_intact():
    """The fixture itself must not have been edited to make a test pass."""
    h = hashlib.sha256()
    for line in (HERE / "normalise_cases.jsonl").read_text(
            encoding="utf-8").splitlines():
        h.update(line.encode())
    assert h.hexdigest() == CHECKSUM, (
        "the golden fixture has been modified. Regenerating it is only correct "
        "as part of a deliberate MAJOR version bump with a re-scoring plan."
    )


def test_fixture_covers_both_scripts_and_all_length_bands():
    langs = {c["language"] for c in CASES}
    assert {"Arabic", "English"} <= langs
    # mixed/unknown must be represented too: they are the cases the funnel
    # drops and the product still has to serve.
    assert langs & {"mixed", "unknown"}
    assert min(c["word_count"] for c in CASES) < 6
    assert max(c["word_count"] for c in CASES) > 25


@pytest.mark.parametrize("case", CASES, ids=range(len(CASES)))
def test_row_level_functions_match_the_thesis(case):
    raw = case["raw"]
    assert normalise(raw) == case["clean"]
    assert detect_language(raw) == case["language"]
    assert word_count(raw) == case["word_count"]
    assert tag_aspects(case["clean"], raw) == case["aspects"]
    assert label_from_stars(case["stars"]) == case["label"]


# ---------------------------------------------------------------------------
# The specific invariants that are easy to break by "tidying up"
# ---------------------------------------------------------------------------

def test_normalise_stage_order_is_load_bearing():
    """Each stage depends on the one before it. Reordering changes output.

    URL/@/emoji/long-id stripping must precede the non-word strip, or the
    punctuation inside a URL leaks into the token stream. Diacritic removal
    must precede the letter folding, or a hamza carrying a fatha never folds.
    """
    got = normalise("Sooooo slow!! أَحمد https://x.co/a?b=1 @user 1234567 🙂")
    # "sooooo" collapses to "soo"; the URL, handle, emoji and 7-digit run are
    # gone; the alef-with-hamza folded to a bare alef.
    assert got == "soo slow احمد"


def test_diacritics_range_does_not_swallow_arabic_indic_digits():
    """U+0660-U+0669 must survive normalisation.

    Widening the diacritics range from U+065F to U+0670 silently deletes every
    number written in Arabic numerals. This was a real regression caught by
    these fixtures.
    """
    assert DIACRITICS.sub("", "٣ مرات") == "٣ مرات"
    assert "٣" in normalise("اضطر لإيقاف التطبيق ٣ مرات")
    assert normalise("تحديث ٢٠٢٦") == "تحديث ٢٠٢٦"


def test_arabic_folding_is_consistent_between_text_and_lexicon():
    """``fold_arabic`` must strip diacritics, unlike the old ``_norm_ar``.

    The old aspect-side folder did not, so a seed term carrying a harakat or a
    tatweel could never match the normalised text it was meant to match.
    """
    assert fold_arabic("تسجيــل الدخـ__ول".replace("_", "")) == fold_arabic(
        "تسجيل الدخول")
    seed = "تسجيل الدخول"
    assert fold_arabic(seed) in normalise(f"مشكلة في {seed}")


def test_transformer_and_lexicon_read_different_fields():
    """The raw/clean contract. Crossing these wires degrades accuracy silently."""
    from capstone_nlp_core import TRANSFORMER_INPUT_FIELD
    assert TRANSFORMER_INPUT_FIELD == "review_text"
    raw = "Cannot LOG IN!!! 🙄"
    assert normalise(raw) != raw          # the lexicon/TF-IDF path
    assert tag_aspects(normalise(raw), raw) == ["login"]


def test_label_from_stars_edge_cases_never_raise():
    """All three of the capstone's implementations disagreed here."""
    for bad in (None, "", "abc", -1, 0, 6, float("nan")):
        assert label_from_stars(bad) is None
        assert label_from_stars(bad, neutral="label") is None

    assert label_from_stars(3) is None                       # modelling path
    assert label_from_stars(3, neutral="label") == "Neutral"  # ingestion path
    assert label_from_stars("3", neutral="label") == "Neutral"
    assert label_from_stars(1) == "Dissatisfied"
    assert label_from_stars(5) == "Satisfied"

    with pytest.raises(ValueError):
        label_from_stars(3, neutral="nonsense")


def test_lexicon_is_frozen_at_version_1_0():
    """Version 1.0 is what the thesis published. Fixes ship as an opt-in 2.0."""
    from capstone_nlp_core.aspects import ASPECTS, LEXICON_VERSION
    assert LEXICON_VERSION == "1.0"
    assert len(ASPECTS) == 10
    assert sum(len(v) for v in ASPECTS.values()) == 95


def test_known_arabic_lexicon_collision_is_still_present():
    """A documented defect, pinned so it cannot be fixed by accident.

    "تسجيل" (registration) is a strict substring of "تسجيل الدخول" (login), so
    every Arabic login mention also fires registration. Table 15's registration
    risk ratio is partly login contamination. Fixing this changes published
    numbers, so it belongs in lexicon 2.0 behind a tenant opt-in -- not in a
    patch release.
    """
    raw = "مشكلة في تسجيل الدخول"
    assert tag_aspects(normalise(raw), raw) == ["login", "registration"]
