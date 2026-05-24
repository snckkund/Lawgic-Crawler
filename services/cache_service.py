"""
SQLite-based caching service.
Caches LLM responses and crawl results to avoid redundant work.
"""

import json
import time
import logging
import sqlite3
from crawler.utils import generate_hash
from config.settings import settings

logger = logging.getLogger(__name__)


class CacheService:
    """SQLite-backed cache for LLM responses and crawl results."""

    def __init__(self, db_path=None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.enabled = settings.CACHE_ENABLED
        self._init_tables()

    def _init_tables(self):
        """Create cache tables if they don't exist."""
        if not self.enabled:
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS llm_cache (
                    prompt_hash TEXT PRIMARY KEY,
                    response TEXT NOT NULL,
                    provider TEXT,
                    created_at REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawl_cache (
                    query_hash TEXT PRIMARY KEY,
                    response TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize cache tables: {e}")

    def get_llm_response(self, prompt):
        """Get a cached LLM response if available and not expired."""
        if not self.enabled:
            return None
        prompt_hash = generate_hash(prompt)
        ttl = settings.CACHE_LLM_TTL
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT response, created_at FROM llm_cache WHERE prompt_hash = ?",
                (prompt_hash,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                response, created_at = row
                if time.time() - created_at < ttl:
                    logger.info("LLM cache hit")
                    return response
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        return None

    def set_llm_response(self, prompt, response, provider=""):
        """Cache an LLM response."""
        if not self.enabled:
            return
        prompt_hash = generate_hash(prompt)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO llm_cache (prompt_hash, response, provider, created_at) "
                "VALUES (?, ?, ?, ?)",
                (prompt_hash, response, provider, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Cache write error: {e}")

    def get_crawl_results(self, query):
        """Get cached crawl results if available and not expired."""
        if not self.enabled:
            return None
        query_hash = generate_hash(query)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT response, expires_at FROM crawl_cache WHERE query_hash = ?",
                (query_hash,)
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                response, expires_at = row
                if time.time() < expires_at:
                    logger.info("Crawl cache hit")
                    return json.loads(response)
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        return None

    def set_crawl_results(self, query, results):
        """Cache crawl results."""
        if not self.enabled:
            return
        query_hash = generate_hash(query)
        ttl = settings.CACHE_CRAWL_TTL
        try:
            serializable = []
            for r in results:
                if hasattr(r, 'to_dict'):
                    serializable.append(r.to_dict())
                elif isinstance(r, dict):
                    serializable.append(r)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO crawl_cache (query_hash, response, created_at, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (query_hash, json.dumps(serializable), time.time(), time.time() + ttl)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Cache write error: {e}")


_cache = None


def get_cache():
    """Get or create the singleton cache instance."""
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
