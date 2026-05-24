"""
Legal document parser.
Extracts structured data from legal case pages.
"""

import re
import logging
from crawler.utils import clean_text, extract_bns_sections, truncate_text

logger = logging.getLogger(__name__)


class CaseResult:
    """Structured representation of a legal case result."""

    def __init__(self, title="", summary="", court="", date="",
                 sections=None, source_url="", source_name="",
                 similarity_score=0.0, authority_score=0.5):
        self.title = title
        self.summary = summary
        self.court = court
        self.date = date
        self.sections = sections or []
        self.source_url = source_url
        self.source_name = source_name
        self.similarity_score = similarity_score
        self.authority_score = authority_score

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            "case_title": self.title,
            "summary": self.summary,
            "court": self.court,
            "date": self.date,
            "sections": self.sections,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "similarity_score": round(self.similarity_score, 3),
            "authority_score": round(self.authority_score, 3),
        }

    def __repr__(self):
        return f"CaseResult(title='{self.title[:50]}...', score={self.similarity_score:.3f})"


def parse_indian_kanoon_result(search_result, soup=None):
    """Parse an Indian Kanoon search result into a CaseResult."""
    title = search_result.get("title", "Unknown Case")
    url = search_result.get("url", "")
    snippet = search_result.get("snippet", "")

    court = search_result.get("court", "") or _extract_court(title)
    date = _extract_date(title + " " + snippet)
    sections = extract_bns_sections(snippet)
    summary = truncate_text(clean_text(snippet), max_length=500)

    if soup is not None:
        full_text = _extract_case_text(soup)
        if full_text and len(full_text) > len(summary):
            summary = truncate_text(clean_text(full_text), max_length=500)
        page_sections = extract_bns_sections(full_text)
        if page_sections:
            sections = list(set(sections + page_sections))

    return CaseResult(
        title=title,
        summary=summary,
        court=court,
        date=date,
        sections=sections,
        source_url=url,
        source_name="Indian Kanoon",
        authority_score=_compute_authority_score(court),
    )


def _extract_court(text):
    """Extract court name from case title or text."""
    court_patterns = [
        (r"Supreme Court", "Supreme Court of India"),
        (r"High Court of (\w+(?:\s+\w+)?)", None),
        (r"(\w+)\s+High Court", None),
        (r"District Court", "District Court"),
        (r"Sessions Court", "Sessions Court"),
        (r"Tribunal", "Tribunal"),
    ]

    for pattern, fixed_name in court_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if fixed_name:
                return fixed_name
            return match.group(0)

    return "Unknown Court"


def _extract_date(text):
    """Extract date from text."""
    date_patterns = [
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{4}',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return ""


def _extract_case_text(soup):
    """Extract the main case text from an Indian Kanoon page."""
    judgment_div = soup.find("div", id="judgments")
    if judgment_div:
        return judgment_div.get_text(separator=" ", strip=True)
    content = soup.find("div", class_="judgments")
    if content:
        return content.get_text(separator=" ", strip=True)
    return ""


def _compute_authority_score(court):
    """Compute authority score based on court level."""
    court_lower = court.lower()
    if "supreme court" in court_lower:
        return 1.0
    elif "high court" in court_lower:
        return 0.8
    elif "tribunal" in court_lower:
        return 0.6
    elif "district" in court_lower or "sessions" in court_lower:
        return 0.5
    else:
        return 0.4
