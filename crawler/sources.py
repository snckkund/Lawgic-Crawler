"""
Legal source definitions for web crawling.
Defines the legal databases and websites to search.
"""


class LegalSource:
    """Represents a legal information source."""

    def __init__(self, name, base_url, search_url_template, source_type, authority_score=0.5):
        self.name = name
        self.base_url = base_url
        self.search_url_template = search_url_template
        self.source_type = source_type
        self.authority_score = authority_score

    def get_search_url(self, query):
        """Build a search URL for the given query."""
        return self.search_url_template.format(query=query)


# ─── Predefined Legal Sources ───

INDIAN_KANOON = LegalSource(
    name="Indian Kanoon",
    base_url="https://indiankanoon.org",
    search_url_template="https://indiankanoon.org/search/?formInput={query}",
    source_type="case_law",
    authority_score=0.9,
)

# ─── Source Registry ───

ALL_SOURCES = [INDIAN_KANOON]
DEFAULT_SOURCES = [INDIAN_KANOON]


def get_source_by_name(name):
    """Get a source by its name."""
    for source in ALL_SOURCES:
        if source.name.lower() == name.lower():
            return source
    return None
