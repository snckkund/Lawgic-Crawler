"""
FAISS Vector Store.
Manages FAISS index for efficient semantic similarity search.
Falls back to numpy cosine similarity if FAISS is not installed.
"""

import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Falling back to brute-force search.")


class VectorStore:
    """FAISS-based vector store with numpy fallback."""

    def __init__(self, dimension=384, index_path=None):
        self.dimension = dimension
        self.index_path = index_path
        self.texts = []
        self.metadata = []

        if FAISS_AVAILABLE:
            self.index = faiss.IndexFlatIP(dimension)
        else:
            self.embeddings = []

    def add(self, embeddings, texts=None, metadata=None):
        """Add embeddings to the index."""
        if hasattr(embeddings, 'cpu'):
            embeddings = embeddings.cpu().numpy()
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings)

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        embeddings = (embeddings / norms).astype('float32')

        if FAISS_AVAILABLE:
            self.index.add(embeddings)
        else:
            self.embeddings.extend(embeddings.tolist())

        if texts:
            self.texts.extend(texts)
        if metadata:
            self.metadata.extend(metadata)

    @property
    def size(self):
        if FAISS_AVAILABLE:
            return self.index.ntotal
        return len(self.embeddings)

    def search(self, query_embedding, top_k=5):
        """Search for the most similar embeddings."""
        if hasattr(query_embedding, 'cpu'):
            query_embedding = query_embedding.cpu().numpy()
        if isinstance(query_embedding, list):
            query_embedding = np.array(query_embedding)

        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        norm = np.linalg.norm(query_embedding)
        if norm > 0:
            query_embedding = query_embedding / norm
        query_embedding = query_embedding.astype('float32')

        if FAISS_AVAILABLE:
            scores, indices = self.index.search(query_embedding, min(top_k, self.size))
            scores = scores[0]
            indices = indices[0]
        else:
            emb_matrix = np.array(self.embeddings, dtype='float32')
            similarities = np.dot(emb_matrix, query_embedding.T).flatten()
            top_indices = np.argsort(similarities)[::-1][:top_k]
            indices = top_indices
            scores = similarities[top_indices]

        results = []
        for idx, score in zip(indices, scores):
            if idx < 0:
                continue
            results.append({
                "index": int(idx),
                "score": float(score),
                "text": self.texts[idx] if idx < len(self.texts) else "",
                "metadata": self.metadata[idx] if idx < len(self.metadata) else {},
            })

        return results
