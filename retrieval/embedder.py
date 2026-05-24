"""
Embedding service.
Wraps the existing SentenceTransformer model for consistent usage.
"""

import logging
from sentence_transformers import SentenceTransformer
from config.settings import settings

logger = logging.getLogger(__name__)

_model = None


def get_model():
    """Get or load the SentenceTransformer model (singleton)."""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully")
    return _model


def encode_text(text, convert_to_tensor=True):
    """Encode a single text string into an embedding."""
    model = get_model()
    return model.encode(text, convert_to_tensor=convert_to_tensor)


def encode_texts(texts, convert_to_tensor=True, batch_size=32):
    """Encode multiple texts into embeddings."""
    model = get_model()
    return model.encode(
        texts,
        convert_to_tensor=convert_to_tensor,
        batch_size=batch_size,
        show_progress_bar=False,
    )
