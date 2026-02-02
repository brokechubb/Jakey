"""
OpenAI-Compatible API Provider.

A lightweight provider for any OpenAI-compatible endpoint (LocalAI, Ollama, vLLM, etc.)
This is the default provider for Jakey, using a local endpoint at localhost:8317.
"""

import random
import threading
import time
from typing import Any, Dict, List, Optional, Union

import requests

from config import (
    OPENAI_COMPAT_API_KEY,
    OPENAI_COMPAT_API_URL,
    OPENAI_COMPAT_DEFAULT_MODEL,
    OPENAI_COMPAT_ENABLED,
    OPENAI_COMPAT_MODELS_URL,
    OPENAI_COMPAT_TIMEOUT,
    TEXT_API_RATE_LIMIT,
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


class OpenAICompatibleAPI:
    """
    OpenAI-Compatible API client for local or custom endpoints.

    Supports any API that follows the OpenAI chat completions format:
    - LocalAI
    - Ollama (with OpenAI compatibility layer)
    - vLLM
    - text-generation-webui
    - LM Studio
    - Any other OpenAI-compatible server
    """

    def __init__(self):
        self.api_key = OPENAI_COMPAT_API_KEY
        self.api_url = OPENAI_COMPAT_API_URL
        self.models_url = OPENAI_COMPAT_MODELS_URL
        self.default_model = OPENAI_COMPAT_DEFAULT_MODEL
        self.enabled = OPENAI_COMPAT_ENABLED
        self.timeout = OPENAI_COMPAT_TIMEOUT

        # Rate limiting
        self.rate_limit = min(TEXT_API_RATE_LIMIT, 60)
        self._requests = []
        self._rate_lock = threading.Lock()

        # Model cache
        self._models_cache = []
        self._models_cache_time = 0
        self._models_cache_duration = 300  # cache for 5 minutes

        logger.info(
            f"OpenAI-Compatible API initialized: enabled={self.enabled}, "
            f"url={self.api_url}, model={self.default_model}, timeout={self.timeout}s"
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for the API."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _is_rate_limited(self, current_time: float) -> bool:
        """Check if we're currently rate limited."""
        with self._rate_lock:
            self._requests[:] = [t for t in self._requests if current_time - t < 60]
            if len(self._requests) >= self.rate_limit:
                return True
            self._requests.append(current_time)
            return False

    def check_service_health(self) -> Dict[str, Any]:
        """Check if the API service is healthy."""
        if not self.enabled:
            return {
                "healthy": False,
                "status": "disabled",
                "error": "OpenAI-Compatible API is disabled",
            }

        try:
            response = requests.get(
                self.models_url,
                headers=self._get_headers(),
                timeout=10,
            )
            if response.status_code == 200:
                return {
                    "healthy": True,
                    "status": "ok",
                    "response_time": response.elapsed.total_seconds(),
                }
            elif response.status_code == 401:
                return {
                    "healthy": False,
                    "status": "unauthorized",
                    "error": "Invalid API key",
                }
            else:
                return {
                    "healthy": False,
                    "status": f"http_{response.status_code}",
                    "error": f"HTTP {response.status_code}",
                }
        except requests.exceptions.Timeout:
            return {"healthy": False, "status": "timeout", "error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return {
                "healthy": False,
                "status": "connection_error",
                "error": "Cannot connect to service",
            }
        except requests.exceptions.RequestException as e:
            return {"healthy": False, "status": "request_error", "error": str(e)}

    def list_models(self) -> List[str]:
        """List available models from the API."""
        if not self.enabled:
            return []

        current_time = time.time()

        # Return cached models if cache is still valid
        if (
            current_time - self._models_cache_time < self._models_cache_duration
            and self._models_cache
        ):
            return [model["id"] for model in self._models_cache]

        try:
            response = requests.get(
                self.models_url,
                headers=self._get_headers(),
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Cache the models
            self._models_cache = data.get("data", [])
            self._models_cache_time = current_time

            models = [model["id"] for model in self._models_cache]
            logger.info(f"OpenAI-Compatible: Retrieved {len(models)} models")
            return models

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI-Compatible: Failed to fetch models: {e}")
            return []

    def generate_text(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        repetition_penalty: Optional[float] = None,
        seed: Optional[int] = None,
        stop: Optional[Union[str, List[str]]] = None,
        response_format: Optional[Dict[str, str]] = None,
        user: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate text using the OpenAI-compatible API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model ID to use
            temperature: Creativity (0-2, default 0.7)
            max_tokens: Max response length
            tools: Function calling tools
            tool_choice: Tool selection mode ('auto', 'none', or specific)
            top_p: Nucleus sampling (0-1)
            top_k: Limit token choices (if supported)
            frequency_penalty: Reduce token repetition based on frequency
            presence_penalty: Reduce token repetition based on presence
            repetition_penalty: Reduce repetition (if supported)
            seed: For deterministic output
            stop: Stop sequences
            response_format: Force output format
            user: User identifier

        Returns:
            API response dictionary
        """
        if not self.enabled:
            return {"error": "OpenAI-Compatible API is disabled or not configured"}

        # Use default model if none specified
        if not model:
            model = self.default_model

        # Check rate limiting
        current_time = time.time()
        if self._is_rate_limited(current_time):
            return {
                "error": "Rate limit exceeded. Please try again later.",
                "rate_limited": True,
            }

        # Build request payload
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Add optional parameters (only if specified)
        if top_p is not None:
            payload["top_p"] = top_p
        if top_k is not None:
            payload["top_k"] = top_k
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty
        if repetition_penalty is not None:
            payload["repetition_penalty"] = repetition_penalty
        if seed is not None:
            payload["seed"] = seed
        if stop is not None:
            payload["stop"] = stop
        if response_format is not None:
            payload["response_format"] = response_format
        if user is not None:
            payload["user"] = user

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            if tool_choice:
                payload["tool_choice"] = tool_choice

        # Retry loop for transient errors
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                logger.debug(
                    f"OpenAI-Compatible: Request to {model} (attempt {attempt + 1}/{max_retries + 1})"
                )

                response = requests.post(
                    self.api_url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    result = response.json()

                    # Check for error in response body
                    if isinstance(result, dict) and "error" in result:
                        error_msg = result.get("error", "Unknown error")
                        if isinstance(error_msg, dict):
                            error_msg = error_msg.get("message", str(error_msg))
                        logger.error(f"OpenAI-Compatible: API error - {error_msg}")
                        return {"error": error_msg}
                    
                    # Log tool call information
                    if isinstance(result, dict) and "choices" in result:
                        choice = result.get("choices", [{}])[0]
                        message = choice.get("message", {})
                        has_tool_calls = "tool_calls" in message and message["tool_calls"]
                        if has_tool_calls:
                            tool_names = [tc.get("function", {}).get("name", "unknown") for tc in message["tool_calls"]]
                            logger.info(f"OpenAI-Compatible: Response includes {len(message['tool_calls'])} tool call(s): {tool_names}")
                        else:
                            logger.debug(f"OpenAI-Compatible: Response has NO tool calls (content only)")

                    logger.debug(f"OpenAI-Compatible: Successful response from {model}")
                    return result

                elif response.status_code == 401:
                    error_msg = "Invalid API key"
                    logger.error(f"OpenAI-Compatible: {error_msg}")
                    return {"error": error_msg}

                elif response.status_code == 429:
                    error_msg = "Rate limit exceeded"
                    if attempt < max_retries:
                        sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"OpenAI-Compatible: Rate limited. Retrying in {sleep_time:.2f}s..."
                        )
                        time.sleep(sleep_time)
                        continue
                    logger.error(f"OpenAI-Compatible: {error_msg} - Max retries reached")
                    return {"error": error_msg, "rate_limited": True}

                elif response.status_code in (500, 502, 503, 504):
                    error_msg = f"Server error (HTTP {response.status_code})"
                    if attempt < max_retries:
                        sleep_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"OpenAI-Compatible: {error_msg}. Retrying in {sleep_time:.2f}s..."
                        )
                        time.sleep(sleep_time)
                        continue
                    logger.error(f"OpenAI-Compatible: {error_msg} - Max retries reached")
                    return {"error": error_msg}

                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"OpenAI-Compatible: {error_msg}")
                    return {"error": error_msg}

            except requests.exceptions.Timeout:
                error_msg = "Request timeout"
                if attempt < max_retries:
                    logger.warning(f"OpenAI-Compatible: Timeout. Retrying...")
                    time.sleep(1)
                    continue
                logger.error(f"OpenAI-Compatible: {error_msg}")
                return {"error": error_msg}

            except requests.exceptions.ConnectionError:
                error_msg = f"Cannot connect to {self.api_url}"
                if attempt < max_retries:
                    sleep_time = retry_delay * (2 ** attempt)
                    logger.warning(
                        f"OpenAI-Compatible: Connection error. Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    continue
                logger.error(f"OpenAI-Compatible: {error_msg}")
                return {"error": error_msg}

            except requests.exceptions.RequestException as e:
                error_msg = f"Request error: {str(e)}"
                logger.error(f"OpenAI-Compatible: {error_msg}")
                return {"error": error_msg}

        return {"error": "Unknown error after retries"}

    def is_model_available(self, model: str) -> bool:
        """Check if a specific model is available."""
        if not self.enabled:
            return False

        try:
            models = self.list_models()
            return model in models
        except Exception as e:
            logger.error(f"OpenAI-Compatible: Error checking model availability: {e}")
            return False


# Create global instance
openai_compatible_api = OpenAICompatibleAPI()
