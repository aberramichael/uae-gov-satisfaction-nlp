# Data Dictionary

The table below documents the fields used across the modelling dataset.

| Field | Type | Description |
|---|---|---|
| `review_id` | string | Unique identifier for the review, used for replication against the source stores. |
| `app_name` | string | Name of the UAE government app the review belongs to. |
| `platform` | categorical | Source platform: `google_play` or `app_store`. |
| `review_text` | string | Raw review text as collected, unedited. Consumed directly by transformer models. |
| `language` | categorical | Detected dominant language: `Arabic` or `English`. |
| `star_rating` | integer | Star rating from 1 to 5 given by the reviewer. |
| `review_date` | date | Date the review was posted. |
| `clean_text` | string | Cleaned and (for Arabic) normalised text. Consumed by classical models only. |
| `satisfaction_label` | categorical | Binary label: `Satisfied` or `Dissatisfied`. |
| `aspect_tags` | list[string] | Service aspects mentioned in the review (see `aspect_lexicon.md`). |

**Note on `satisfaction_label`:** The label is binary. Neutral (3-star) reviews are excluded
from the modelling set. Labels are derived by weak supervision from `star_rating`
(4-5 stars → `Satisfied`, 1-2 stars → `Dissatisfied`).
