# Transformer Models for Predicting User Satisfaction from Arabic–English Reviews of UAE Government Digital Services

Bilingual (Arabic and English) app store reviews of UAE government mobile applications are
collected from Google Play and the Apple App Store, weakly labelled from star ratings, validated
against an annotated reference sample, and classified with TF-IDF baselines and fine-tuned
multilingual / Arabic transformers. A bilingual aspect lexicon plus BERTopic ranks the service
aspects associated with dissatisfaction, and everything is reported by language, platform and
entity with effect sizes alongside every test.

## Setup (local)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

The transformer notebook (07) needs a GPU and its own requirements (`requirements-gpu.txt`);
it is written to run on Google Colab, see below.

## Reproduce

```bash
scripts/run_all.sh                       # notebooks 02-06, 08-10 on this machine
REPORT=path/to/Final_Report.docx scripts/run_all.sh   # ... and populate the report
```

or open the notebooks in `notebooks/` and run them in numerical order. Each stage reads the
output of the previous one from `data/` or `results/`.

| # | Notebook | What it does | Writes |
|---|---|---|---|
| 01 | `01_scrape_reviews` | Documents the collection run (public endpoints, resumable) | `data/raw/reviews_dataset.csv` |
| 02 | `02_clean_normalise` | Language detection, Arabic normalisation, the logged inclusion funnel | `data/interim/`, `data/processed/modelling_set.parquet` |
| 03 | `03_eda` | Length bands, language / label balance, apps, time coverage | `results/tables/eda_*`, `results/figures/` |
| 04 | `04_weak_labels` | Star → label check, 70/15/15 split stratified on label × language, leakage check | `data/processed/{train,val,test}.parquet` |
| 05 | `05_label_validation` | 400-review annotated sample, Cohen's κ overall / per language / second pass | `table17_kappa.csv` |
| 06 | `06_baselines_tfidf` | TF-IDF + LR / linear SVM / NB, per-language metrics | `results/predictions/tfidf_*_test.csv` |
| 07 | `07_transformers` | **GPU.** XLM-R, mBERT (bilingual); AraBERT, MARBERT (Arabic) | `results/predictions/{xlmr,mbert,arabert,marbert}_test.csv` |
| 08 | `08_model_comparison` | Tables 12-14, bootstrap CIs, McNemar, confusion matrix, ROC | `table12..14_*.csv`, `fig5`, `fig6` |
| 09 | `09_aspects_bertopic` | Aspect risk ratios with BH adjustment (Table 15), optional BERTopic pass | `table15_aspects.csv` |
| 10 | `10_segmentation` | Language comparison (Table 16), κ verdict, segment-level aspect rankings | `table16_*`, `segment_*` |

Every statistic quoted in the report is also written to `results/metrics.json`;
`scripts/fill_report.py` reads that file and the tables to populate the report document.

### Running notebook 07 on Colab

1. Upload `data/processed/train.parquet`, `val.parquet` and `test.parquet` to
   `MyDrive/uae-gov-satisfaction-nlp/data/processed/` (or edit `DATA_DIR` in the notebook).
2. Open `notebooks/07_transformers.ipynb` in Colab with a GPU runtime and run all cells.
3. Copy the four `*_test.csv` files into `results/predictions/` and `transformer_runs.json`
   into `results/tables/`, then run `scripts/run_all.sh --post-colab` (and the report script
   if needed). Tables 12-14 and the RQ2 text fill themselves from those files.

Set `SMOKE_TEST = True` in the notebook to check the code path on CPU in a couple of minutes.

## Project structure

```
uae-gov-satisfaction-nlp/
├── README.md, LICENSE, requirements.txt, requirements-gpu.txt
├── data/
│   ├── raw/                scraper output, never edited by hand
│   ├── interim/            cleaned frame and funnel (regenerated, not committed)
│   ├── processed/          modelling set and train/val/test partitions (regenerated)
│   └── annotations/        400-review sample, completed labels, second pass
├── notebooks/              01-10, run in order; legacy/ holds the scraper development notebook
├── src/                    config, scraping, preprocessing, labelling, features, models,
│                           evaluation, stats, aspects, io
├── scripts/                run_all.sh, fill_report.py
├── results/
│   ├── tables/             every table in the report as CSV
│   ├── figures/            every figure in the report as PNG
│   ├── predictions/        per-model test predictions paired by review_id
│   └── metrics.json
└── docs/                   data_dictionary.md, aspect_lexicon.md
```

## Notes

- Review text is public store content; no reviewer identifiers are stored.
- Random seed 42 throughout; exact duplicates are removed before the split so no text sits on
  both sides of a partition.
- Three-star reviews are kept in the raw file and excluded from the binary modelling set.
