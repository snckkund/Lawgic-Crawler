"""
Search result ranking module.
Scores and ranks legal case results using weighted criteria.
"""

import logging

logger = logging.getLogger(__name__)


def compute_keyword_score(case_summary, keywords):
    """Compute keyword overlap score."""
    if not keywords or not case_summary:
        return 0.0
    summary_lower = case_summary.lower()
    matches = sum(1 for kw in keywords if kw.lower() in summary_lower)
    return min(matches / max(len(keywords), 1), 1.0)


def compute_section_overlap(case_sections, query_sections):
    """Compute overlap between case sections and query sections."""
    if not case_sections or not query_sections:
        return 0.0
    case_set = set(str(s) for s in case_sections)
    query_set = set(str(s) for s in query_sections)
    intersection = case_set & query_set
    if not query_set:
        return 0.0
    return len(intersection) / len(query_set)


def rank_results(results, query_keywords=None, query_sections=None,
                 embedding_scores=None):
    """
    Rank case results using weighted scoring formula.

    Formula:
        final_score = 0.5 * embedding_similarity +
                      0.2 * keyword_match +
                      0.2 * section_overlap +
                      0.1 * source_authority
    """
    query_keywords = query_keywords or []
    query_sections = query_sections or []
    embedding_scores = embedding_scores or {}

    for result in results:
        emb_score = embedding_scores.get(result.source_url, result.similarity_score)
        kw_score = compute_keyword_score(result.summary, query_keywords)
        sec_score = compute_section_overlap(result.sections, query_sections)
        auth_score = result.authority_score

        final_score = (
            0.5 * emb_score +
            0.2 * kw_score +
            0.2 * sec_score +
            0.1 * auth_score
        )

        result.similarity_score = final_score

    results.sort(key=lambda r: r.similarity_score, reverse=True)
    return results
