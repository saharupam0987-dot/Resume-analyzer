from sentence_transformers import SentenceTransformer
from config.settings import EMBEDDING_MODEL

_model = None


def get_embedding_model() -> SentenceTransformer:
    """Get or create the singleton embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors.
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


def embed_single(text: str) -> list[float]:
    """Generate embedding for a single text."""
    model = get_embedding_model()
    embedding = model.encode(text, show_progress_bar=False)
    return embedding.tolist()
