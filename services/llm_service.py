"""
LAWGIC LLM Service
Cloud-hosted LLM API client with provider switching, fallback, and retry logic.
Supports OpenAI-compatible APIs (Groq, Gemini, OpenRouter) and Ollama native API.
"""

import time
import logging
import requests
from config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Cloud LLM API client with fallback and retry support."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.timeout = settings.LLM_TIMEOUT
        self.max_retries = settings.LLM_MAX_RETRIES
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    def _build_headers(self, api_key):
        """Build request headers for the API call."""
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(self, prompt, model):
        """Build the request payload in OpenAI-compatible format."""
        return {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a senior Indian Criminal Court Judge and legal expert. "
                        "You strictly follow Bharatiya Nyaya Sanhita (BNS), 2023. "
                        "Provide accurate, structured legal analysis."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def _call_api(self, prompt, provider=None):
        """
        Make a single API call to the specified provider.
        Returns the response text or raises an exception.
        """
        provider = provider or self.provider
        config = settings.get_provider_config(provider)
        api_key = settings.get_api_key(provider)
        model = settings.LLM_MODEL or config["default_model"]
        base_url = settings.LLM_BASE_URL or config["base_url"]

        logger.info(f"Calling LLM provider: {provider} | model: {model}")

        # ── Ollama uses its native /api/chat endpoint ──
        if provider == "ollama":
            url = f"{base_url}/api/chat"
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a senior Indian Criminal Court Judge and legal expert. "
                            "You strictly follow Bharatiya Nyaya Sanhita (BNS), 2023. "
                            "Provide accurate, structured legal analysis."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                },
            }
            headers = {"Content-Type": "application/json"}

            response = requests.post(
                url, json=payload, headers=headers, timeout=120,
            )
            response.raise_for_status()

            data = response.json()
            return data["message"]["content"]

        # ── OpenAI-compatible endpoint (Groq, Gemini, OpenRouter) ──
        else:
            url = f"{base_url}/chat/completions"
            headers = self._build_headers(api_key)
            payload = self._build_payload(prompt, model)

            response = requests.post(
                url, json=payload, headers=headers, timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

    def generate(self, prompt):
        """
        Generate a response from the LLM with retry and fallback logic.

        Retry flow:
        1. Try primary provider with exponential backoff
        2. If all retries fail, try each fallback provider in order
        3. If everything fails, return an error message

        Args:
            prompt: The text prompt to send to the LLM.

        Returns:
            str: The generated response text.
        """
        # ── Try primary provider with retries ──
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._call_api(prompt)
            except requests.exceptions.Timeout:
                logger.warning(
                    f"Timeout on attempt {attempt}/{self.max_retries} "
                    f"with provider {self.provider}"
                )
                last_error = "Request timed out"
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else "unknown"
                logger.warning(
                    f"HTTP {status} on attempt {attempt}/{self.max_retries} "
                    f"with provider {self.provider}: {e}"
                )
                last_error = f"HTTP error {status}"
                # Don't retry on 4xx client errors (except 429 rate limit)
                if e.response is not None and 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    break
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request error on attempt {attempt}/{self.max_retries} "
                    f"with provider {self.provider}: {e}"
                )
                last_error = str(e)
            except (KeyError, IndexError) as e:
                logger.error(f"Unexpected response format from {self.provider}: {e}")
                last_error = f"Invalid response format: {e}"
                break

            # Exponential backoff: 1s, 2s, 4s...
            if attempt < self.max_retries:
                wait_time = 2 ** (attempt - 1)
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

        # ── Try fallback providers ──
        fallback_providers = settings.get_fallback_providers()
        for fallback in fallback_providers:
            if fallback == self.provider:
                continue  # Skip the primary (already tried)
            logger.info(f"Attempting fallback provider: {fallback}")
            try:
                return self._call_api(prompt, provider=fallback)
            except Exception as e:
                logger.warning(f"Fallback provider {fallback} failed: {e}")
                last_error = str(e)

        # ── All providers failed ──
        error_msg = (
            f"⚠️ LLM Service Error: All providers failed.\n"
            f"Last error: {last_error}\n\n"
            f"Please check your API key and provider configuration in .env file.\n"
            f"Current provider: {self.provider}"
        )
        logger.error(error_msg)
        return error_msg


# ── Backward-compatible function (drop-in replacement for call_local_llm) ──
_llm_service = None


def get_llm_service():
    """Get or create the singleton LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def call_cloud_llm(prompt):
    """
    Drop-in replacement for the old call_local_llm() function.
    Uses cloud-hosted LLM API instead of local Ollama.
    """
    service = get_llm_service()
    return service.generate(prompt)
