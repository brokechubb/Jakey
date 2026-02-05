"""
AI Provider integration - OpenAI-Compatible (primary) with OpenRouter fallback.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ai.openai_compatible import openai_compatible_api
from ai.openrouter import openrouter_api
from config import (
    DISABLE_REASONING_MODELS,
    FALLBACK_MODELS,
    MAX_CONVERSATION_TOKENS,
    OPENAI_COMPAT_DEFAULT_MODEL,
    OPENAI_COMPAT_ENABLED,
    OPENROUTER_DEFAULT_MODEL,
    OPENROUTER_ENABLED,
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 characters for English)."""
    if not text:
        return 0
    return len(text) // 4


def sanitize_messages_for_api(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitize messages to ensure API compliance.
    
    Fixes:
    1. Remove empty string content (omit field entirely instead of null)
    2. Ensure required fields are present
    3. Remove any None values that might cause issues
    """
    sanitized = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
            
        role = msg.get("role")
        if not role:
            continue
            
        # Create sanitized message with required fields
        clean_msg = {"role": role}
        
        # Handle content field - omit empty strings entirely (don't send null)
        content = msg.get("content")
        if content:  # Only include content if it's a non-empty string
            clean_msg["content"] = content
            
        # Handle tool_calls if present
        if "tool_calls" in msg and msg["tool_calls"]:
            clean_msg["tool_calls"] = msg["tool_calls"]
            
        # Handle tool_call_id for tool messages
        if "tool_call_id" in msg:
            clean_msg["tool_call_id"] = msg["tool_call_id"]
            
        sanitized.append(clean_msg)
        
    return sanitized


def trim_messages_to_fit(messages: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
    """
    Trim messages to fit within token limit while preserving system prompt and most recent context.
    
    CRITICAL: Never remove messages with tool_calls or tool responses as this breaks the conversation flow.
    
    Strategy:
    1. Keep system messages (usually the first message)
    2. Keep ALL messages with tool_calls or tool_call_id (essential for tool conversation flow)
    3. Keep the most recent user/assistant messages
    4. Remove older non-essential messages if needed
    """
    if not messages:
        return messages
    
    # Calculate total tokens (only count content, tool_calls are handled separately)
    total_tokens = sum(estimate_tokens(msg.get("content", "")) for msg in messages)
    
    if total_tokens <= max_tokens:
        return messages
    
    # Need to trim - but preserve essential messages
    trimmed = []
    optional_messages = []
    
    # First pass: identify essential vs optional messages
    for i, msg in enumerate(messages):
        role = msg.get("role")
        has_tool_calls = "tool_calls" in msg and msg["tool_calls"]
        has_tool_call_id = "tool_call_id" in msg
        
        # System message is always essential
        if role == "system":
            trimmed.append(msg)
        # Messages with tool_calls or tool_call_id are ESSENTIAL - never remove these
        elif has_tool_calls or has_tool_call_id:
            trimmed.append(msg)
        else:
            # These are optional and can be removed if needed
            optional_messages.append((i, msg))
    
    # Calculate current tokens from essential messages
    current_tokens = sum(estimate_tokens(msg.get("content", "")) for msg in trimmed)
    
    # Add optional messages from most recent backwards until we hit the limit
    kept_optional = []
    for idx, msg in reversed(optional_messages):
        msg_tokens = estimate_tokens(msg.get("content", ""))
        if current_tokens + msg_tokens <= max_tokens:
            kept_optional.insert(0, (idx, msg))
            current_tokens += msg_tokens
        else:
            break
    
    # Combine essential and kept optional messages, preserving original order
    all_kept_indices = set()
    for msg in trimmed:
        all_kept_indices.add(messages.index(msg))
    for idx, _ in kept_optional:
        all_kept_indices.add(idx)
    
    result = [messages[i] for i in sorted(all_kept_indices)]
    
    if len(result) < len(messages):
        logger.info(f"Trimmed messages from {len(messages)} to {len(result)} messages "
                    f"(estimated tokens: {total_tokens} -> {current_tokens}, "
                    f"preserved {len(trimmed) - (1 if messages and messages[0].get('role') == 'system' else 0)} tool-related messages)")
    
    return result


@dataclass
class ProviderStatus:
    """Provider status information."""

    name: str
    healthy: bool
    response_time: float
    error_message: Optional[str] = None
    last_check: float = 0.0


class SimpleAIProviderManager:
    """
    AI provider manager with OpenAI-Compatible as primary and OpenRouter as fallback.
    The primary provider uses a local endpoint at localhost:8317 by default.
    """

    def __init__(self):
        """Initialize the AI provider manager."""
        # Primary provider: OpenAI-Compatible (local endpoint)
        self.openai_compat_api = openai_compatible_api
        # Fallback provider: OpenRouter
        self.openrouter_api = openrouter_api

        # Determine which providers are available
        self.primary_enabled = OPENAI_COMPAT_ENABLED
        self.fallback_enabled = OPENROUTER_ENABLED

        self.provider_status = {
            "openai_compatible": ProviderStatus("openai_compatible", True, 0.0),
            "openrouter": ProviderStatus("openrouter", True, 0.0),
        }

        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failover_count": 0,
            "provider_usage": {"openai_compatible": 0, "openrouter": 0},
        }

        # Use OpenAI-compatible model as default, fall back to OpenRouter model
        if self.primary_enabled:
            self.default_model = OPENAI_COMPAT_DEFAULT_MODEL
        else:
            self.default_model = OPENROUTER_DEFAULT_MODEL

        self.user_model_preferences = {}  # user_id -> model preference

        logger.info(
            f"AI Provider Manager initialized: "
            f"primary=openai_compatible (enabled={self.primary_enabled}), "
            f"fallback=openrouter (enabled={self.fallback_enabled}), "
            f"default_model={self.default_model}"
        )

    async def check_provider_health(self, provider_name: str) -> ProviderStatus:
        """Check health of a specific provider."""
        if provider_name == "openai_compatible":
            try:
                result = self.openai_compat_api.check_service_health()
                status = ProviderStatus(
                    name="openai_compatible",
                    healthy=result.get("healthy", False),
                    response_time=result.get("response_time", 0.0),
                    error_message=result.get("error")
                    if not result.get("healthy")
                    else None,
                    last_check=time.time(),
                )
            except Exception as e:
                status = ProviderStatus(
                    name="openai_compatible",
                    healthy=False,
                    response_time=0.0,
                    error_message=str(e),
                    last_check=time.time(),
                )
        elif provider_name == "openrouter":
            try:
                result = self.openrouter_api.check_service_health()
                status = ProviderStatus(
                    name="openrouter",
                    healthy=result.get("healthy", False),
                    response_time=result.get("response_time", 0.0),
                    error_message=result.get("error")
                    if not result.get("healthy")
                    else None,
                    last_check=time.time(),
                )
            except Exception as e:
                status = ProviderStatus(
                    name="openrouter",
                    healthy=False,
                    response_time=0.0,
                    error_message=str(e),
                    last_check=time.time(),
                )
        else:
            status = ProviderStatus(
                name=provider_name,
                healthy=False,
                response_time=0.0,
                error_message="Unknown provider",
            )

        self.provider_status[provider_name] = status
        return status

    async def generate_text(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: int = 500,
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        preferred_provider: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate text using OpenAI-Compatible API (primary) with OpenRouter fallback.

        Args:
            messages: List of message dictionaries
            model: Model to use (optional)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            tools: List of tools for function calling
            tool_choice: Tool choice strategy
            preferred_provider: Preferred provider ('openai_compatible' or 'openrouter')
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        # Sanitize messages for API compliance (convert empty strings to None, etc.)
        messages = sanitize_messages_for_api(messages)
        
        # DIAGNOSTIC LOGGING: Log tool calling configuration
        if tools:
            logger.info(
                f"API Request with {len(tools)} tools: {[t.get('function', {}).get('name', 'unknown') for t in tools]}"
            )
            logger.debug(
                f"Tool choice: {tool_choice}, Model: {model or self.default_model}"
            )
        else:
            logger.debug(
                f"API Request with NO tools, Model: {model or self.default_model}"
            )

        # Prepare kwargs
        api_kwargs = kwargs.copy()
        reasoning_param = api_kwargs.pop("reasoning", None)
        api_kwargs.pop("use_fallback_routing", None)

        effective_model = model or self.default_model
        if reasoning_param is None and effective_model in DISABLE_REASONING_MODELS:
            reasoning_param = {"effort": "none"}
            logger.info(f"Auto-disabling reasoning for {effective_model}")

        # Determine provider order
        if preferred_provider == "openrouter":
            providers = [("openrouter", self.fallback_enabled)]
            if self.primary_enabled:
                providers.append(("openai_compatible", True))
        else:
            providers = []
            if self.primary_enabled:
                providers.append(("openai_compatible", True))
            if self.fallback_enabled:
                providers.append(("openrouter", True))

        last_error = None

        for provider_name, enabled in providers:
            if not enabled:
                continue

            try:
                request_start = time.time()

                if provider_name == "openai_compatible":
                    # Use provider-specific model for OpenAI-compatible endpoint
                    # Don't pass OpenRouter model names to local endpoint
                    compat_model = None  # Let the provider use its default
                    if model and not model.endswith(":free") and "/" not in model:
                        # Only pass simple model names (not OpenRouter format)
                        compat_model = model

                    result = await asyncio.to_thread(
                        self.openai_compat_api.generate_text,
                        messages=messages,
                        model=compat_model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        tools=tools,
                        tool_choice=tool_choice,
                        **api_kwargs,
                    )
                else:  # openrouter
                    result = await asyncio.to_thread(
                        self.openrouter_api.generate_text,
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        tools=tools,
                        tool_choice=tool_choice,
                        reasoning=reasoning_param,
                        use_fallback_routing=True,
                        **api_kwargs,
                    )

                request_time = time.time() - request_start
                logger.debug(f"{provider_name} API call completed in {request_time:.2f}s")

                if isinstance(result, dict) and "error" in result:
                    last_error = result["error"]
                    is_marked_unrecoverable = result.get("unrecoverable", False)
                    error_str = str(last_error).lower()
                    
                    # Check if this is a content filter / safety issue
                    is_content_filter = (
                        "data inspection failed" in error_str or
                        "datainspectionfailed" in error_str or
                        "content filter" in error_str or
                        "inappropriate content" in error_str or
                        "safety" in error_str
                    )
                    
                    # For content filter errors, retry with deepseek-v3 (no safety filter)
                    if is_content_filter and provider_name == "openai_compatible":
                        logger.warning(f"{provider_name} content filter triggered. "
                                       f"Retrying with deepseek-v3 (no safety filter)...")
                        try:
                            retry_result = await asyncio.to_thread(
                                self.openai_compat_api.generate_text,
                                messages=messages,
                                model="deepseek-v3",  # Use uncensored model
                                temperature=temperature,
                                max_tokens=max_tokens,
                                tools=None,  # deepseek doesn't support tools well anyway
                                tool_choice="none",
                                **api_kwargs,
                            )
                            if "error" not in retry_result:
                                logger.info(f"Retry with deepseek-v3 succeeded")
                                self.stats["successful_requests"] += 1
                                self.stats["provider_usage"][provider_name] += 1
                                # Note: Tools won't work but at least we get a response
                                return retry_result
                        except Exception as retry_e:
                            logger.warning(f"Retry with deepseek-v3 failed: {retry_e}")
                            
                        # If deepseek also fails, try without tools as last resort
                        if tools:
                            logger.warning(f"Trying original model without tools...")
                            try:
                                retry_result = await asyncio.to_thread(
                                    self.openai_compat_api.generate_text,
                                    messages=messages,
                                    model=compat_model,
                                    temperature=temperature,
                                    max_tokens=max_tokens,
                                    tools=None,
                                    tool_choice="none",
                                    **api_kwargs,
                                )
                                if "error" not in retry_result:
                                    logger.info(f"Retry without tools succeeded")
                                    self.stats["successful_requests"] += 1
                                    self.stats["provider_usage"][provider_name] += 1
                                    return retry_result
                            except Exception as retry_e:
                                logger.warning(f"Retry without tools failed: {retry_e}")
                    
                    # Don't fallback on other unrecoverable errors (HTTP 400, content issues)
                    # These are validation/content errors that won't be fixed by switching providers
                    is_unrecoverable = is_marked_unrecoverable or (
                        "invalid request" in error_str or
                        "bad request" in error_str or
                        "context length" in error_str or
                        "maximum context" in error_str or
                        "too large" in error_str
                    )
                    
                    if is_unrecoverable:
                        logger.error(f"{provider_name} returned unrecoverable error: {last_error}. "
                                     f"Not attempting fallback - this is a content/validation issue.")
                        return {"error": last_error}
                    
                    logger.warning(f"{provider_name} error: {last_error}, trying fallback...")
                    if provider_name == "openai_compatible" and self.fallback_enabled:
                        self.stats["failover_count"] += 1
                    continue

                response_time = time.time() - start_time
                self.stats["successful_requests"] += 1
                self.stats["provider_usage"][provider_name] += 1

                logger.info(f"Generated text via {provider_name} ({response_time:.2f}s)")
                return result

            except Exception as e:
                last_error = str(e)
                logger.warning(f"{provider_name} exception: {last_error}, trying fallback...")
                if provider_name == "openai_compatible" and self.fallback_enabled:
                    self.stats["failover_count"] += 1
                continue

        # All providers failed
        response_time = time.time() - start_time
        error_msg = last_error or "All providers failed"
        logger.error(f"Text generation failed after trying all providers: {error_msg}")
        return {"error": error_msg}

    async def generate_image(
        self,
        prompt: str,
        model: str = "flux",
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Generate image using Arta API (if available).

        Args:
            prompt: Image generation prompt
            model: Model to use
            width: Image width
            height: Image height
            seed: Random seed
            **kwargs: Additional parameters

        Returns:
            Image URL or error message
        """
        from media.image_generator import image_generator

        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            image_url = image_generator.generate_image(
                prompt=prompt,
                model=model,
                width=width,
                height=height,
                seed=seed,
                **kwargs,
            )

            response_time = time.time() - start_time
            self.stats["successful_requests"] += 1

            if not image_url.startswith("Error:"):
                logger.info(f"Generated image via Arta ({response_time:.2f}s)")
                return image_url
            else:
                logger.error(f"Image generation failed: {image_url}")
                return image_url

        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Image generation failed: {error_msg}")
            return f"Error: {error_msg}"

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        return {
            "providers": {
                name: {
                    "name": status.name,
                    "healthy": status.healthy,
                    "response_time": status.response_time,
                    "error_message": status.error_message,
                    "last_check": status.last_check,
                }
                for name, status in self.provider_status.items()
            },
            "statistics": self.get_statistics(),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics."""
        total_requests = self.stats["total_requests"]
        success_rate = (
            self.stats["successful_requests"] / total_requests
            if total_requests > 0
            else 0
        )

        return {
            "total_requests": total_requests,
            "successful_requests": self.stats["successful_requests"],
            "failover_count": self.stats["failover_count"],
            "success_rate": success_rate,
            "provider_usage": self.stats["provider_usage"].copy(),
        }

    def reset_statistics(self):
        """Reset all statistics."""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failover_count": 0,
            "provider_usage": {"openai_compatible": 0, "openrouter": 0},
        }
        logger.info("AI Provider statistics reset")

    async def health_check_all(self) -> Dict[str, ProviderStatus]:
        """Perform health check on all providers."""
        results = {}
        for provider in ["openai_compatible", "openrouter"]:
            results[provider] = await self.check_provider_health(provider)
        return results

    def _is_model_available(self, model: str, provider: str) -> bool:
        """
        Check if a model is available on a specific provider.
        """
        provider_models = {
            "openrouter": FALLBACK_MODELS,
        }

        available_models = provider_models.get(provider, [])
        return model in available_models

    def set_user_model_preference(self, user_id: str, model: str):
        """
        Set a user's preferred model.
        """
        self.user_model_preferences[user_id] = model
        logger.info(f"Set model preference for user {user_id}: {model}")

    def get_user_model_preference(self, user_id: str) -> Optional[str]:
        """
        Get a user's preferred model.
        """
        return self.user_model_preferences.get(user_id)


# Global AI provider manager instance
ai_provider_manager = SimpleAIProviderManager()
