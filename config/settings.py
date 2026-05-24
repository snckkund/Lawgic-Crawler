"""
LAWGIC Configuration Settings
Loads configuration from .env file with sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Central configuration for the LAWGIC application."""

    # ─── LLM Configuration ───
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # groq | gemini | openrouter | ollama
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
    LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2048"))

    # ─── Fallback LLM Providers ───
    # Comma-separated list of fallback providers (e.g., "gemini,openrouter")
    LLM_FALLBACK_PROVIDERS = os.getenv("LLM_FALLBACK_PROVIDERS", "")

    # Provider-specific keys (used by fallback logic)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

    # ─── Provider Presets ───
    PROVIDER_CONFIGS = {
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "default_model": "llama-3.3-70b-versatile",
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "default_model": "gemini-2.0-flash",
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "default_model": "meta-llama/llama-3.3-70b-instruct",
        },
        "ollama": {
            "base_url": "http://localhost:11434/v1",
            "default_model": "llama3",
        },
    }

    # ─── Embedding Model ───
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ─── Database ───
    DATABASE_PATH = os.getenv("DATABASE_PATH", "lawgic.db")

    # ─── Crawling ───
    CRAWL_ENABLED = os.getenv("CRAWL_ENABLED", "true").lower() == "true"
    CRAWL_RATE_LIMIT = float(os.getenv("CRAWL_RATE_LIMIT", "1.0"))  # seconds between requests
    CRAWL_MAX_RESULTS = int(os.getenv("CRAWL_MAX_RESULTS", "10"))
    CRAWL_TIMEOUT = int(os.getenv("CRAWL_TIMEOUT", "15"))

    # ─── Caching ───
    CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_LLM_TTL = int(os.getenv("CACHE_LLM_TTL", "3600"))  # 1 hour
    CACHE_CRAWL_TTL = int(os.getenv("CACHE_CRAWL_TTL", "86400"))  # 24 hours

    # ─── OCR ───
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")

    # ─── Flask ───
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5050"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "lawgic-secret-key-change-in-production")

    @classmethod
    def get_provider_config(cls, provider=None):
        """Get configuration for a specific LLM provider."""
        provider = provider or cls.LLM_PROVIDER
        config = cls.PROVIDER_CONFIGS.get(provider, {})
        return {
            "base_url": config.get("base_url", cls.LLM_BASE_URL),
            "default_model": config.get("default_model", cls.LLM_MODEL),
        }

    @classmethod
    def get_api_key(cls, provider=None):
        """Get the API key for a specific provider."""
        provider = provider or cls.LLM_PROVIDER
        provider_key_map = {
            "groq": cls.GROQ_API_KEY or cls.LLM_API_KEY,
            "gemini": cls.GEMINI_API_KEY or cls.LLM_API_KEY,
            "openrouter": cls.OPENROUTER_API_KEY or cls.LLM_API_KEY,
            "ollama": cls.LLM_API_KEY or "ollama",  # Ollama doesn't need a key
        }
        return provider_key_map.get(provider, cls.LLM_API_KEY)

    @classmethod
    def get_fallback_providers(cls):
        """Get ordered list of fallback providers."""
        if not cls.LLM_FALLBACK_PROVIDERS:
            return []
        return [p.strip() for p in cls.LLM_FALLBACK_PROVIDERS.split(",") if p.strip()]


# Singleton instance
settings = Settings()
