"""
Optional LLM-based reranker (placeholder for future enhancement).
"""

import logging

logger = logging.getLogger(__name__)


def rerank_with_llm(query_text, results, top_k=5):
    """Use LLM to rerank search results (placeholder)."""
    if not results or len(results) <= 1:
        return results
    logger.info("LLM reranking: using default ranking (feature placeholder)")
    return results[:top_k]
