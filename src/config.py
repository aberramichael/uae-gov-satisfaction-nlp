"""Project configuration: paths, constants, seeds, and reference data.

All paths are resolved relative to the repository root so the project can be
cloned and run from any location without editing hard-coded paths.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# config.py lives in <repo_root>/src/, so the repo root is one level up.
REPO_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"
ANNOTATIONS_DIR = DATA_DIR / "annotations"

NOTEBOOKS_DIR = REPO_ROOT / "notebooks"
MODELS_DIR = REPO_ROOT / "models"

RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
TABLES_DIR = RESULTS_DIR / "tables"
METRICS_FILE = RESULTS_DIR / "metrics.json"

DOCS_DIR = REPO_ROOT / "docs"

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Labelling
# ---------------------------------------------------------------------------
# Weak supervision maps star ratings to a binary satisfaction label.
# 3-star reviews are treated as neutral and excluded from the modelling set.
SATISFIED_LABEL = "Satisfied"
DISSATISFIED_LABEL = "Dissatisfied"

STAR_TO_LABEL = {
    1: DISSATISFIED_LABEL,
    2: DISSATISFIED_LABEL,
    3: None,  # neutral — excluded from the binary modelling set
    4: SATISFIED_LABEL,
    5: SATISFIED_LABEL,
}

# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
# Minimum number of whitespace-separated tokens for a review to be considered
# substantive enough to keep in the modelling set.
MIN_WORDS = 6

# ---------------------------------------------------------------------------
# Languages
# ---------------------------------------------------------------------------
LANGUAGES = ["Arabic", "English"]

# ---------------------------------------------------------------------------
# App list (Appendix A)
# ---------------------------------------------------------------------------
# Each entry pairs an app with its Google Play package id and its Apple App
# Store numeric id. Fill in the remaining apps and store ids below.
APP_LIST = [
    {
        "app_name": "UAE PASS",
        "gplay_id": "ae.uaepass.mobile",
        "appstore_id": "1173222969",
    },
    {
        "app_name": "DubaiNow",
        "gplay_id": "com.dubai.smartapp",
        "appstore_id": "1358918292",
    },
    {
        "app_name": "TAMM Abu Dhabi",
        "gplay_id": "ae.gov.tamm",
        "appstore_id": "1176589014",
    },
    # TODO: add the remaining apps with their gplay_id and appstore_id.
]
