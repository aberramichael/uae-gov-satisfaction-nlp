"""Model training and fine-tuning wrappers.

Classical baseline:
    TF-IDF features with a linear classifier, trained on cleaned text.

Transformer models:
    - XLM-RoBERTa  — multilingual, trained on the full Arabic+English set.
    - mBERT        — multilingual, trained on the full Arabic+English set.
    - AraBERT      — trained on the Arabic subset only.
    - MARBERT      — trained on the Arabic subset only.
    Transformers consume raw review text (no cleaning or Arabic normalisation).
"""

from __future__ import annotations


def train_tfidf_baseline(X_train, y_train, **kwargs):
    """Train a TF-IDF classical baseline classifier.

    Args:
        X_train: TF-IDF feature matrix for the training split (cleaned text).
        y_train: Training labels.
        **kwargs: Hyperparameters for the underlying classifier.

    Returns:
        The fitted classical model.
    """
    raise NotImplementedError


def finetune_transformer(model_name: str, train_ds, val_ds, **kwargs):
    """Fine-tune a transformer model for binary satisfaction classification.

    Args:
        model_name: Hugging Face model identifier or short name. Multilingual
            models (XLM-RoBERTa, mBERT) train on the full set; Arabic-specific
            models (AraBERT, MARBERT) train on the Arabic subset only.
        train_ds: Training dataset of raw review text and labels.
        val_ds: Validation dataset of raw review text and labels.
        **kwargs: Training arguments (learning rate, epochs, batch size, etc.).

    Returns:
        The fine-tuned model and its training metadata.
    """
    raise NotImplementedError
