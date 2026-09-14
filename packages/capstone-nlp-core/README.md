# capstone-nlp-core

The deployable extraction of this project's text pipeline: the bilingual
preprocessing, the aspect lexicon, and the statistical helpers, packaged so
something other than a notebook can install and call them.

It exists so that anything built on top of this research — a dashboard, a
service, a follow-up study — computes its numbers with **the same code that
produced the numbers in the report**, rather than a re-implementation that
quietly drifts.

## Relationship to `src/`

`src/` is the thesis code and is **frozen**. It is what the notebooks import and
what generated every figure and table in `results/`. Nothing in this package
changes it.

This package is a copy of the pure, I/O-free parts of `src/`, with four
long-standing duplications consolidated (see below). The golden tests assert the
two produce **identical output**, so the extraction is verifiable rather than
asserted:

```
Verified over the full corpus (74,412 reviews):
  normalise         0 mismatches
  detect_language   0 mismatches
  word_count        0 mismatches
  tag_aspects       0 mismatches
  label_from_stars  0 mismatches
  expanded lexicon  byte-identical
```

If those ever diverge, the report and any downstream product have stopped
agreeing, and that is a defect to fix — not a fixture to regenerate.

## What was consolidated

| Duplication in `src/` | Resolution here |
|---|---|
| `label_from_stars` existed **three** times — `preprocessing.py` (3★ → `None`), `scraping.py` (3★ → `"Neutral"`, `""` for 0, raises on non-numeric), `labelling.py` (raises on `None`) | One `label_from_stars(stars, *, neutral="drop"\|"label")`. The differing intent is preserved as a keyword; it never raises. |
| Arabic folding in both `preprocessing.ARABIC_CHAR_MAP` and `aspects._norm_ar` — and the aspect-side copy did **not** strip diacritics, so a seed term carrying a harakat could never match | One `arabic.fold_arabic()`. Fixes the latent miss without moving any published number. |
| Length bands declared twice: `config.LENGTH_BANDS` (never read) and hardcoded `pd.cut` bins inside `preprocessing.length_band` | One `LENGTH_BAND_EDGES` / `LENGTH_BAND_LABELS`, with the other forms derived. |
| No counts-based entry point for `aspect_association`, so any caller had to pass the whole DataFrame | Added `aspect_association_from_counts()`. Reproduces Table 15 exactly — ΔRR = 0, identical CI bounds, identical ranking. |

## A defect this caught

Simplifying the diacritics regex to `[ً-ٰـ]` widens the range to U+064B–U+0670,
which **swallows the Arabic-Indic digits U+0660–U+0669** — silently deleting
every number written in Arabic numerals from `clean_text`. The original
deliberately stops at U+065F and lists U+0670 separately.

It affected 24 of 5,000 sampled reviews before the golden tests caught it. There
is now a regression test pinning the behaviour.

## Known limitations, deliberately preserved

The aspect lexicon is frozen at `LEXICON_VERSION = "1.0"`, exactly as published,
including its documented weaknesses. `"تسجيل"` (registration) is a strict
substring of `"تسجيل الدخول"` (login), so **every Arabic login mention also fires
registration** — Table 15's registration risk ratio is partly login
contamination. A test pins this so it cannot be "fixed" by accident: correcting
it changes a published number and therefore belongs in an opt-in version 2.0,
not a patch release.

## Install

```bash
pip install -e packages/capstone-nlp-core          # from the repo root
pip install -e "packages/capstone-nlp-core[stats]" # + scipy/statsmodels/sklearn
```

The row-level functions need nothing but the standard library:

```python
from capstone_nlp_core import normalise, detect_language, tag_aspects

clean = normalise(raw)
tag_aspects(clean, raw)          # -> ['login', 'performance']
```

Frame-level and statistical helpers need the `stats` extra.

## Tests

```bash
PYTHONPATH=packages/capstone-nlp-core/src \
  .venv/bin/python -m pytest packages/capstone-nlp-core/tests -q
```

1,531 tests: 1,522 golden cases drawn from real store reviews — stratified
across both scripts, every star rating and every length band — plus the
invariants that are easy to break by tidying up (stage order in `normalise`,
the diacritics range, the raw-vs-clean contract, the label edge cases).

The fixture file is checksum-locked. Regenerating it is only correct as part of
a deliberate major version bump with a documented re-scoring plan.

## Versioning

Any change that alters the output of `normalise`, `detect_language`,
`tag_aspects` or `label_from_stars` on the golden set is a **major** bump. The
manifest of any model artifact records the `core_package_version` it was trained
under, so every stored prediction is traceable to the exact preprocessing that
produced it.
