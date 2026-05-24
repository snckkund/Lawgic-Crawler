"""
Crawler utility functions.
Rate limiting, robots.txt checking, and general helpers.
"""

import time
import hashlib
import re
import logging
from collections import Counter
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter to respect source rate limits."""

    def __init__(self, min_interval=1.0):
        self.min_interval = min_interval
        self._last_request_time = {}

    def wait(self, domain):
        """Wait if needed to respect rate limits for a domain."""
        now = time.time()
        last_time = self._last_request_time.get(domain, 0)
        elapsed = now - last_time

        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
            time.sleep(wait_time)

        self._last_request_time[domain] = time.time()


_robots_cache = {}


def check_robots_txt(url, user_agent="*"):
    """Check if a URL is allowed by robots.txt."""
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        if robots_url not in _robots_cache:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            _robots_cache[robots_url] = rp

        return _robots_cache[robots_url].can_fetch(user_agent, url)
    except Exception as e:
        logger.warning(f"Could not check robots.txt for {url}: {e}")
        return True


def clean_text(text):
    """Clean and normalize text content."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,;:!?\'\"()\-/]', '', text)
    return text.strip()


def extract_keywords(text, max_keywords=10):
    """Extract important keywords from text for search queries."""
    stop_words = {
        # Common English
        'the', 'a', 'an', 'is', 'was', 'were', 'are', 'been', 'be',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'shall', 'can', 'need',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
        'as', 'into', 'through', 'during', 'before', 'after', 'above',
        'below', 'between', 'under', 'and', 'but', 'or', 'nor', 'not',
        'so', 'yet', 'both', 'either', 'neither', 'each', 'every',
        'all', 'any', 'few', 'more', 'most', 'other', 'some', 'such',
        'no', 'only', 'same', 'than', 'too', 'very', 'just', 'because',
        'that', 'this', 'these', 'those', 'it', 'its', 'he', 'she',
        'they', 'them', 'his', 'her', 'their', 'my', 'your', 'our',
        'which', 'who', 'whom', 'what', 'when', 'where', 'how', 'if',
        'then', 'also', 'about', 'up', 'out', 'said', 'one', 'two',
        'being', 'upon', 'whether', 'within', 'without', 'against',
        'made', 'make', 'doing', 'done', 'case', 'cases',
        # Legal/statutory terms (too generic for search)
        'section', 'act', 'shall', 'person', 'whoever', 'thereof',
        'herein', 'hereinafter', 'provided', 'notwithstanding',
        'imprisonment', 'punished', 'punishable', 'offence', 'offences',
        'liable', 'extend', 'fine', 'convicted', 'conviction',
        'term', 'description', 'committed', 'commission', 'subject',
        'matter', 'provisions', 'provision', 'clause', 'sub',
        'government', 'state', 'central', 'chapter', 'india',
        'called', 'deemed', 'means', 'includes', 'purpose',
        'purposes', 'nothing', 'contained', 'accordance', 'respect',
        'order', 'prescribed', 'notification', 'gazette', 'force',
        'come', 'words', 'defined', 'referred', 'specified',
        'manner', 'excepted', 'exception', 'following', 'according',
        'part', 'parts', 'given', 'used', 'using',
    }

    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    keywords = [w for w in words if w not in stop_words]

    word_freq = Counter(keywords)
    return [word for word, _ in word_freq.most_common(max_keywords)]


def extract_bns_sections(text):
    """Extract BNS/IPC section references from text."""
    patterns = [
        r'BNS\s+(?:Section\s+)?(\d+)',
        r'Section\s+(\d+)\s+(?:of\s+)?BNS',
        r'IPC\s+(?:Section\s+)?(\d+)',
        r'Section\s+(\d+)\s+(?:of\s+)?IPC',
    ]
    sections = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        sections.update(matches)
    return sorted(sections)


def generate_hash(text):
    """Generate a hash for caching purposes."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def truncate_text(text, max_length=500):
    """Truncate text to a maximum length, adding ellipsis if needed."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + "..."
