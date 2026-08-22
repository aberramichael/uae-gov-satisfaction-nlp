# Data Dictionary

Fields in the raw scrape (`data/raw/reviews_dataset.csv`) and the derived columns added by
notebook 02 (`data/interim/reviews_clean.parquet`, `data/processed/modelling_set.parquet`).

| Field | Type | Description |
|---|---|---|
| `review_id` | string | 16-character hash of platform, app name and the store's own review id. Unique; used to pair model predictions. |
| `app_name` | string | Name of the UAE government app the review belongs to (see `APP_LIST` in `src/config.py`). |
| `platform` | categorical | `Google Play` or `App Store`. |
| `review_text` | string | Raw review text as collected, unedited. Consumed directly by the transformer models. |
| `language` | categorical | Dominant script by character ratio: `Arabic`, `English`, `mixed` (minority script >= 15%) or `unknown` (no letters). Only Arabic and English enter the modelling set. |
| `star_rating` | integer | Star rating 1-5 given by the reviewer. Missing for a handful of App Store entries. |
| `review_date` | date | Date the review was posted. |
| `clean_text` | string | Normalised text (URLs, usernames, emoji and long numbers removed; Arabic orthography unified; elongation collapsed; lower-cased). Consumed by the TF-IDF baselines and the aspect lexicon. |
| `word_count` | integer | Whitespace tokens in `review_text`. Reviews below 6 are excluded from modelling. |
| `satisfaction_label` | categorical | `Satisfied` (4-5 stars) or `Dissatisfied` (1-2 stars). 3-star reviews carry `Neutral` in the raw file and are excluded from the modelling set. |
| `aspect_tags` | string | Pipe-separated aspects from the seed lexicon (`docs/aspect_lexicon.md`); one boolean `aspect_<name>` column per aspect is added in notebooks 03, 09 and 10. |
| `length_band` | categorical | `0-2`, `3-5`, `6-10`, `11-25`, `26+` words. |
| `split` | categorical | `train`, `val` or `test` (processed partitions only). |
