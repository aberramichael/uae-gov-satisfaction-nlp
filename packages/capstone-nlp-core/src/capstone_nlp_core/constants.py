"""Frozen constants shared by the thesis pipeline and the Mirsad platform.

Everything here is a pure value. There are no paths, no I/O, and no imports
beyond the standard library, so this module is safe to import inside a web
request handler.

The values are lifted verbatim from the capstone's ``src/config.py``. Changing
any of them changes the meaning of every number the thesis reports, so they are
covered by the golden tests in ``tests/golden/``.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------
SATISFIED_LABEL = "Satisfied"
DISSATISFIED_LABEL = "Dissatisfied"
NEUTRAL_LABEL = "Neutral"

NEUTRAL_STAR = 3

#: Weak-label map. 3 stars is ``None`` here: the modelling path drops it.
STAR_TO_LABEL = {
    1: DISSATISFIED_LABEL,
    2: DISSATISFIED_LABEL,
    3: None,
    4: SATISFIED_LABEL,
    5: SATISFIED_LABEL,
}

#: The class the model is scored against. Dissatisfaction is the signal a
#: ministry acts on, so it is the positive class throughout.
POSITIVE_CLASS = DISSATISFIED_LABEL

#: Order matters: index 0 is the positive class, matching the transformer's
#: ``id2label`` and sklearn's alphabetical ``classes_`` (they coincide).
LABELS = [DISSATISFIED_LABEL, SATISFIED_LABEL]

# ---------------------------------------------------------------------------
# Seeds and statistics
# ---------------------------------------------------------------------------
RANDOM_SEED = 42
N_BOOT = 2000
ALPHA = 0.05

# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
#: Reviews shorter than this were excluded from *training*. The platform still
#: ingests and displays them; see the abstention policy.
MIN_WORDS = 6

#: A review is "mixed" when the minority script carries at least this share.
MIXED_THRESHOLD = 0.15

# ---------------------------------------------------------------------------
# Length bands — single source of truth
# ---------------------------------------------------------------------------
# The capstone declared these twice (``config.LENGTH_BANDS`` as tuples, which
# nothing read, and hardcoded ``pd.cut`` bins inside ``preprocessing``). One
# definition now, with the other forms derived from it.
LENGTH_BAND_EDGES = (-1, 2, 5, 10, 25, 10**9)
LENGTH_BAND_LABELS = ("0-2", "3-5", "6-10", "11-25", "26+")

assert len(LENGTH_BAND_EDGES) == len(LENGTH_BAND_LABELS) + 1, (
    "length band edges and labels are out of sync"
)

#: Display form: inclusive (low, high) word counts, ``None`` for unbounded.
LENGTH_BANDS = [(0, 2), (3, 5), (6, 10), (11, 25), (26, None)]

# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------
SPLIT_FRACTIONS = {"train": 0.70, "val": 0.15, "test": 0.15}

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
LANGUAGES = ["Arabic", "English"]
PLATFORMS = ["Google Play", "App Store"]

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
CLASSICAL_MODELS = {
    "tfidf_lr": "TF-IDF + logistic regression",
    "tfidf_svm": "TF-IDF + linear SVM",
    "tfidf_nb": "TF-IDF + multinomial naive Bayes",
}

#: ``key -> (display name, HuggingFace id, language scope)``
TRANSFORMER_MODELS = {
    "xlmr": ("XLM-RoBERTa (base)", "xlm-roberta-base", "bilingual"),
    "mbert": ("Multilingual BERT", "bert-base-multilingual-cased", "bilingual"),
    "arabert": ("AraBERT", "aubmindlab/bert-base-arabertv2", "arabic"),
    "marbert": ("MARBERT", "UBC-NLP/MARBERT", "arabic"),
}

MODEL_DISPLAY = {
    **CLASSICAL_MODELS,
    **{k: v[0] for k, v in TRANSFORMER_MODELS.items()},
}

# ---------------------------------------------------------------------------
# Serving policy
# ---------------------------------------------------------------------------
#: Transformer input contract. The transformer reads RAW text; only the TF-IDF
#: baselines and the aspect lexicon read ``normalise()``d text. Crossing these
#: wires silently degrades accuracy, so the manifest records it and the service
#: asserts it at load time.
TRANSFORMER_INPUT_FIELD = "review_text"
TRANSFORMER_MAX_LEN = 128

#: DEFAULT abstention band on the *calibrated* P(Dissatisfied), for XLM-R.
#:
#: Measured on the held-out test set: abstaining outside this band keeps 86.8%
#: of items at 0.9616 macro-F1, against 0.9273 with no abstention. A narrower
#: band is not enough -- p in [0.4, 0.6] alone is 1.5% of items and is worse
#: than chance (0.425 accuracy); the real uncertainty lives in 0.1-0.4 and
#: 0.6-0.9.
#:
#: These are a DEFAULT, not a constant of nature. Every artifact carries its own
#: ``thresholds.json`` and the serving runtime must read that, because the band
#: is a property of the model's probability distribution rather than of the
#: task. Measured: the TF-IDF SVM baseline is far less peaked, and the same
#: (0.10, 0.90) band costs it 32.5% of coverage against XLM-R's 13.2%. Applying
#: one global band across models would quietly send a third of the corpus to the
#: review queue whenever the circuit breaker trips.
ABSTAIN_LOW = 0.10
ABSTAIN_HIGH = 0.90

#: Reference figure the served model is verified against. See
#: ``training/verify_artifact.py``.
REFERENCE_TEST_MACRO_F1 = 0.9272737237557649

#: How far the served checkpoint may drift from the reference before the
#: verification gate fails.
VERIFY_TOLERANCE = 0.01
