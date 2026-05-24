"""
Web scraper for legal websites.
Handles HTTP requests, HTML parsing, and rate limiting.
"""

import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from config.settings import settings
from crawler.utils import RateLimiter

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

_agent_index = 0


def _get_user_agent():
    """Rotate through user agents."""
    global _agent_index
    agent = USER_AGENTS[_agent_index % len(USER_AGENTS)]
    _agent_index += 1
    return agent


class Scraper:
    """Web scraper with rate limiting."""

    def __init__(self):
        self.rate_limiter = RateLimiter(min_interval=settings.CRAWL_RATE_LIMIT)
        self.timeout = settings.CRAWL_TIMEOUT
        self.session = requests.Session()

    def fetch_page(self, url):
        """Fetch a web page and return parsed BeautifulSoup object."""
        domain = urlparse(url).netloc
        self.rate_limiter.wait(domain)

        try:
            headers = {
                "User-Agent": _get_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            response = self.session.get(
                url, headers=headers, timeout=self.timeout, allow_redirects=True,
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            logger.info(f"Successfully fetched: {url}")
            return soup

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url}")
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error fetching {url}: {e}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error fetching {url}: {e}")

        return None

    def search_indian_kanoon(self, query, max_results=10):
        """
        Search Indian Kanoon and return a list of result dicts.

        Indian Kanoon HTML structure (2024+):
          - Results are in <div class="results-list">
          - Each result has a <a href="/docfragment/ID/..."> for title
          - <div class="headline"> for snippet text
          - <div class="hlbottom"> with <span class="docsource"> for court
          - <a href="/doc/ID/"> for full document link
        """
        search_url = f"https://indiankanoon.org/search/?formInput={requests.utils.quote(query)}"
        soup = self.fetch_page(search_url)

        if soup is None:
            logger.warning("Failed to fetch Indian Kanoon search results")
            return []

        results = []

        # Find the results list container
        results_list = soup.find("div", class_="results-list")
        if not results_list:
            logger.warning("No results-list div found on Indian Kanoon")
            return []

        # Parse results by iterating headline divs paired with their links
        # Structure: <a href="/docfragment/...">Title</a>
        #            <div class="headline">snippet text...</div>
        #            <div class="hlbottom"><span class="docsource">Court</span>...</div>

        headlines = results_list.find_all("div", class_="headline")

        for headline in headlines[:max_results]:
            try:
                # Title link: the docfragment <a> is the previous sibling
                doc_link = headline.find_previous_sibling(
                    "a", href=lambda h: h and "/docfragment/" in h
                )
                if not doc_link:
                    # Sometimes the link is a direct previous element
                    prev = headline.find_previous("a", href=lambda h: h and "/docfragment/" in h)
                    doc_link = prev

                if not doc_link:
                    continue

                title = doc_link.get_text(strip=True)
                if not title or len(title) < 5:
                    continue

                href = doc_link.get("href", "")

                # Extract doc ID for the full document URL
                doc_id = ""
                if "/docfragment/" in href:
                    parts = href.split("/docfragment/")[1].split("/")
                    doc_id = parts[0]

                full_url = f"https://indiankanoon.org/doc/{doc_id}/" if doc_id else ""

                # Skip duplicates
                if any(r["url"] == full_url for r in results):
                    continue

                # Snippet: text content of this headline div
                snippet = headline.get_text(strip=True)[:500]

                # Court: from the hlbottom div that follows this headline
                court = ""
                hlbottom = headline.find_next_sibling("div", class_="hlbottom")
                if hlbottom:
                    docsource = hlbottom.find("span", class_="docsource")
                    if docsource:
                        court = docsource.get_text(strip=True)

                results.append({
                    "url": full_url,
                    "title": title,
                    "snippet": snippet,
                    "court": court,
                })

            except Exception as e:
                logger.debug(f"Error parsing result: {e}")
                continue

        logger.info(f"Found {len(results)} results from Indian Kanoon for: {query}")
        return results
