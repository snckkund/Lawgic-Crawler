"""
Semantic similarity search interface.
Provides high-level functions for finding similar laws and cases.
"""

import logging
from retrieval.embedder import encode_text, encode_texts
from sentence_transformers import util

logger = logging.getLogger(__name__)


def find_similar_laws(query_text, law_embeddings, df, top_k=5):
    """Find similar laws using semantic search."""
    query_embedding = encode_text(query_text, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, law_embeddings, top_k=top_k)

    results = []
    for hit in hits[0]:
        idx = hit["corpus_id"]
        row = df.iloc[idx]
        results.append({
            "section": row["section"],
            "description": row["description"],
            "score": hit["score"],
        })

    return results


def find_similar_cases(query_text, case_results):
    """
    Compute embedding similarity between query text and crawled case results.

    Args:
        query_text: The FIR/case description text.
        case_results: List of CaseResult objects from the crawler.

    Returns:
        dict: Mapping of source_url -> similarity_score.
    """
    if not case_results:
        return {}

    query_embedding = encode_text(query_text, convert_to_tensor=True)

    case_texts = [r.summary for r in case_results if r.summary]
    if not case_texts:
        return {}

    case_embeddings = encode_texts(case_texts, convert_to_tensor=True)

    hits = util.semantic_search(query_embedding, case_embeddings, top_k=len(case_texts))

    similarity_map = {}
    for hit in hits[0]:
        idx = hit["corpus_id"]
        if idx < len(case_results):
            url = case_results[idx].source_url
            similarity_map[url] = hit["score"]

    return similarity_map
