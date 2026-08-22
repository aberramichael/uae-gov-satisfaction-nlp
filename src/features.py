"""TF-IDF feature construction for the classical baselines.

Word 1-2 grams and character 3-5 grams (within word boundaries) are stacked.
The character view matters for Arabic, where clitics and spelling variation
fragment the word-level vocabulary.
"""

from __future__ import annotations

from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion


def word_vectorizer(**kw) -> TfidfVectorizer:
    return TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2,
                           sublinear_tf=True, token_pattern=r"(?u)\b\w+\b", **kw)


def char_vectorizer(**kw) -> TfidfVectorizer:
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                           sublinear_tf=True, **kw)


def word_char_features() -> FeatureUnion:
    return FeatureUnion([("word", word_vectorizer()), ("char", char_vectorizer())])


def word_only_features() -> TfidfVectorizer:
    return word_vectorizer()
