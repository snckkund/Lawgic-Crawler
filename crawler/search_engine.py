"""
Search engine orchestrator.
Coordinates web crawling, parsing, and ranking to find similar legal cases.
"""

import logging
from config.settings import settings
from crawler.scraper import Scraper
from crawler.parser import parse_indian_kanoon_result
from crawler.ranking import rank_results
from crawler.utils import extract_keywords, extract_bns_sections

logger = logging.getLogger(__name__)


class SearchEngine:
    """Orchestrates legal case discovery across multiple sources."""

    def __init__(self):
        self.scraper = Scraper()
        self.max_results = settings.CRAWL_MAX_RESULTS

    def search(self, fir_text, bns_sections=None, keywords=None):
        """
        Search for similar legal cases based on FIR text and BNS sections.

        Args:
            fir_text: The FIR/case description text.
            bns_sections: List of recommended BNS section names (e.g., ["BNS Section 303"]).
            keywords: Optional pre-extracted keywords.

        Returns:
            list of CaseResult: Ranked list of similar cases.
        """
        if not settings.CRAWL_ENABLED:
            logger.info("Web crawling is disabled in settings")
            return []

        bns_sections = bns_sections or []
        keywords = keywords or extract_keywords(fir_text)

        logger.info(f"Starting legal case search. Keywords: {keywords[:5]}, Sections: {bns_sections[:3]}")

        all_results = []
        queries = self._build_queries(fir_text, bns_sections, keywords)

        for query in queries[:3]:
            try:
                logger.info(f"Searching Indian Kanoon: '{query}'")
                raw_results = self.scraper.search_indian_kanoon(
                    query, max_results=self.max_results
                )

                for raw in raw_results:
                    case = parse_indian_kanoon_result(raw)
                    if not any(r.source_url == case.source_url for r in all_results):
                        all_results.append(case)

            except Exception as e:
                logger.error(f"Search query '{query}' failed: {e}")
                continue

        if not all_results:
            logger.info("No results found from web crawling")
            return []

        section_numbers = []
        for sec in bns_sections:
            nums = extract_bns_sections(sec)
            section_numbers.extend(nums)

        ranked = rank_results(
            all_results,
            query_keywords=keywords,
            query_sections=section_numbers,
        )

        top_results = ranked[:self.max_results]
        logger.info(f"Returning {len(top_results)} ranked results")
        return top_results

    def _build_queries(self, fir_text, bns_sections, keywords):
        """
        Build effective search queries for Indian Kanoon.

        Strategy:
          1. Crime-specific keywords (best for finding similar cases)
          2. Section numbers as IPC equivalents (IPC is better indexed)
          3. Mixed: keywords + section reference
        """
        queries = []

        # Query 1: Top crime-specific keywords
        if keywords:
            crime_keywords = keywords[:6]
            queries.append(" ".join(crime_keywords))

        # Query 2: Section numbers — search with IPC equivalents
        # (Indian Kanoon has more IPC-era case law)
        if bns_sections:
            # Extract just the section numbers and search as IPC
            sec_nums = []
            for sec in bns_sections[:3]:
                nums = extract_bns_sections(sec)
                sec_nums.extend(nums)

            if sec_nums:
                queries.append("IPC Section " + " Section ".join(sec_nums[:3]))

        # Query 3: Keywords + a section reference
        if keywords and bns_sections:
            sec_nums = extract_bns_sections(bns_sections[0])
            sec_part = f"Section {sec_nums[0]}" if sec_nums else ""
            kw_part = " ".join(keywords[:3])
            if sec_part:
                queries.append(f"{kw_part} {sec_part}")
            else:
                queries.append(kw_part)

        # Fallback: use first chunk of the FIR text
        if not queries:
            # Take first meaningful sentence
            first_sentence = fir_text.split('.')[0][:100]
            queries.append(first_sentence)

        return queries
