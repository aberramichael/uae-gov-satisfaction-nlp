# Transformer Models for Predicting User Satisfaction from Arabic–English Reviews of UAE Government Digital Services

## Overview

This project analyses bilingual (Arabic and English) user reviews of United Arab Emirates
government mobile applications to predict user satisfaction. Reviews are collected from public
app stores, weakly labelled from star ratings, and classified with both classical baselines
(TF-IDF with linear models) and multilingual transformer models. The pipeline covers data
collection, cleaning and Arabic normalisation, weak supervision, human validation of labels,
model training and comparison, aspect discovery with topic modelling, and segmented reporting
by language, platform, and entity.

## Setup

```bash
# From the repository root
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Reproduce

Run the notebooks in `notebooks/` in numerical order. Each stage writes its outputs to `data/`
or `results/` for the next stage to consume.

1. `01_scrape_reviews.ipynb` — collect raw reviews from the app stores for the app list.
2. `02_clean_normalise.ipynb` — clean text and apply Arabic normalisation for classical models.
3. `03_eda.ipynb` — exploratory analysis: review length distribution and language split.
4. `04_weak_labels.ipynb` — derive binary satisfaction labels from star ratings.
5. `05_label_validation.ipynb` — validate weak labels against a gold set using per-language Cohen's kappa.
6. `06_baselines_tfidf.ipynb` — train and evaluate TF-IDF classical baselines.
7. `07_transformers.ipynb` — fine-tune multilingual and Arabic transformer models.
8. `08_model_comparison.ipynb` — compare models with McNemar's test and effect size.
9. `09_aspects_bertopic.ipynb` — discover and label review aspects with BERTopic.
10. `10_segmentation.ipynb` — report performance segmented by language, platform, and entity.

## Project Structure

```
uae-gov-satisfaction-nlp/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/                # scraper output, never edited by hand
│   ├── interim/            # partially processed data
│   ├── processed/          # final modelling sets
│   └── annotations/        # hand-labelled gold set and guidelines
├── notebooks/              # numbered, run in order
├── src/                    # reusable code imported by the notebooks
├── models/                 # saved model artefacts (gitignored)
├── results/
│   ├── figures/            # confusion matrices, charts
│   └── tables/             # metric tables, per-segment CSVs
└── docs/
    ├── data_dictionary.md
    └── aspect_lexicon.md
```


