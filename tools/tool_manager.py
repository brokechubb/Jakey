import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import pytz
import requests
import yfinance as yf

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import COINMARKETCAP_API_KEY, MCP_MEMORY_ENABLED, SEARXNG_URL

from .discord_tools import DiscordTools

logger = logging.getLogger(__name__)

# Import rate limiter
try:
    from .rate_limiter import rate_limit_middleware

    RATE_LIMITING_ENABLED = True
except ImportError:
    logger.warning("Rate limiter not available, using fallback rate limiting")
    RATE_LIMITING_ENABLED = False


class ToolManager:
    def __init__(self):
        # Create a session for connection pooling (reuses TCP connections)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

        self.tools = {
            "set_reminder": self.set_reminder,
            "list_reminders": self.list_reminders,
            "cancel_reminder": self.cancel_reminder,
            "check_due_reminders": self.check_due_reminders,
            "remember_user_info": self.remember_user_info,
            "search_user_memory": self.search_user_memory,
            "get_crypto_price": self.get_crypto_price,
            "get_stock_price": self.get_stock_price,
            "tip_user": self.tip_user,
            "check_balance": self.check_balance,
            "get_bonus_schedule": self.get_bonus_schedule,
            "web_search": self.web_search,
            "company_research": self.company_research,
            "crawling": self.crawling,
            "generate_image": self.generate_image,
            "analyze_image": self.analyze_image,
            "calculate": self.calculate,
            "get_current_time": self.get_current_time,
            "remember_user_mcp": self.remember_user_mcp,
            "generate_keno_numbers": self.generate_keno_numbers,
            # Trivia tools
            "play_trivia": self.play_trivia,
            # Discord tools
            "discord_get_user_info": self.discord_get_user_info,
            "discord_list_guilds": self.discord_list_guilds,
            "discord_list_channels": self.discord_list_channels,
            "discord_read_channel": self.discord_read_channel,
            "discord_search_messages": self.discord_search_messages,
            "discord_list_guild_members": self.discord_list_guild_members,
            "discord_send_message": self.discord_send_message,
            "discord_send_dm": self.discord_send_dm,
            "discord_get_user_roles": self.discord_get_user_roles,
            # Discord Moderation Tools
            "discord_kick_user": self.discord_kick_user,
            "discord_ban_user": self.discord_ban_user,
            "discord_unban_user": self.discord_unban_user,
            "discord_timeout_user": self.discord_timeout_user,
            "discord_remove_timeout": self.discord_remove_timeout,
            "discord_purge_messages": self.discord_purge_messages,
            "discord_pin_message": self.discord_pin_message,
            "discord_unpin_message": self.discord_unpin_message,
            "discord_delete_message": self.discord_delete_message,
            # Rate limiting tools
            "get_user_rate_limit_status": self.get_user_rate_limit_status,
            "get_system_rate_limit_stats": self.get_system_rate_limit_stats,
            "reset_user_rate_limits": self.reset_user_rate_limits,
            # FatTips tools
            "fattips_get_balance": self.fattips_get_balance,
            "fattips_send_tip": self.fattips_send_tip,
            "fattips_send_batch_tip": self.fattips_send_batch_tip,
            "fattips_create_airdrop": self.fattips_create_airdrop,
            "fattips_claim_airdrop": self.fattips_claim_airdrop,
            "fattips_list_airdrops": self.fattips_list_airdrops,
            "fattips_create_rain": self.fattips_create_rain,
            "fattips_get_wallet": self.fattips_get_wallet,
            "fattips_create_wallet": self.fattips_create_wallet,
            "fattips_get_transactions": self.fattips_get_transactions,
            "fattips_withdraw": self.fattips_withdraw,
            "fattips_get_swap_quote": self.fattips_get_swap_quote,
            "fattips_execute_swap": self.fattips_execute_swap,
            "fattips_get_leaderboard": self.fattips_get_leaderboard,
        }

        # Initialize Discord tools - will be set later by main.py after bot initialization
        self.discord_tools = None

        # Initialize trivia games dictionary at startup for proper answer detection
        self._trivia_games = {}  # channel_id -> game_state

        # Define corrected bonus schedules for different sites
        self.bonus_schedules = {
            "stake_weekly": "Saturday 12:30 PM UTC",
            "stake_monthly": "Around the 15th of each month (varies by VIP)",
            "bitsler_daily": "Every 24 hours after last claim",
            "bitsler_weekly": "Sunday 12:00 AM UTC (approximate, may vary)",
            "bitsler_monthly": "First day of month 12:00 AM UTC",
            "freebitco.in_daily": "12:00 AM UTC",
            "freebitco.in_weekly": "Sunday 12:00 AM UTC",
            "freebitco.in_monthly": "First day of month 12:00 AM UTC",
            "freebitco.in_hourly": "Every hour",
            "fortunejack_daily": "12:00 AM UTC",
            "fortunejack_weekly": "Sunday 12:00 AM UTC",
            "fortunejack_monthly": "First day of month 12:00 AM UTC",
            "bc.game_daily": "Once every 24 hours (local reset varies)",
            "bc.game_weekly": "Sunday 12:00 AM UTC",
            "bc.game_monthly": "End of month 12:00 AM UTC",
            "roobet_daily": "12:00 AM UTC",
            "roobet_weekly": "Weekly raffle (time not fixed)",
            "roobet_monthly": "Monthly cashback (time not fixed)",
            "vave_daily": "12:00 AM UTC",
            "vave_weekly": "Sunday 12:00 AM UTC",
            "vave_monthly": "First day of month 12:00 AM UTC",
            "spinz.io_daily": "12:00 AM UTC",
            "spinz.io_weekly": "Sunday 12:00 AM UTC",
            "spinz.io_monthly": "First day of month 12:00 AM UTC",
            "blazebet_daily": "12:00 AM UTC",
            "blazebet_weekly": "Sunday 12:00 AM UTC",
            "blazebet_monthly": "First day of month 12:00 AM UTC",
            "duelbits_daily": "12:00 AM UTC",
            "duelbits_weekly": "Sunday 12:00 AM UTC",
            "duelbits_monthly": "First day of month 12:00 AM UTC",
            "bets.io_daily": "12:00 AM UTC",
            "bets.io_weekly": "Sunday 12:00 AM UTC",
            "bets.io_monthly": "First day of month 12:00 AM UTC",
            "clash.bet_daily": "12:00 AM UTC",
            "clash.bet_weekly": "Sunday 12:00 AM UTC",
            "clash.bet_monthly": "First day of month 12:00 AM UTC",
            "stake.us_weekly": "Saturday 12:30 PM UTC",
            "stake.us_monthly": "Around the 15th of each month (varies by VIP)",
            "shuffle_weekly": "Thursday 11:00 AM UTC",
            "shuffle_monthly": "First Friday 12:00 AM UTC",
        }

        # Add rate limiting for tools
        self.last_call_time = {}
        self.rate_limits = {
            "crypto_price": 1.0,  # 1 second between calls
            "stock_price": 1.0,  # 1 second between calls
            "tip_user": 1.0,  # 1 second between calls
            "check_balance": 1.0,  # 1 second between calls
            "get_bonus_schedule": 1.0,  # 1 second between calls
            "web_search": 2.0,  # 2 seconds between calls
            "company_research": 2.0,  # 2 seconds between calls
            "crawling": 2.0,  # 2 seconds between calls
            "generate_image": 5.0,  # 5 seconds between calls
            "analyze_image": 5.0,  # 5 seconds between calls
            "calculate": 0.1,  # 0.1 seconds between calls
            "get_current_time": 0.1,  # 0.1 seconds between calls
            "set_reminder": 1.0,  # 1 second between calls
            "list_reminders": 1.0,  # 1 second between calls
            "cancel_reminder": 1.0,  # 1 second between calls
            "check_due_reminders": 5.0,  # 5 seconds between calls (background task)
            "remember_user_info": 1.0,  # 1 second between calls
            "remember_user_mcp": 1.0,  # 1 second between calls
            "search_user_memory": 0.1,  # 0.1 seconds between calls
            # Trivia tool rate limits
            "play_trivia": 3.0,  # 3 seconds between calls
            # Discord tool rate limits
            "discord_get_user_info": 1.0,
            "discord_list_guilds": 1.0,
            "discord_list_channels": 1.0,
            "discord_read_channel": 1.0,
            "discord_search_messages": 1.0,
            "discord_list_guild_members": 1.0,
            "discord_send_message": 1.0,
            "discord_send_dm": 1.0,
            # Discord Moderation rate limits
            "discord_kick_user": 2.0,
            "discord_ban_user": 2.0,
            "discord_unban_user": 2.0,
            "discord_timeout_user": 2.0,
            "discord_remove_timeout": 2.0,
            "discord_purge_messages": 5.0,  # Higher rate limit for bulk delete
            "discord_pin_message": 2.0,
            "discord_unpin_message": 2.0,
            "discord_delete_message": 2.0,
        }

        # Initialize trivia games dictionary to track active games
        # Maps channel_id to game state dictionary with question, category, start_time, attempts
        self._trivia_games = {}

    def _validate_crypto_symbol(self, symbol: str) -> bool:
        """Validate cryptocurrency symbol using security framework."""
        try:
            # Import here to avoid circular imports
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent))
            from utils.security_validator import validator

            is_valid, _ = validator.validate_cryptocurrency_symbol(symbol)
            return is_valid
        except ImportError:
            # Fallback to basic validation if security validator not available
            import re

            return bool(re.match(r"^[A-Z0-9]{1,10}$", symbol.upper()))

    def _validate_currency_code(self, currency: str) -> bool:
        """Validate currency code using security framework."""
        try:
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent))
            from utils.security_validator import validator

            is_valid, _ = validator.validate_currency_code(currency)
            return is_valid
        except ImportError:
            # Fallback validation
            import re

            return bool(re.match(r"^[A-Z]{3}$", currency.upper()))

    def _validate_search_query(self, query: str) -> bool:
        """Validate search query using security framework."""
        try:
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent))
            from utils.security_validator import validator

            is_valid, _ = validator.validate_search_query(query)
            return is_valid
        except ImportError:
            # Fallback validation
            return bool(query and len(query.strip()) <= 1000 and "\x00" not in query)

    def _check_rate_limit(self, tool_name: str, user_id: str = "system") -> bool:
        """Check if tool can be called based on per-user rate limits"""
        # Check per-user rate limits first if available
        if RATE_LIMITING_ENABLED:
            try:
                is_allowed, violation_reason = rate_limit_middleware.check_request(
                    user_id, tool_name
                )
                if not is_allowed:
                    logger.warning(
                        f"Rate limit violation for user {user_id}: {violation_reason}"
                    )
                    return False
            except Exception as e:
                logger.error(f"Error checking per-user rate limit: {e}")
                # Fall back to global rate limiting on error

        # Fall back to global rate limits for backward compatibility
        current_time = time.time()
        if tool_name in self.last_call_time:
            time_since_last_call = current_time - self.last_call_time[tool_name]
            if time_since_last_call < self.rate_limits.get(tool_name, 1.0):
                return False
        self.last_call_time[tool_name] = current_time
        return True

    def get_available_tools(self) -> List[Dict]:
        """Return the list of available tools in OpenAI function calling format"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "set_reminder",
                    "description": "Set a reminder, alarm, or timer for a specific time",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID who owns the reminder",
                            },
                            "reminder_type": {
                                "type": "string",
                                "description": "Type of reminder: 'alarm', 'timer', or 'reminder'",
                                "enum": ["alarm", "timer", "reminder"],
                            },
                            "title": {
                                "type": "string",
                                "description": "Title of the reminder",
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed description of what the reminder is about",
                            },
                            "trigger_time": {
                                "type": "string",
                                "description": "ISO 8601 formatted time when the reminder should trigger (e.g., '2025-10-03T15:00:00Z')",
                            },
                            "channel_id": {
                                "type": "string",
                                "description": "Optional Discord channel ID to send reminder to",
                            },
                            "recurring_pattern": {
                                "type": "string",
                                "description": "Optional recurring pattern (daily, weekly, monthly)",
                            },
                        },
                        "required": [
                            "user_id",
                            "reminder_type",
                            "title",
                            "description",
                            "trigger_time",
                        ],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_reminders",
                    "description": "List all pending reminders for a user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID whose reminders to list",
                            }
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "cancel_reminder",
                    "description": "Cancel a specific reminder by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID who owns the reminder",
                            },
                            "reminder_id": {
                                "type": "integer",
                                "description": "ID of the reminder to cancel",
                            },
                        },
                        "required": ["user_id", "reminder_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_due_reminders",
                    "description": "Check for any due reminders (used by background tasks)",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "remember_user_info",
                    "description": "Remember important information about a user for future reference",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID",
                            },
                            "information_type": {
                                "type": "string",
                                "description": "Type of information to remember (e.g., preference, fact, habit)",
                            },
                            "information": {
                                "type": "string",
                                "description": "The actual information to remember",
                            },
                        },
                        "required": ["user_id", "information_type", "information"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_user_memory",
                    "description": "Search for previously remembered information about a user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID",
                            },
                            "query": {
                                "type": "string",
                                "description": "Search query to find relevant memories",
                            },
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_crypto_price",
                    "description": "Get current price of a cryptocurrency in a specific currency",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Cryptocurrency symbol (e.g., BTC, ETH, DOGE)",
                            },
                            "currency": {
                                "type": "string",
                                "description": "Currency to convert to (e.g., USD, EUR, GBP)",
                                "default": "USD",
                            },
                        },
                        "required": ["symbol"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "description": "Get current price of a stock",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "Stock symbol (e.g., AAPL, GOOGL, TSLA)",
                            }
                        },
                        "required": ["symbol"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "tip_user",
                    "description": "Tip another user through tip.cc",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID of the recipient",
                            },
                            "amount": {
                                "type": "string",
                                "description": "Amount to tip (e.g., '100' or '5.5')",
                            },
                            "currency": {
                                "type": "string",
                                "description": "Currency to tip in (e.g., 'DOGE', 'BTC', 'USD')",
                                "default": "DOGE",
                            },
                            "message": {
                                "type": "string",
                                "description": "Optional message to include with the tip",
                            },
                        },
                        "required": ["user_id", "amount"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "check_balance",
                    "description": "Check user's tip.cc balance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID",
                            }
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_bonus_schedule",
                    "description": "Get bonus schedule information for gambling sites",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "site": {
                                "type": "string",
                                "description": "Gambling site name (e.g., 'stake', 'bitsler', 'freebitco.in')",
                            },
                            "frequency": {
                                "type": "string",
                                "description": "Bonus frequency (daily, weekly, monthly, hourly)",
                                "enum": ["daily", "weekly", "monthly", "hourly"],
                            },
                        },
                        "required": ["site", "frequency"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Performs real-time web searches using public SearXNG instances with multiple search engines",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "company_research",
                    "description": "Comprehensive company research using public SearXNG instances with multiple search engines",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "company_name": {
                                "type": "string",
                                "description": "Name of the company to research",
                            }
                        },
                        "required": ["company_name"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "crawling",
                    "description": "Extracts content from specific URLs using direct web scraping",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL to crawl"},
                            "max_characters": {
                                "type": "integer",
                                "description": "Maximum number of characters to extract",
                                "default": 3000,
                            },
                        },
                        "required": ["url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_image",
                    "description": "Generate an image using Arta API with artistic styles and aspect ratios",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "Image generation prompt",
                            },
                            "model": {
                                "type": "string",
                                "description": "Model to use for generation",
                                "default": "SDXL 1.0",
                            },
                            "width": {
                                "type": "integer",
                                "description": "Image width in pixels (converted to aspect ratio)",
                                "default": 1024,
                            },
                            "height": {
                                "type": "integer",
                                "description": "Image height in pixels (converted to aspect ratio)",
                                "default": 1024,
                            },
                        },
                        "required": ["prompt"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_image",
                    "description": "Analyze an image using Pollinations API vision capabilities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image_url": {
                                "type": "string",
                                "description": "URL of the image to analyze",
                            },
                            "prompt": {
                                "type": "string",
                                "description": "Prompt for image analysis",
                                "default": "Describe this image",
                            },
                        },
                        "required": ["image_url"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Perform mathematical calculations and comparisons",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Mathematical expression to calculate (supports basic operations +, -, *, / and comparisons >, <, >=, <=, ==, !=)",
                            }
                        },
                        "required": ["expression"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get current time and date information for any timezone worldwide",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "description": "Timezone name or alias (e.g., 'UTC', 'EST', 'US/Eastern', 'Europe/London')",
                                "default": "UTC",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "remember_user_mcp",
                    "description": "Remember user information using MCP memory server with enhanced capabilities",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID",
                            },
                            "information_type": {
                                "type": "string",
                                "description": "Type of information (e.g. 'preference', 'fact', 'reminder')",
                            },
                            "information": {
                                "type": "string",
                                "description": "The information to remember",
                            },
                        },
                        "required": ["user_id", "information_type", "information"],
                    },
                },
            },
            # Discord tools
            {
                "type": "function",
                "function": {
                    "name": "discord_get_user_info",
                    "description": "Get information about the currently logged-in Discord user",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_list_guilds",
                    "description": "List all Discord servers/guilds the user is in",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_list_channels",
                    "description": "List channels the user has access to, optionally filtered by guild",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "guild_id": {
                                "type": "string",
                                "description": "Optional: Filter channels by guild ID",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_read_channel",
                    "description": "Read messages from a specific Discord channel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "The Discord channel ID to read messages from. Use 'current' to read from the channel where the user sent the message.",
                            },
                            "limit": {
                                "type": "number",
                                "description": "Number of messages to fetch (default: 50, max: 100)",
                            },
                        },
                        "required": ["channel_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_search_messages",
                    "description": "Search for messages in a Discord channel by content, author, or date range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "The Discord channel ID to search messages in. Use 'current' for the channel where the user sent the message.",
                            },
                            "query": {
                                "type": "string",
                                "description": "Text to search for in message content",
                            },
                            "author_id": {
                                "type": "string",
                                "description": "Optional: Filter by author ID",
                            },
                            "limit": {
                                "type": "number",
                                "description": "Number of messages to search through (default: 100, max: 500)",
                            },
                        },
                        "required": ["channel_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_list_guild_members",
                    "description": "List members of a specific Discord guild/server",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "guild_id": {
                                "type": "string",
                                "description": "The Discord guild ID to list members from",
                            },
                            "limit": {
                                "type": "number",
                                "description": "Number of members to fetch (default: 100, max: 1000)",
                            },
                            "include_roles": {
                                "type": "boolean",
                                "description": "Whether to include role information for each member",
                            },
                        },
                        "required": ["guild_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_get_user_roles",
                    "description": "Get roles for the currently logged-in user in a specific Discord guild",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "guild_id": {
                                "type": "string",
                                "description": "The Discord guild ID to get user roles from",
                            },
                        },
                        "required": ["guild_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_send_message",
                    "description": "Send a message to a Discord text channel. ONLY use for server/guild channels, NEVER for DMs. Use 'current' for the current channel.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "The Discord channel ID to send the message to. Use 'current' for the channel where the user sent the message. WARNING: Do NOT use DM channel IDs - use discord_send_dm instead.",
                            },
                            "content": {
                                "type": "string",
                                "description": "The message content to send",
                            },
                            "reply_to_message_id": {
                                "type": "string",
                                "description": "Optional: Message ID to reply to",
                            },
                        },
                        "required": ["channel_id", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_send_dm",
                    "description": "Send a direct message to a Discord user. Use ONLY for DMs, NEVER for server channels. Has a 10-second cooldown between messages.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "The Discord user ID (snowflake) to send the DM to. NOTE: This is NOT a channel ID. Must be a user ID.",
                            },
                            "content": {
                                "type": "string",
                                "description": "The message content to send. Keep it concise since there's a cooldown.",
                            },
                        },
                        "required": ["user_id", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_kick_user",
                    "description": "Kick a user from a specific Discord guild",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "guild_id": {
                                "type": "string",
                                "description": "The Discord guild ID where the user is",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "The Discord user ID to kick",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for kicking the user",
                            },
                        },
                        "required": ["guild_id", "user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_ban_user",
                    "description": "Ban a user from a specific Discord guild",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "guild_id": {
                                "type": "string",
                                "description": "The Discord guild ID where to ban the user",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "The Discord user ID to ban",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for banning the user",
                            },
                            "delete_message_seconds": {
                                "type": "integer",
                                "description": "Number of seconds to delete messages for (0-604800)",
                                "default": 0,
                            },
                        },
                        "required": ["guild_id", "user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_unban_user",
                    "description": "Unban a user from a specific Discord guild",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "guild_id": {
                                "type": "string",
                                "description": "The Discord guild ID where to unban the user",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "The Discord user ID to unban",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for unbanning the user",
                            },
                        },
                        "required": ["guild_id", "user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_timeout_user",
                    "description": "Timeout/mute a user for a specific duration",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "guild_id": {
                                "type": "string",
                                "description": "The Discord guild ID where the user is",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "The Discord user ID to timeout",
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "description": "Duration of timeout in minutes (0 to remove timeout)",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for the timeout",
                            },
                        },
                        "required": ["guild_id", "user_id", "duration_minutes"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_remove_timeout",
                    "description": "Remove timeout from a user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "guild_id": {
                                "type": "string",
                                "description": "The Discord guild ID where the user is",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "The Discord user ID to remove timeout from",
                            },
                            "reason": {
                                "type": "string",
                                "description": "Reason for removing the timeout",
                            },
                        },
                        "required": ["guild_id", "user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_purge_messages",
                    "description": "Purge/delete multiple messages from a channel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "The Discord channel ID to purge messages from",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of messages to delete (max 100)",
                                "default": 10,
                            },
                            "user_id": {
                                "type": "string",
                                "description": "Optional: Only delete messages from this user",
                            },
                        },
                        "required": ["channel_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_pin_message",
                    "description": "Pin a specific message in a channel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "The Discord channel ID",
                            },
                            "message_id": {
                                "type": "string",
                                "description": "The ID of the message to pin",
                            },
                        },
                        "required": ["channel_id", "message_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_unpin_message",
                    "description": "Unpin a specific message in a channel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "The Discord channel ID",
                            },
                            "message_id": {
                                "type": "string",
                                "description": "The ID of the message to unpin",
                            },
                        },
                        "required": ["channel_id", "message_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "discord_delete_message",
                    "description": "Delete a single user message from a channel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "The Discord channel ID where the message is",
                            },
                            "message_id": {
                                "type": "string",
                                "description": "The ID of the message to delete",
                            },
                        },
                        "required": ["channel_id", "message_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_user_rate_limit_status",
                    "description": "Get rate limiting status and statistics for a specific user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID to check rate limit status for",
                            }
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_system_rate_limit_stats",
                    "description": "Get overall system rate limiting statistics and metrics",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_keno_numbers",
                    "description": "Generate random Keno numbers (1-10 numbers from 1-40) with 8x5 visual board",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "count": {
                                "type": "integer",
                                "description": "Optional number between 1-10 specifying how many numbers to generate",
                                "minimum": 1,
                                "maximum": 10,
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "play_trivia",
                    "description": "Start an interactive trivia game in the current channel. This creates an engaging trivia question that users in the chat can answer. The AI should wait for user responses and check answers.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "channel_id": {
                                "type": "string",
                                "description": "Discord channel ID where to post the trivia question",
                            },
                            "category": {
                                "type": "string",
                                "description": "Optional trivia category. IMPORTANT: Use %triviacats command first to see available categories before specifying one. If not provided, a random category will be selected automatically.",
                            },
                            "difficulty": {
                                "type": "integer",
                                "description": "Optional difficulty level (1=easy, 2=medium, 3=hard). Defaults to mixed difficulty.",
                                "enum": [1, 2, 3],
                            },
                        },
                        "required": ["channel_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "reset_user_rate_limits",
                    "description": "Reset rate limits and penalties for a specific user (admin function)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID to reset rate limits for",
                            }
                        },
                        "required": ["user_id"],
                    },
                },
            },
            # FatTips Tools
            {
                "type": "function",
                "function": {
                    "name": "fattips_get_balance",
                    "description": "Get a user's FatTips wallet balance including SOL, USDC, and USDT",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID to check balance for",
                            }
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_send_tip",
                    "description": "Send a Solana token tip to another user using FatTips",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_user_id": {
                                "type": "string",
                                "description": "Discord user ID of the sender (Jakey's ID)",
                            },
                            "to_user_id": {
                                "type": "string",
                                "description": "Discord user ID of the recipient",
                            },
                            "amount": {
                                "type": "number",
                                "description": "Amount to tip",
                            },
                            "token": {
                                "type": "string",
                                "description": "Token to tip in (SOL, USDC, USDT)",
                                "default": "SOL",
                            },
                            "amount_type": {
                                "type": "string",
                                "description": "Whether amount is in tokens or USD",
                                "enum": ["token", "usd"],
                                "default": "token",
                            },
                        },
                        "required": ["from_user_id", "to_user_id", "amount"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_send_batch_tip",
                    "description": "Send tips to multiple users at once (Rain) using FatTips",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_user_id": {
                                "type": "string",
                                "description": "Discord user ID of the sender",
                            },
                            "recipients": {
                                "type": "array",
                                "description": "List of Discord user IDs to receive tips",
                                "items": {"type": "string"},
                            },
                            "total_amount": {
                                "type": "number",
                                "description": "Total amount to distribute among all recipients",
                            },
                            "token": {
                                "type": "string",
                                "description": "Token to tip in",
                                "default": "SOL",
                            },
                            "amount_type": {
                                "type": "string",
                                "description": "Whether amount is in tokens or USD",
                                "enum": ["token", "usd"],
                                "default": "token",
                            },
                        },
                        "required": ["from_user_id", "recipients", "total_amount"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_create_airdrop",
                    "description": "Create a FatTips airdrop that multiple users can claim. If channel_id is provided, the FatTips bot will automatically post a message with a claim button in that channel.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "creator_id": {
                                "type": "string",
                                "description": "Discord user ID creating the airdrop",
                            },
                            "amount": {
                                "type": "number",
                                "description": "Total amount for the airdrop pot",
                            },
                            "token": {
                                "type": "string",
                                "description": "Token to airdrop (SOL, USDC, USDT)",
                            },
                            "duration": {
                                "type": "string",
                                "description": "Duration string like '10m', '1h', '30s'",
                            },
                            "max_winners": {
                                "type": "integer",
                                "description": "Maximum number of winners allowed",
                            },
                            "amount_type": {
                                "type": "string",
                                "description": "Whether amount is in tokens or USD",
                                "enum": ["token", "usd"],
                                "default": "token",
                            },
                            "channel_id": {
                                "type": "string",
                                "description": "Discord channel ID where the FatTips bot should post the airdrop message with claim button (optional but recommended)",
                            },
                        },
                        "required": ["creator_id", "amount", "token", "duration", "max_winners"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_claim_airdrop",
                    "description": "Claim a FatTips airdrop",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "airdrop_id": {
                                "type": "string",
                                "description": "ID of the airdrop to claim",
                            },
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID claiming the airdrop",
                            },
                        },
                        "required": ["airdrop_id", "user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_list_airdrops",
                    "description": "List available FatTips airdrops",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "Filter by status",
                                "enum": ["ACTIVE", "EXPIRED", "SETTLED", "RECLAIMED"],
                                "default": "ACTIVE",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 10,
                            },
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_create_rain",
                    "description": "Create a FatTips rain to specific winners (like trivia winners)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "creator_id": {
                                "type": "string",
                                "description": "Discord user ID creating the rain",
                            },
                            "amount": {
                                "type": "number",
                                "description": "Total amount to rain",
                            },
                            "token": {
                                "type": "string",
                                "description": "Token to rain",
                                "default": "SOL",
                            },
                            "winners": {
                                "type": "array",
                                "description": "List of Discord user IDs who receive the rain",
                                "items": {"type": "string"},
                            },
                            "amount_type": {
                                "type": "string",
                                "description": "Whether amount is in tokens or USD",
                                "enum": ["token", "usd"],
                                "default": "token",
                            },
                        },
                        "required": ["creator_id", "amount", "winners"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_get_wallet",
                    "description": "Get a user's FatTips wallet information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID",
                            }
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_create_wallet",
                    "description": "Create a new FatTips wallet for a user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID",
                            }
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_get_transactions",
                    "description": "Get a user's FatTips transaction history",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of transactions to retrieve",
                                "default": 5,
                            },
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_withdraw",
                    "description": "Withdraw FatTips funds to an external Solana wallet",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID",
                            },
                            "destination_address": {
                                "type": "string",
                                "description": "External Solana wallet address",
                            },
                            "amount": {
                                "type": ["number", "null"],
                                "description": "Amount to withdraw (null for max/all)",
                            },
                            "token": {
                                "type": "string",
                                "description": "Token to withdraw",
                                "default": "SOL",
                            },
                        },
                        "required": ["user_id", "destination_address"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_get_swap_quote",
                    "description": "Get a quote for swapping tokens using FatTips",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "input_token": {
                                "type": "string",
                                "description": "Token to swap from (e.g., SOL)",
                            },
                            "output_token": {
                                "type": "string",
                                "description": "Token to swap to (e.g., USDC)",
                            },
                            "amount": {
                                "type": "number",
                                "description": "Amount to swap",
                            },
                            "amount_type": {
                                "type": "string",
                                "description": "Whether amount is in tokens or USD",
                                "enum": ["token", "usd"],
                                "default": "token",
                            },
                        },
                        "required": ["input_token", "output_token", "amount"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_execute_swap",
                    "description": "Execute a token swap using FatTips",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Discord user ID",
                            },
                            "input_token": {
                                "type": "string",
                                "description": "Token to swap from",
                            },
                            "output_token": {
                                "type": "string",
                                "description": "Token to swap to",
                            },
                            "amount": {
                                "type": "number",
                                "description": "Amount to swap",
                            },
                            "amount_type": {
                                "type": "string",
                                "description": "Whether amount is in tokens or USD",
                                "enum": ["token", "usd"],
                                "default": "token",
                            },
                            "slippage": {
                                "type": "number",
                                "description": "Maximum slippage percentage",
                                "default": 1.0,
                            },
                        },
                        "required": ["user_id", "input_token", "output_token", "amount"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "fattips_get_leaderboard",
                    "description": "Get FatTips leaderboard showing top tippers or receivers",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "description": "Leaderboard type",
                                "enum": ["tippers", "receivers"],
                                "default": "tippers",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of entries to show",
                                "default": 10,
                            },
                        },
                    },
                },
            },
        ]

    def remember_user_info(
        self, user_id: str, information_type: str, information: str
    ) -> str:
        """Remember important information about a user with rate limiting"""
        if not self._check_rate_limit("remember_user_info", user_id):
            return (
                "Rate limit exceeded. Please wait before remembering more information."
            )

        try:
            # Check if unified memory backend is enabled (migration complete)
            migration_flag = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), ".memory_migration_complete"
            )
            if os.path.exists(migration_flag):
                try:
                    # Dynamic import to avoid circular dependencies
                    import importlib

                    memory_module = importlib.import_module("memory")
                    memory_backend = memory_module.memory_backend

                    if memory_backend is not None:
                        # Use unified memory backend
                        import asyncio

                        async def _store_memory():
                            success = await memory_backend.store(
                                user_id, information_type, information
                            )
                            return success

                        # Run the async operation
                        try:
                            loop = asyncio.get_running_loop()
                            import concurrent.futures

                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, _store_memory())
                                success = future.result()
                        except RuntimeError:
                            success = asyncio.run(_store_memory())

                        if success:
                            return f"Got it! I'll remember that {information_type}: {information}"
                        else:
                            return (
                                "Sorry, I couldn't remember that information right now."
                            )
                except (ImportError, AttributeError) as e:
                    # Log but don't fail - fall back to legacy system
                    import logging

                    logging.getLogger(__name__).warning(
                        f"Unified memory backend unavailable: {e}"
                    )

            # Fallback to direct database access (legacy system)
            from data.database import db

            key = f"{information_type}"
            db.add_memory(user_id, key, information)

            return f"Got it! I'll remember that {information_type}: {information}"
        except Exception as e:
            return f"Error remembering information: {str(e)}"

        except Exception as e:
            return f"Error remembering information: {str(e)}"

    def remember_user_mcp(
        self, user_id: str, information_type: str, information: str
    ) -> str:
        """Remember user information using MCP memory server with rate limiting and fallback"""
        if not self._check_rate_limit("remember_user_mcp", user_id):
            return (
                "Rate limit exceeded. Please wait before remembering more information."
            )

        if not MCP_MEMORY_ENABLED:
            # Fallback to SQLite when MCP is disabled
            return self.remember_user_info(user_id, information_type, information)

        try:
            # Create the async function to run the operation
            async def _run_with_context():
                async with MCPMemoryClient() as client:
                    if not await client.check_connection():
                        return {"error": "MCP memory server not accessible"}
                    return await client.remember_user_info(
                        user_id, information_type, information
                    )

            # Check if there's already a running event loop
            try:
                loop = asyncio.get_running_loop()
                # If there's a running loop, create a task and wait for it
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_with_context())
                    result = future.result()
            except RuntimeError:
                # No running event loop, safe to run directly
                result = asyncio.run(_run_with_context())

            if "error" in result:
                # Fallback to SQLite when MCP fails
                fallback_result = self.remember_user_info(
                    user_id, information_type, information
                )
                return f"MCP memory unavailable, using local storage: {fallback_result}"

            return f"Got it! I'll remember that {information_type}: {information} (stored in MCP memory)"
        except Exception as e:
            # Fallback to SQLite when MCP fails
            try:
                fallback_result = self.remember_user_info(
                    user_id, information_type, information
                )
                return f"MCP memory error ({str(e)}), using local storage: {fallback_result}"
            except Exception as fallback_error:
                return f"Both MCP and local storage failed: MCP: {str(e)}, Local: {str(fallback_error)}"

    def search_user_memory(self, user_id: str, query: str = "") -> str:
        """Search user memories with rate limiting - Uses SQLite as single source"""
        if not self._check_rate_limit("search_user_memory", user_id):
            return "Rate limit exceeded. Please wait before searching memories."

        # Import asyncio here to avoid issues
        import asyncio
        import concurrent.futures

        try:
            # Dynamic import to avoid circular dependencies
            import importlib

            memory_module = importlib.import_module("memory")
            memory_backend = memory_module.memory_backend

            if memory_backend is None:
                return "Memory backend not available."

            # Use unified memory backend (SQLite)
            async def _search_memory():
                results = await memory_backend.search(
                    user_id, query or None, limit=10
                )
                return results

            # Run the async operation
            try:
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _search_memory())
                    results = future.result()
            except RuntimeError:
                results = asyncio.run(_search_memory())

            if not results:
                return f"No memories found for user {user_id}."

            # Format the results
            formatted_memories = []
            for entry in results[:10]:  # Show up to 10 results
                # Extract memory type from key
                key_parts = entry.key.split('_', 2)
                if len(key_parts) >= 2:
                    mem_type = key_parts[0]
                    category = key_parts[1] if len(key_parts) > 1 else ""
                    label = f"{mem_type}/{category}" if category else mem_type
                else:
                    label = entry.key
                
                # Truncate long values
                value = entry.value
                if len(value) > 100:
                    value = value[:97] + "..."
                
                formatted_memories.append(f"• [{label}] {value}")

            return (
                f"Found {len(results)} memories for user {user_id}:\n"
                + "\n".join(formatted_memories)
            )
        except (ImportError, AttributeError) as e:
            logger.error(f"Memory backend error: {e}")
            return f"Memory search error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected memory search error: {e}")
            return f"Error searching memories: {str(e)}"

    def get_crypto_price(
        self, symbol: str, currency: str = "USD", user_id: str = "system"
    ) -> str:
        """Get cryptocurrency price from CoinMarketCap API with rate limiting"""
        if not self._check_rate_limit("crypto_price", user_id):
            return "Rate limit exceeded. Please wait before checking another price."

        # Check if API key is available
        if not COINMARKETCAP_API_KEY:
            return "CoinMarketCap API key not configured. Cannot fetch crypto prices."

        # VALIDATE inputs to prevent injection attacks
        if not self._validate_crypto_symbol(symbol):
            return f"Invalid cryptocurrency symbol: {symbol}"

        if not self._validate_currency_code(currency):
            return f"Invalid currency code: {currency}"

        try:
            # Use CoinMarketCap API
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            parameters = {"symbol": symbol.upper(), "convert": currency.upper()}
            headers = {
                "Accepts": "application/json",
                "X-CMC_PRO_API_KEY": COINMARKETCAP_API_KEY,
            }

            response = self.session.get(
                url, headers=headers, params=parameters, timeout=10
            )
            response.raise_for_status()
            data = response.json()

            # Parse the response
            if data.get("status", {}).get("error_code", 0) == 0:
                crypto_data = data["data"][symbol.upper()]
                price = crypto_data["quote"][currency.upper()]["price"]
                volume_24h = crypto_data["quote"][currency.upper()]["volume_24h"]
                market_cap = crypto_data["quote"][currency.upper()]["market_cap"]

                return f"Current {symbol.upper()} price: ${price:.6f} {currency.upper()}\n24h Volume: ${volume_24h:,.2f}\nMarket Cap: ${market_cap:,.2f}"
            else:
                error_message = data.get("status", {}).get(
                    "error_message", "Unknown error"
                )
                return f"Error getting crypto price: {error_message}"

        except requests.exceptions.RequestException as e:
            return f"Network error getting crypto price: {str(e)}"
        except KeyError as e:
            return f"Data format error: {str(e)}"
        except Exception as e:
            return f"Error getting crypto price: {str(e)}"

    def get_stock_price(self, symbol: str) -> str:
        """Get stock price using yfinance with rate limiting"""
        if not self._check_rate_limit("stock_price"):
            return "Rate limit exceeded. Please wait before checking another stock."

        try:
            stock = yf.Ticker(symbol)
            info = stock.info

            # Try to get current price
            if "currentPrice" in info:
                price = info["currentPrice"]
            elif "regularMarketPrice" in info:
                price = info["regularMarketPrice"]
            else:
                return f"Could not get price for {symbol}"

            return f"Current {symbol} price: ${price:.2f}"
        except Exception as e:
            return f"Error getting stock price for {symbol}: {str(e)}"

    def tip_user(
        self, user_id: str, amount: str, currency: str = "USD", message: str = ""
    ) -> str:
        """Tip a user through tip.cc with rate limiting and validation"""
        if not self._check_rate_limit("tip_user"):
            return "Rate limit exceeded. Please wait before tipping again."

        try:
            # Validate tip parameters using security framework
            try:
                import sys
                from pathlib import Path

                sys.path.insert(0, str(Path(__file__).parent.parent))
                from utils.security_validator import validator

                is_valid, error = validator.validate_tip_command(
                    f"<@{user_id}>", amount, currency, message
                )
                if not is_valid:
                    return f"Validation error: {error}"
            except ImportError:
                # Fallback validation
                if not user_id or not user_id.strip():
                    return "Invalid user ID"
                if not amount or not amount.strip():
                    return "Invalid amount"

            # Format the tip command safely
            recipient = f"<@{user_id.strip()}>"
            amount_safe = amount.strip()
            currency_safe = currency.upper().strip()
            message_safe = message.strip() if message else ""

            tip_command = f"$tip {recipient} {amount_safe} {currency_safe}"
            if message_safe:
                tip_command += f" {message_safe}"
            return f"Tip command prepared: {tip_command}\nPlease use this command in a channel where the tip.cc bot is active."

        except Exception as e:
            return f"Error preparing tip: {str(e)}"

    def check_balance(self, user_id: str) -> str:
        """Check balance through tip.cc with rate limiting"""
        if not self._check_rate_limit("check_balance"):
            return (
                "Rate limit exceeded. Please wait before checking your balance again."
            )

        try:
            # Format the balance command
            balance_command = "$balance"
            return f"Balance command prepared: {balance_command}\nPlease use this command in a channel where the tip.cc bot is active."

        except Exception as e:
            return f"Error preparing balance check: {str(e)}"

    def get_bonus_schedule(self, site: str, frequency: str) -> str:
        """Get bonus schedule information with rate limiting"""
        if not self._check_rate_limit("get_bonus_schedule"):
            return "Rate limit exceeded. Please wait before checking another schedule."

        # Convert to lowercase to ensure case-insensitive matching
        key = f"{site.lower()}_{frequency.lower()}"
        if key in self.bonus_schedules:
            return f"{site.title()} {frequency} bonus: {self.bonus_schedules[key]}"
        else:
            return f"No schedule found for {site} {frequency} bonus"

    def web_search(self, query: str) -> str:
        """Perform real-time web searches using local SearXNG instance with AI guidance"""
        if not self._check_rate_limit("web_search"):
            return "Rate limit exceeded. Please wait before making another search."

        # VALIDATE query to prevent injection attacks
        if not self._validate_search_query(query):
            return "Invalid search query. Please check your input and try again."

        # Use only localhost SearXNG instance for efficiency
        instance = "http://localhost:8086"

        try:
            logger.debug(f"web_search query: {query}")
            search_url = urljoin(instance, "search")

            # Prepare search parameters for SearXNG
            params = {
                "q": query,
                "format": "json",
                "categories": "general",
                "engines": "google,bing,duckduckgo,brave",
                "language": "en-US",
            }

            response = self.session.get(search_url, params=params, timeout=10)

            # Check if we got a successful response
            if response.status_code == 200:
                try:
                    data = response.json()

                    # Parse and format results
                    if "results" in data and data["results"]:
                        results = []
                        for result in data["results"][:7]:  # Limit to top 7 results
                            title = result.get("title", "No title")
                            content = result.get("content", "")
                            if len(content) > 300:
                                content = content[:300] + "..."
                            # Don't include URLs - AI guidance says not to cite them
                            results.append(f"• {title}: {content}")

                        logger.info(
                            f"web_search success: {len(data['results'])} results for '{query[:50]}'"
                        )

                        # Add a strong system instruction to the results
                        search_output = "\n".join(results)
                        return (
                            f"SEARCH RESULTS FOR '{query}':\n{search_output}\n\n"
                            "SYSTEM INSTRUCTION: SUMMARIZE THESE RESULTS IN 1-4 SENTENCES. "
                            "DO NOT LIST THEM. DO NOT RAMBLE. JUST GIVE THE ANSWER."
                        )
                    else:
                        logger.info(f"web_search no results for: {query}")
                        return f"No search results found for '{query}'."
                except ValueError:
                    logger.warning(f"web_search JSON decode failed")
                    return f"Error parsing search results for '{query}'."
            else:
                logger.warning(f"web_search HTTP {response.status_code}")
                return f"Search service returned error {response.status_code}. Try again later."

        except requests.exceptions.Timeout:
            logger.warning(f"web_search timeout")
            return "Search timed out. Please try again."
        except requests.exceptions.ConnectionError:
            logger.error(
                f"web_search connection error - is SearXNG running on localhost:8086?"
            )
            return "Search service unavailable. Please try again later."
        except requests.exceptions.RequestException as e:
            logger.warning(f"web_search request error: {e}")
            return "Search request failed. Please try again."
        except Exception as e:
            logger.error(f"web_search unexpected error: {e}")
            return "An error occurred during search. Please try again."

    def company_research(self, company_name: str) -> str:
        """Comprehensive company research tool using local SearXNG instance"""
        if not self._check_rate_limit("company_research"):
            return "Rate limit exceeded. Please wait before making another search."

        # Use only localhost SearXNG instance for efficiency
        instance = "http://localhost:8086"

        try:
            search_url = urljoin(instance, "search")

            # Prepare search parameters for company research
            params = {
                "q": f"company {company_name}",
                "format": "json",
                "categories": "general",
                "engines": "google,bing,duckduckgo,brave",
                "language": "en-US",
            }

            response = self.session.get(search_url, params=params, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()

                    if "results" in data and data["results"]:
                        results = []
                        for result in data["results"][:7]:
                            title = result.get("title", "No title")
                            content = result.get("content", "")
                            if len(content) > 300:
                                content = content[:300] + "..."
                            url = result.get("url", "")
                            results.append(f"• {title}: {content} ({url})")

                        logger.info(
                            f"company_research success: {len(data['results'])} results for '{company_name}'"
                        )
                        return "\n".join(results)
                    else:
                        return f"No company information found for '{company_name}'."
                except ValueError:
                    return (
                        f"Error parsing company research results for '{company_name}'."
                    )
            else:
                return f"Search service returned error {response.status_code}. Try again later."

        except requests.exceptions.Timeout:
            return "Company research timed out. Please try again."
        except requests.exceptions.ConnectionError:
            logger.error(
                f"company_research connection error - is SearXNG running on localhost:8086?"
            )
            return "Search service unavailable. Please try again later."
        except requests.exceptions.RequestException as e:
            logger.warning(f"company_research request error: {e}")
            return "Company research request failed. Please try again."
        except Exception as e:
            logger.error(f"company_research unexpected error: {e}")
            return "An error occurred during company research. Please try again."

    def crawling(self, url: str, max_characters: int = 3000) -> str:
        """Extracts content from specific URLs using direct web scraping"""
        if not self._check_rate_limit("crawling"):
            return "Rate limit exceeded. Please wait before crawling another URL."

        try:
            # Use session for content extraction (headers already set in session)
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # Use BeautifulSoup to parse HTML and extract text
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text content
            text = soup.get_text()

            # Limit to max_characters
            if len(text) > max_characters:
                text = text[:max_characters] + "..."

            return f"Content from {url}: {text}"

        except requests.exceptions.Timeout:
            return "URL crawling timed out. Try again later."
        except requests.exceptions.RequestException as e:
            return f"Error crawling URL: {str(e)}"
        except Exception as e:
            return f"Unexpected error during URL crawling: {str(e)}"

    def generate_image(
        self,
        prompt: str,
        model: str = "SDXL 1.0",
        width: int = 1024,
        height: int = 1024,
    ) -> str:
        """Generate an image using Arta API with rate limiting"""
        if not self._check_rate_limit("generate_image"):
            return "Rate limit exceeded. Please wait before generating another image."

        try:
            # Import image generator here to avoid circular imports
            from media.image_generator import image_generator

            # Generate the image
            image_url = image_generator.generate_image(
                prompt=prompt, model=model, width=width, height=height
            )

            return image_url

        except Exception as e:
            return f"Error generating image: {str(e)}"

    def analyze_image(self, image_url: str, prompt: str = "Describe this image") -> str:
        """Analyze an image using OpenRouter API vision capabilities with rate limiting"""
        if not self._check_rate_limit("analyze_image"):
            return "Rate limit exceeded. Please wait before analyzing another image."

        try:
            from ai.openrouter import openrouter_api

            payload = {
                "model": "openai",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                ],
            }

            headers = {"Content-Type": "application/json"}

            if openrouter_api.api_key:
                headers["Authorization"] = f"Bearer {openrouter_api.api_key}"

            response = self.session.post(
                openrouter_api.api_url,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                error_msg = result["error"]
                if "tenor.com" in image_url.lower():
                    return f"Cannot analyze Tenor GIF directly. Please provide a direct image URL (ending with .jpg, .png, .gif, etc.) instead of the Tenor page URL."
                return f"Error analyzing image: {error_msg}"

            if "choices" in result and len(result["choices"]) > 0:
                response_text = result["choices"][0]["message"]["content"]
                return response_text
            else:
                return "No response from image analysis"

        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    def calculate(self, expression: str) -> str:
        """Perform mathematical calculations and comparisons with rate limiting"""
        if not self._check_rate_limit("calculate"):
            return "Rate limit exceeded. Please wait before making another calculation."

        try:
            # Safe evaluation - allow alphanumeric characters and basic operators for flexible expressions
            # AST parsing below provides actual security - this validation just excludes truly dangerous characters
            disallowed_pattern = (
                r'[;\[\]{}"\'\\]'  # Reject: semicolons, brackets, quotes, backslash
            )
            import re

            if re.search(disallowed_pattern, expression):
                return "Error: Expression contains characters that could indicate code execution attempts. Only use numbers, operators, letters, and basic punctuation."

            # Use a safer evaluation method instead of eval
            import ast
            import operator

            # Supported operators for math and comparisons
            operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
            }

            # Supported comparison operators
            comparison_operators = {
                ast.Gt: operator.gt,  # >
                ast.Lt: operator.lt,  # <
                ast.GtE: operator.ge,  # >=
                ast.LtE: operator.le,  # <=
                ast.Eq: operator.eq,  # ==
                ast.NotEq: operator.ne,  # !=
            }

            def eval_expr(expr):
                """
                Safe evaluation of mathematical expressions
                """

                def _eval(node):
                    if isinstance(node, ast.Constant):  # For Python 3.8+
                        return node.value
                    elif isinstance(node, ast.Num):  # For Python < 3.8
                        return node.n
                    elif isinstance(node, ast.BinOp):
                        left = _eval(node.left)
                        right = _eval(node.right)
                        return operators[type(node.op)](left, right)
                    elif isinstance(node, ast.Compare):
                        left = _eval(node.left)
                        comparators = [_eval(comp) for comp in node.comparators]
                        ops = [comparison_operators[type(op)] for op in node.ops]

                        # For chained comparisons like 1 < 2 < 3
                        result = True
                        current_left = left
                        for op, current_right in zip(ops, comparators):
                            result = result and op(current_left, current_right)
                            current_left = current_right
                        return result
                    elif isinstance(node, ast.UnaryOp):
                        operand = _eval(node.operand)
                        return operators[type(node.op)](operand)
                    else:
                        raise TypeError(node)

                try:
                    tree = ast.parse(expr, mode="eval")
                    return _eval(tree.body)
                except (SyntaxError, TypeError, ValueError) as e:
                    raise ValueError(f"Invalid expression: {e}")

            result = eval_expr(expression)
            return f"Result: {result}"
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            return f"Error calculating expression: {str(e)}"

    def get_current_time(self, timezone: str = "UTC") -> str:
        """Get current time and date information for a specific timezone"""
        if not self._check_rate_limit("get_current_time"):
            return "Rate limit exceeded. Please wait before checking time again."

        try:
            # Common timezone aliases for ease of use
            timezone_aliases = {
                "est": "US/Eastern",
                "edt": "US/Eastern",
                "cst": "US/Central",
                "cdt": "US/Central",
                "mst": "US/Mountain",
                "mdt": "US/Mountain",
                "pst": "US/Pacific",
                "pdt": "US/Pacific",
                "gmt": "GMT",
                "bst": "Europe/London",
                "cet": "CET",
                "cest": "CET",
                "aest": "Australia/Sydney",
                "utc": "UTC",
            }

            # Convert alias to proper timezone name
            tz_name = timezone_aliases.get(timezone.lower(), timezone)

            try:
                # Get the timezone
                tz = pytz.timezone(tz_name)
            except pytz.exceptions.UnknownTimeZoneError:
                # Fallback to UTC if timezone not found
                tz = pytz.timezone("UTC")
                tz_name = "UTC"

            # Get current time in the specified timezone
            now = datetime.now(tz)

            # Format the time and date
            time_str = now.strftime("%I:%M:%S %p").lstrip(
                "0"
            )  # Remove leading zero from hour
            date_str = now.strftime("%A, %B %d, %Y")
            iso_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")

            # Calculate some additional info
            day_of_year = now.strftime("%j")
            week_number = now.isocalendar()[1]

            # Get timezone offset info
            offset = now.strftime("%z")
            offset_hours = int(offset[:3])
            offset_minutes = int(offset[3:])
            if offset_hours >= 0:
                offset_str = f"UTC+{offset_hours}:{offset_minutes:02d}"
            else:
                offset_str = f"UTC{offset_hours}:{offset_minutes:02d}"

            # Build response
            response = f"Current time in {tz_name}:\n"
            response += f"Time: {time_str}\n"
            response += f"Date: {date_str}\n"
            response += f"ISO: {iso_str}\n"
            response += f"Day of Year: {day_of_year}\n"
            response += f"Week: {week_number}\n"
            response += f"Offset: {offset_str}"

            return response

        except Exception as e:
            return f"Error getting time: {str(e)}"

    def set_reminder(
        self,
        user_id: str,
        reminder_type: str,
        title: str,
        description: str,
        trigger_time: str,
        channel_id: str = None,
        recurring_pattern: str = None,
    ) -> str:
        """Set a new reminder with rate limiting"""
        if not self._check_rate_limit("set_reminder"):
            return "Rate limit exceeded. Please wait before setting another reminder."

        try:
            # Import db here to avoid circular imports
            from data.database import db

            # Parse and validate trigger_time (support multiple formats)
            try:
                import datetime

                # Try to parse various time formats
                parsed_time = None

                # Try ISO 8601 format first
                try:
                    parsed_time = datetime.datetime.fromisoformat(
                        trigger_time.replace("Z", "+00:00")
                    )
                except ValueError:
                    pass

                # Try time formats like "12:15PM", "3:30 PM", etc.
                if not parsed_time:
                    try:
                        # Handle both 12:15PM and 12:15 PM formats
                        time_str = trigger_time.replace(" ", "").upper()
                        parsed_time = datetime.datetime.strptime(time_str, "%I:%M%p")
                        # Set to today's date
                        now = datetime.datetime.now()
                        parsed_time = parsed_time.replace(
                            year=now.year, month=now.month, day=now.day
                        )
                        # If time is in the past, set to tomorrow
                        if parsed_time <= now:
                            parsed_time += datetime.timedelta(days=1)
                    except ValueError:
                        pass

                # Try time formats like "12:15", "15:30", etc.
                if not parsed_time:
                    try:
                        # Try 24-hour format
                        if ":" in trigger_time:
                            time_parts = trigger_time.split(":")
                            if len(time_parts) == 2:
                                hour, minute = int(time_parts[0]), int(time_parts[1])
                                now = datetime.datetime.now()
                                parsed_time = now.replace(
                                    hour=hour, minute=minute, second=0, microsecond=0
                                )
                                # If time is in the past, set to tomorrow
                                if parsed_time <= now:
                                    parsed_time += datetime.timedelta(days=1)
                    except (ValueError, IndexError):
                        pass

                if not parsed_time:
                    raise ValueError(f"Could not parse time format: {trigger_time}")

                # Convert to ISO 8601 format for storage
                trigger_time = parsed_time.isoformat()

            except ValueError as e:
                return f"Invalid trigger_time format: {trigger_time}. Please use formats like '12:15PM', '15:30', or '2025-10-03T15:00:00Z'"

            # Create the reminder
            reminder_id = db.add_reminder(
                user_id,
                reminder_type,
                title,
                description,
                trigger_time,
                channel_id,
                recurring_pattern,
            )

            return f"✅ Reminder set successfully!\n• **Title**: {title}\n• **Description**: {description}\n• **Trigger Time**: {trigger_time}\n• **ID**: {reminder_id}"

        except Exception as e:
            return f"Error setting reminder: {str(e)}"

    def list_reminders(self, user_id: str) -> str:
        """List all pending reminders for a user with rate limiting"""
        if not self._check_rate_limit("list_reminders"):
            return "Rate limit exceeded. Please wait before listing reminders again."

        try:
            # Import db here to avoid circular imports
            from data.database import db

            reminders = db.get_user_reminders(user_id)

            if not reminders:
                return "📝 You have no pending reminders."

            response = f"📅 **Your Reminders** ({len(reminders)} total):\n\n"

            for reminder in reminders:
                status_emoji = "⏰" if reminder["status"] == "pending" else "✅"
                response += f"{status_emoji} **{reminder['title']}**\n"
                response += f"   • Description: {reminder['description']}\n"
                response += f"   • Due: {reminder['trigger_time']}\n"
                response += f"   • Type: {reminder['reminder_type']}\n"
                response += f"   • ID: {reminder['id']}\n\n"

            return response

        except Exception as e:
            return f"Error listing reminders: {str(e)}"

    def cancel_reminder(self, reminder_id: str, user_id: str) -> str:
        """Cancel a reminder by ID with rate limiting"""
        if not self._check_rate_limit("cancel_reminder"):
            return "Rate limit exceeded. Please wait before canceling another reminder."

        try:
            # Import db here to avoid circular imports
            from data.database import db

            # First check if the reminder exists and belongs to the user
            reminder = db.get_reminder(int(reminder_id))
            if not reminder:
                return f"❌ Reminder with ID {reminder_id} not found."

            if str(reminder["user_id"]) != user_id:
                return "❌ You can only cancel your own reminders."

            # Cancel the reminder
            db.update_reminder_status(int(reminder_id), "cancelled")

            return f"✅ Reminder '{reminder['title']}' has been cancelled."

        except Exception as e:
            return f"Error canceling reminder: {str(e)}"

    def check_due_reminders(self) -> str:
        """Check for due reminders and return formatted list with rate limiting"""
        if not self._check_rate_limit("check_due_reminders"):
            return (
                "Rate limit exceeded. Please wait before checking due reminders again."
            )

        try:
            # Import db here to avoid circular imports
            from data.database import db

            due_reminders = db.get_due_reminders()

            if not due_reminders:
                return "No reminders are currently due."

            response = f"🔔 **{len(due_reminders)} reminder(s) are due:**\n"

            for reminder in due_reminders:
                response += f"- **{reminder['title']}** (ID: {reminder['id']}, User: {reminder['user_id']})\n"
                response += f"  {reminder['description']}\n"
                response += f"  Due: {reminder['trigger_time']}\n\n"

            return response

        except Exception as e:
            return f"Error checking due reminders: {str(e)}"

    # Discord tool methods
    def discord_get_user_info(self) -> str:
        """Get information about the currently logged-in Discord user"""
        if not self._check_rate_limit("discord_get_user_info"):
            return "Rate limit exceeded for Discord user info request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = self.discord_tools.get_user_info()
            if "error" in result:
                return f"Error getting Discord user info: {result['error']}"

            user = result["user"]
            return f"Discord User Info:\n- ID: {user['id']}\n- Username: {user['username']}\n- Display Name: {user['display_name']}\n- Created: {user['created_at']}"
        except Exception as e:
            return f"Error getting Discord user info: {str(e)}"

    def discord_list_guilds(self) -> str:
        """List all Discord servers/guilds the user is in"""
        if not self._check_rate_limit("discord_list_guilds"):
            return "Rate limit exceeded for Discord guilds list request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = self.discord_tools.list_guilds()
            if "error" in result:
                return f"Error listing Discord guilds: {result['error']}"

            guilds = result["guilds"]
            response = f"Discord Guilds ({result['count']} total):\n"
            for guild in guilds:
                response += f"- {guild['name']} (ID: {guild['id']}, Members: {guild['member_count']})\n"

            return response
        except Exception as e:
            return f"Error listing Discord guilds: {str(e)}"

    def discord_list_channels(self, guild_id: Optional[str] = None) -> str:
        """List channels the user has access to, optionally filtered by guild"""
        if not self._check_rate_limit("discord_list_channels"):
            return "Rate limit exceeded for Discord channels list request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = self.discord_tools.list_channels(guild_id)
            if "error" in result:
                return f"Error listing Discord channels: {result['error']}"

            channels = result["channels"]
            response = f"Discord Channels ({result['count']} total):\n"
            for channel in channels:
                response += f"- #{channel['name']} (ID: {channel['id']}, Guild: {channel['guild_name']})\n"

            return response
        except Exception as e:
            return f"Error listing Discord channels: {str(e)}"

    async def discord_read_channel(self, channel_id: str, limit: int = 50) -> str:
        """Read messages from a specific Discord channel"""
        logger.info(
            f"discord_read_channel called with channel_id={channel_id}, limit={limit}"
        )

        if not self._check_rate_limit("discord_read_channel"):
            logger.warning("Rate limit exceeded for discord_read_channel")
            return "Rate limit exceeded for Discord channel read request."

        try:
            if self.discord_tools is None:
                logger.error(
                    "Discord tools not initialized when discord_read_channel was called"
                )
                return "Discord tools not initialized. Bot may not be connected to Discord."

            logger.info(
                f"Calling discord_tools.read_channel with channel_id={channel_id}, limit={limit}"
            )
            result = await self.discord_tools.read_channel(channel_id, limit)
            logger.info(f"discord_tools.read_channel returned: {result}")
            logger.info(
                f"Result type: {type(result)}, Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
            )

            if "error" in result:
                logger.error(f"Error in discord_read_channel result: {result['error']}")
                return f"Error reading Discord channel: {result['error']}"

            messages = result["messages"]
            channel_info = result["channel"]
            response = f"Channel: #{channel_info['name']} ({channel_info['id']})\n"
            response += f"Guild: {channel_info['guild_name']}\n"
            response += f"Messages ({result['count']} total):\n\n"

            for message in messages:
                timestamp = message["timestamp"].split("T")[0]  # Just the date part
                response += f"[{timestamp}] {message['author']['username']}: {message['content']}\n"
                if message["attachments"]:
                    response += f"  Attachments: {', '.join(message['attachments'])}\n"
                response += "\n"

            logger.info(
                f"Successfully formatted {len(messages)} messages from channel {channel_id}"
            )
            return response
        except Exception as e:
            logger.error(f"Exception in discord_read_channel: {str(e)}", exc_info=True)
            return f"Error reading Discord channel: {str(e)}"

    async def discord_search_messages(
        self,
        channel_id: str,
        query: str = "",
        author_id: Optional[str] = None,
        limit: int = 100,
    ) -> str:
        """Search for messages in a Discord channel by content, author, etc."""
        if not self._check_rate_limit("discord_search_messages"):
            return "Rate limit exceeded for Discord message search request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            logger.info(
                f"discord_search_messages calling discord_tools.search_messages with channel_id={channel_id}, query='{query}', limit={limit}"
            )
            result = await self.discord_tools.search_messages(
                channel_id, query, author_id, limit
            )
            logger.info(f"discord_search_messages received result: {str(result)[:500]}")

            if "error" in result:
                logger.error(f"discord_search_messages error: {result['error']}")
                return f"Error searching Discord messages: {result['error']}"

            messages = result["messages"]
            channel_info = result["channel"]
            logger.info(
                f"discord_search_messages found {len(messages)} messages in #{channel_info['name']}"
            )
            response = f"Search Results in Channel: #{channel_info['name']} ({channel_info['id']})\n"
            response += f"Guild: {channel_info['guild_name']}\n"
            response += f"Query: '{result['query']}'\n"
            response += f"Found {result['count']} matching messages:\n\n"

            for message in messages:
                timestamp = message["timestamp"].split("T")[0]  # Just the date part
                response += f"[{timestamp}] {message['author']['username']}: {message['content']}\n"
                if message["attachments"]:
                    response += f"  Attachments: {', '.join(message['attachments'])}\n"
                response += "\n"

            return response
        except Exception as e:
            return f"Error searching Discord messages: {str(e)}"

    def discord_list_guild_members(
        self, guild_id: str, limit: int = 100, include_roles: bool = False
    ) -> str:
        """List members of a specific Discord guild/server"""
        if not self._check_rate_limit("discord_list_guild_members"):
            return "Rate limit exceeded for Discord guild members list request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = self.discord_tools.list_guild_members(
                guild_id, limit, include_roles
            )
            if "error" in result:
                return f"Error listing Discord guild members: {result['error']}"

            members = result["members"]
            guild_info = result["guild"]
            response = f"Members of Guild: {guild_info['name']} ({guild_info['id']})\n"
            response += f"Total Members Listed: {result['count']}\n\n"

            for member in members:
                response += f"- {member['username']}#{member['discriminator']} (ID: {member['id']})\n"
                if include_roles and "roles" in member and member["roles"]:
                    role_names = [role["name"] for role in member["roles"]]
                    response += f"  Roles: {', '.join(role_names)}\n"

            return response
        except Exception as e:
            return f"Error listing Discord guild members: {str(e)}"

    async def discord_send_message(
        self, channel_id: str, content: str, reply_to_message_id: Optional[str] = None
    ) -> str:
        """Send a message to a specific Discord channel"""
        logger.info(
            f"discord_send_message called with channel_id={channel_id}, content='{content[:100]}...', reply_to_message_id={reply_to_message_id}"
        )

        if not self._check_rate_limit("discord_send_message"):
            logger.warning("Rate limit exceeded for Discord send message request.")
            return "Rate limit exceeded for Discord send message request."

        try:
            if self.discord_tools is None:
                logger.error(
                    "Discord tools not initialized when discord_send_message was called"
                )
                return "Discord tools not initialized. Bot may not be connected to Discord."

            logger.info(
                f"Calling discord_tools.send_message with channel_id={channel_id}, content='{content[:100]}...', reply_to_message_id={reply_to_message_id}"
            )
            result = await self.discord_tools.send_message(
                channel_id, content, reply_to_message_id
            )
            logger.info(f"discord_tools.send_message returned: {result}")

            if "error" in result:
                logger.error(f"Error in discord_send_message result: {result['error']}")
                return f"Error sending Discord message: {result['error']}"

            message = result["message"]
            logger.info(
                f"Successfully sent message to channel {message['channel_id']}, message ID: {message['id']}"
            )
            return f"✅ Message sent successfully!\nChannel: {message['channel_id']}\nMessage ID: {message['id']}\nContent: {message['content']}"
        except Exception as e:
            logger.error(f"Exception in discord_send_message: {str(e)}", exc_info=True)
            return f"Error sending Discord message: {str(e)}"

    async def discord_send_dm(self, user_id: str, content: str) -> str:
        """Send a direct message to a specific Discord user"""
        if not self._check_rate_limit("discord_send_dm"):
            return "Rate limit exceeded for Discord send DM request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = await self.discord_tools.send_dm(user_id, content)
            if "error" in result:
                return f"Error sending Discord DM: {result['error']}"

            message = result["message"]
            return f"✅ DM sent successfully!\nRecipient ID: {message['recipient_id']}\nMessage ID: {message['id']}\nContent: {message['content']}"
        except Exception as e:
            return f"Error sending Discord DM: {str(e)}"

    def discord_get_user_roles(self, guild_id: Optional[str] = None) -> str:
        """Get roles for the currently logged-in user in a specific guild"""
        logger.info(f"discord_get_user_roles called with guild_id={guild_id}")

        if not self._check_rate_limit("discord_get_user_roles"):
            return "Rate limit exceeded for Discord user roles request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = self.discord_tools.get_user_roles(guild_id)
            logger.info(f"discord_get_user_roles result: {result}")

            if "error" in result:
                logger.error(f"discord_get_user_roles error: {result['error']}")
                return f"Error getting Discord user roles: {result['error']}"

            user = result["user"]
            guild = result["guild"]
            roles = result["roles"]
            logger.info(
                f"discord_get_user_roles: user={user['display_name']}, guild={guild['name']}, roles_count={len(roles)}"
            )

            if not roles:
                return f"User {user['display_name']} has no roles in guild '{guild['name']}' (ID: {guild['id']})."

            role_list = "\n".join(
                [f"- {role['name']} (ID: {role['id']})" for role in roles]
            )
            return f"Discord User Roles in '{guild['name']}':\nUser: {user['display_name']} (ID: {user['id']})\nRoles ({result['role_count']}):\n{role_list}"
        except Exception as e:
            return f"Error getting Discord user roles: {str(e)}"

    async def discord_kick_user(
        self, guild_id: str, user_id: str, reason: str = "", **kwargs
    ) -> str:
        """Kick a user from a specific guild"""
        if not self._check_rate_limit("discord_kick_user"):
            return "Rate limit exceeded for kick user request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = await self.discord_tools.kick_user(guild_id, user_id, reason)
            if "error" in result:
                return f"Error kicking user: {result['error']}"

            return f"✅ Successfully kicked user {result['user']} from {result['guild']}.\nReason: {result['reason'] or 'None provided'}"
        except Exception as e:
            return f"Error kicking user: {str(e)}"

    async def discord_ban_user(
        self,
        guild_id: str,
        user_id: str,
        reason: str = "",
        delete_message_seconds: int = 0,
        **kwargs,
    ) -> str:
        """Ban a user from a specific guild"""
        if not self._check_rate_limit("discord_ban_user"):
            return "Rate limit exceeded for ban user request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = await self.discord_tools.ban_user(
                guild_id, user_id, reason, delete_message_seconds
            )
            if "error" in result:
                return f"Error banning user: {result['error']}"

            return f"✅ Successfully banned user {result['user']} from {result['guild']}.\nReason: {result['reason'] or 'None provided'}"
        except Exception as e:
            return f"Error banning user: {str(e)}"

    async def discord_unban_user(
        self, guild_id: str, user_id: str, reason: str = "", **kwargs
    ) -> str:
        """Unban a user from a specific guild"""
        if not self._check_rate_limit("discord_unban_user"):
            return "Rate limit exceeded for unban user request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = await self.discord_tools.unban_user(guild_id, user_id, reason)
            if "error" in result:
                return f"Error unbanning user: {result['error']}"

            return f"✅ Successfully unbanned user {result['user']} from {result['guild']}.\nReason: {result['reason'] or 'None provided'}"
        except Exception as e:
            return f"Error unbanning user: {str(e)}"

    async def discord_timeout_user(
        self,
        guild_id: str,
        user_id: str,
        duration_minutes: int,
        reason: str = "",
        **kwargs,
    ) -> str:
        """Timeout a user in a specific guild"""
        if not self._check_rate_limit("discord_timeout_user"):
            return "Rate limit exceeded for timeout user request."

        if kwargs:
            # Log ignored arguments for debugging
            pass

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            # Ensure duration_minutes is an integer before passing to discord_tools
            if isinstance(duration_minutes, str):
                try:
                    duration_minutes = int(duration_minutes)
                except ValueError:
                    return f"Error timing out user: Invalid duration_minutes: '{duration_minutes}'. Must be a number."

            result = await self.discord_tools.timeout_user(
                guild_id, user_id, duration_minutes, reason
            )
            if "error" in result:
                return f"Error timing out user: {result['error']}"

            # Ensure the returned duration_minutes is an int for comparison
            returned_duration = result.get("duration_minutes", 0)
            if isinstance(returned_duration, str):
                try:
                    returned_duration = int(returned_duration)
                except ValueError:
                    returned_duration = 0

            if returned_duration > 0:
                return f"✅ Successfully timed out user {result['user']} in {result['guild']} for {returned_duration} minutes.\nReason: {result['reason'] or 'None provided'}"
            else:
                return f"✅ Successfully removed timeout for user {result['user']} in {result['guild']}.\nReason: {result['reason'] or 'None provided'}"
        except Exception as e:
            return f"Error timing out user: {str(e)}"

    async def discord_remove_timeout(
        self, guild_id: str, user_id: str, reason: str = ""
    ) -> str:
        """Remove timeout from a user"""
        if not self._check_rate_limit("discord_remove_timeout"):
            return "Rate limit exceeded for remove timeout request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            # Calls timeout_user with duration 0 to remove timeout
            result = await self.discord_tools.timeout_user(guild_id, user_id, 0, reason)
            if "error" in result:
                return f"Error removing timeout: {result['error']}"

            return f"✅ Successfully removed timeout for user {result['user']} in {result['guild']}.\nReason: {result['reason'] or 'None provided'}"
        except Exception as e:
            return f"Error removing timeout: {str(e)}"

    async def discord_purge_messages(
        self, channel_id: str, limit: int = 10, user_id: str = None
    ) -> str:
        """Purge messages from a channel"""
        if not self._check_rate_limit("discord_purge_messages"):
            return "Rate limit exceeded for purge messages request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = await self.discord_tools.purge_messages(channel_id, limit, user_id)
            if "error" in result:
                return f"Error purging messages: {result['error']}"

            return f"✅ Successfully purged {result['deleted_count']} messages in #{result['channel']}."
        except Exception as e:
            return f"Error purging messages: {str(e)}"

    async def discord_pin_message(self, channel_id: str, message_id: str) -> str:
        """Pin a message in a channel"""
        if not self._check_rate_limit("discord_pin_message"):
            return "Rate limit exceeded for pin message request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = await self.discord_tools.pin_message(channel_id, message_id)
            if "error" in result:
                return f"Error pinning message: {result['error']}"

            return f"✅ Successfully pinned message {result['message_id']} in #{result['channel']}."
        except Exception as e:
            return f"Error pinning message: {str(e)}"

    async def discord_unpin_message(self, channel_id: str, message_id: str) -> str:
        """Unpin a message in a channel"""
        if not self._check_rate_limit("discord_unpin_message"):
            return "Rate limit exceeded for unpin message request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = await self.discord_tools.unpin_message(channel_id, message_id)
            if "error" in result:
                return f"Error unpinning message: {result['error']}"

            return f"✅ Successfully unpinned message {result['message_id']} in #{result['channel']}."
        except Exception as e:
            return f"Error unpinning message: {str(e)}"

    async def discord_delete_message(self, channel_id: str, message_id: str) -> str:
        """Delete a single user message from a channel"""
        if not self._check_rate_limit("discord_delete_message"):
            return "Rate limit exceeded for delete message request."

        try:
            if self.discord_tools is None:
                return "Discord tools not initialized. Bot may not be connected to Discord."

            result = await self.discord_tools.delete_message(channel_id, message_id)
            if "error" in result:
                return f"Error deleting message: {result['error']}"

            return f"✅ Successfully deleted message {result['message_id']} in {result['channel']}."
        except Exception as e:
            return f"Error deleting message: {str(e)}"

    def set_discord_tools(self, bot_client):
        """Initialize Discord tools with the bot client"""
        from .discord_tools import DiscordTools

        self.discord_tools = DiscordTools(bot_client)

    def get_user_rate_limit_status(self, user_id: str) -> str:
        """Get rate limiting status for a specific user"""
        if not RATE_LIMITING_ENABLED:
            return "Rate limiting is not enabled."

        try:
            stats = rate_limit_middleware.rate_limiter.get_user_stats(user_id)

            response = f"📊 **Rate Limit Status for User {user_id}**\n\n"
            response += f"🔥 Penalty Multiplier: {stats['penalty_multiplier']}x\n"
            response += f"⚠️ Total Violations: {stats['total_violations']}\n"
            response += f"🚨 Recent Violations (1h): {stats['recent_violations']}\n\n"

            if stats["current_usage"]:
                response += "**Current Usage:**\n"
                for operation, usage in stats["current_usage"].items():
                    response += f"• {operation}:\n"
                    for limit_type, data in usage.items():
                        percentage = data["percentage"]
                        emoji = (
                            "🟢"
                            if percentage < 50
                            else "🟡"
                            if percentage < 80
                            else "🔴"
                        )
                        response += f"  {emoji} {limit_type}: {data['current']}/{data['limit']} ({percentage:.1f}%)\n"
                    response += "\n"
            else:
                response += "No recent activity recorded.\n"

            return response
        except Exception as e:
            return f"Error getting rate limit status: {str(e)}"

    def get_system_rate_limit_stats(self) -> str:
        """Get overall system rate limiting statistics"""
        if not RATE_LIMITING_ENABLED:
            return "Rate limiting is not enabled."

        try:
            stats = rate_limit_middleware.rate_limiter.get_system_stats()

            response = f"📈 **System Rate Limit Statistics**\n\n"
            response += f"⏱️ Uptime: {stats['uptime_seconds']:.0f} seconds\n"
            response += f"📊 Total Requests: {stats['total_requests']}\n"
            response += f"⚠️ Total Violations: {stats['total_violations']}\n"
            response += f"🚀 Requests/Second: {stats['requests_per_second']:.2f}\n"
            response += f"👥 Active Users (1h): {stats['active_users_count']}\n"
            response += f"👤 Total Users: {stats['total_users_count']}\n"
            response += (
                f"🚨 Recent Violations (1h): {stats['recent_violations_count']}\n"
            )
            response += f"🔥 Users with Penalties: {stats['users_with_penalties']}\n"
            response += (
                f"⚡ Average Penalty: {stats['average_penalty_multiplier']:.2f}x\n"
            )

            # Calculate violation rate
            if stats["total_requests"] > 0:
                violation_rate = (
                    stats["total_violations"] / stats["total_requests"]
                ) * 100
                response += f"📉 Violation Rate: {violation_rate:.2f}%\n"

            return response
        except Exception as e:
            return f"Error getting system stats: {str(e)}"

    def reset_user_rate_limits(self, user_id: str) -> str:
        """Reset rate limits for a specific user (admin function)"""
        if not RATE_LIMITING_ENABLED:
            return "Rate limiting is not enabled."

        try:
            rate_limit_middleware.rate_limiter.reset_user_limits(user_id)
            return f"✅ Rate limits reset for user {user_id}"
        except Exception as e:
            return f"Error resetting user rate limits: {str(e)}"

    async def execute_tool(
        self, tool_name: str, arguments: Dict, user_id: str = "system"
    ) -> str:
        """Execute a tool by name with given arguments and improved error handling"""
        if tool_name not in self.tools:
            return f"Unknown tool: {tool_name}"

        # Handle parameter mapping for backward compatibility
        mapped_arguments = arguments.copy()
        if tool_name == "remember_user_info":
            if "key" in mapped_arguments and "information_type" not in mapped_arguments:
                mapped_arguments["information_type"] = mapped_arguments.pop("key")
            if "value" in mapped_arguments and "information" not in mapped_arguments:
                mapped_arguments["information"] = mapped_arguments.pop("value")
        elif tool_name == "get_bonus_schedule":
            # Handle case where AI calls with "platform" instead of separate "site" and "frequency"
            if (
                "platform" in mapped_arguments
                and "site" not in mapped_arguments
                and "frequency" not in mapped_arguments
            ):
                platform = mapped_arguments.pop("platform")
                # Parse platform string to extract site and frequency
                # Example: "shuffle weekly" -> site="shuffle", frequency="weekly"
                parts = platform.split()
                if len(parts) >= 2:
                    mapped_arguments["site"] = parts[0]
                    mapped_arguments["frequency"] = parts[1]
                elif len(parts) == 1:
                    # If only one part, assume it's the site and default to "weekly"
                    mapped_arguments["site"] = parts[0]
                    mapped_arguments["frequency"] = "weekly"

        # Add/override user_id for methods that should use the actual Discord user ID
        # These tools should always use the real user ID from the message context, not what the AI provides
        user_id_override_tools = [
            "set_reminder",
            "list_reminders",
            "cancel_reminder",
            "remember_user_info",
            "search_user_memory",
        ]
        if tool_name in user_id_override_tools:
            mapped_arguments["user_id"] = user_id
        elif (
            tool_name in ["get_crypto_price", "get_stock_price"]
            and "user_id" not in mapped_arguments
        ):
            mapped_arguments["user_id"] = user_id

        try:
            tool_func = self.tools[tool_name]

            # Tools that are async and need to be awaited directly
            async_tools = [
                # FatTips tools - all are async and make API calls
                "fattips_get_balance",
                "fattips_send_tip",
                "fattips_send_batch_tip",
                "fattips_create_airdrop",
                "fattips_claim_airdrop",
                "fattips_list_airdrops",
                "fattips_create_rain",
                "fattips_get_wallet",
                "fattips_create_wallet",
                "fattips_get_transactions",
                "fattips_withdraw",
                "fattips_get_swap_quote",
                "fattips_execute_swap",
                "fattips_get_leaderboard",
            ]

            # Handle async tools directly
            if tool_name in async_tools:
                import asyncio
                import inspect

                if inspect.iscoroutinefunction(tool_func):
                    return await tool_func(**mapped_arguments)
                else:
                    # If it's not async but in async list, call normally
                    return tool_func(**mapped_arguments)

            # Tools that make network requests and should run in thread pool to avoid blocking
            blocking_tools = [
                "web_search",
                "crawling",
                "company_research",
                "get_crypto_price",
                "get_stock_price",
                "generate_image",
                "analyze_image",
                "check_balance",
                "get_bonus_schedule",
            ]

            # Run blocking tools in thread pool to avoid event loop blocking
            if tool_name in blocking_tools:
                import asyncio
                import functools

                loop = asyncio.get_running_loop()
                # Use functools.partial to handle keyword arguments properly
                partial_func = functools.partial(tool_func, **mapped_arguments)
                return await loop.run_in_executor(None, partial_func)

            # Check if the function is a coroutine function
            import asyncio

            if asyncio.iscoroutinefunction(tool_func):
                return await tool_func(**mapped_arguments)
            else:
                return tool_func(**mapped_arguments)
        except TypeError as e:
            return f"Error executing {tool_name}: Parameter mismatch - {str(e)}"
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def generate_keno_numbers(self, count: int = None) -> str:
        """Generate random Keno numbers (1-10 numbers from 1-40) with visual board

        Args:
            count: Optional number between 1-10 specifying how many numbers to generate

        Returns:
            Formatted string with Keno numbers and visual board
        """
        import random

        # Validate count parameter
        if count is not None:
            if not (1 <= count <= 10):
                return "❌ Please provide a count between 1 and 10!"
        else:
            # Generate a random count between 3 and 10 if not provided
            count = random.randint(3, 10)

        # Generate random numbers from 1-40 without duplicates
        numbers = random.sample(range(1, 41), count)

        # Sort the numbers for better readability
        numbers.sort()

        # Create the response
        response = f"**🎯 Keno Number Generator**\n"
        response += f"Generated **{count}** numbers for you!\n\n"

        # Add the numbers
        response += f"**Your Keno Numbers:**\n"
        response += f"`{', '.join(map(str, numbers))}`\n\n"

        # Create visual representation (8 columns x 5 rows) with clean spacing
        visual_lines = []
        for row in range(0, 40, 8):
            line = ""
            for i in range(row + 1, min(row + 9, 41)):
                if i in numbers:
                    # Bracketed numbers with consistent spacing
                    line += f"[{i:2d}] "
                else:
                    # Regular numbers with consistent spacing
                    line += f" {i:2d}  "
            visual_lines.append(line.rstrip())

        response += "**Visual Board:**\n"
        response += "```\n" + "\n".join(visual_lines) + "\n```"
        response += "\n*Numbers in brackets are your picks!*"

        return response

    async def play_trivia(
        self, channel_id: str, category: str = None, difficulty: int = None
    ) -> str:
        """Start an interactive trivia game in the specified channel and post the question

        Args:
            channel_id: Discord channel ID where to post the trivia question
            category: Optional trivia category filter
            difficulty: Optional difficulty level (1=easy, 2=medium, 3=hard)

        Returns:
            Success message if posted successfully, error message if failed
        """
        if not self._check_rate_limit("play_trivia", channel_id):
            return "⏰ Trivia rate limit exceeded. Please wait before starting another game."

        try:
            # Handle "null" strings from AI
            if isinstance(category, str) and category.lower() == "null":
                category = None
            if isinstance(difficulty, str) and difficulty.lower() == "null":
                difficulty = None

            # Convert difficulty to int if it's a string
            if difficulty is not None:
                try:
                    difficulty = int(difficulty)
                except ValueError:
                    # Handle string literals like "none" or invalid numeric strings
                    logger.warning(
                        f"Invalid difficulty value '{difficulty}', using None"
                    )
                    difficulty = None
            # Import trivia manager
            import random

            from data.trivia_database import trivia_db

            # Initialize if needed
            if not hasattr(self, "_trivia_games"):
                self._trivia_games = {}  # channel_id -> game_state

            # Check if there's already an active game in this channel
            if channel_id in self._trivia_games:
                active_game = self._trivia_games[channel_id]
                elapsed = asyncio.get_event_loop().time() - active_game["start_time"]
                if elapsed < 60:  # Game expires after 60 seconds
                    return f"❌ There's already an active trivia game in this channel! Wait for it to finish."

            # Get available categories if category not specified
            if category:
                questions = await trivia_db.get_questions_by_category(
                    category, limit=100
                )
                if not questions:
                    return f"❌ No trivia questions found for category: `{category}`. Try %triviacats to see available categories."
            else:
                # Get all categories
                categories = await trivia_db.get_all_categories()
                if not categories:
                    return "❌ No trivia categories available. An admin should run `%seedtrivia` first to populate the database."

                # Pick a random category that has questions
                categories_with_questions = [
                    c for c in categories if c["question_count"] > 0
                ]
                if not categories_with_questions:
                    return "❌ No trivia questions available. An admin should run `%seedtrivia` first."

                selected_category = random.choice(categories_with_questions)
                category = selected_category["name"]
                questions = await trivia_db.get_questions_by_category(
                    category, limit=100
                )

            # Filter by difficulty if specified
            if difficulty:
                questions = [
                    q for q in questions if q.get("difficulty", 1) == difficulty
                ]
                if not questions:
                    return f"❌ No questions found with difficulty level {difficulty} in category `{category}`."

            # Select a random question
            question = random.choice(questions)

            # Store the active game
            start_time = asyncio.get_event_loop().time()
            self._trivia_games[channel_id] = {
                "question": question,
                "category": category,
                "start_time": start_time,
                "attempts": 0,
            }
            logger.info(
                f"Stored trivia game in channel {channel_id}, start_time: {start_time}"
            )

            # Format the trivia question
            difficulty_emoji = {1: "🟢", 2: "🟡", 3: "🔴"}
            difficulty_text = {1: "Easy", 2: "Medium", 3: "Hard"}

            diff_level = question.get("difficulty", 1)

            trivia_message = f"""**🎮 TRIVIA TIME! 🎮**

📚 **Category:** {category}
{difficulty_emoji.get(diff_level, "🟢")} **Difficulty:** {difficulty_text.get(diff_level, "Easy")}

**❓ Question:**
{question["question_text"]}

⏱️ You have 60 seconds to answer! Just type your answer in chat.

💡 *Hint: The answer has {len(question["answer_text"])} characters*"""

            # Post the question to the channel using the Discord tools if available
            if self.discord_tools:
                try:
                    # Sanitize message to handle ampersands and other special characters before validation
                    sanitized_message = trivia_message.replace("&", "and").replace(
                        "&amp;", "and"
                    )

                    # Send the trivia question to the specified channel
                    # Need to await the coroutine since discord_tools.send_message is async
                    send_result = await self.discord_tools.send_message(
                        channel_id=channel_id, content=sanitized_message
                    )

                    # Check if message was sent successfully
                    if (
                        isinstance(send_result, dict)
                        and send_result.get("status") == "sent"
                    ):
                        return "Trivia question has been posted successfully to the channel."
                    else:
                        logger.error(f"Failed to send trivia message: {send_result}")
                        # Fallback - return the trivia message in case AI tries to send it manually
                        return trivia_message
                except Exception as e:
                    logger.error(f"Error sending trivia question to Discord: {e}")
                    # Fallback - return the trivia message in case AI tries to send it manually
                    return trivia_message
            else:
                # If no Discord tools available, return the message for AI to handle
                return trivia_message

        except Exception as e:
            logger.error(f"Error in play_trivia: {e}")
            return f"❌ Error starting trivia game: {str(e)}"

    def check_trivia_answer(self, channel_id: str, user_answer: str) -> tuple:
        """Check if a user's answer to the active trivia game is correct

        Args:
            channel_id: Discord channel ID
            user_answer: User's answer attempt

        Returns:
            Tuple of (is_correct: bool, correct_answer: str, game_ended: bool)
        """
        if not hasattr(self, "_trivia_games"):
            logger.debug(
                f"_trivia_games not initialized when checking channel {channel_id}"
            )
            return False, "", False

        logger.debug(
            f"Checking trivia answer for channel {channel_id}, active games: {len(self._trivia_games) if hasattr(self, '_trivia_games') else 0}"
        )

        game = self._trivia_games.get(channel_id)
        if not game:
            logger.debug(f"No active trivia game in channel {channel_id}")
            return False, "", False

        # Check if game has timed out
        elapsed = asyncio.get_event_loop().time() - game["start_time"]
        if elapsed > 30:
            correct_answer = game["question"]["answer_text"]
            if channel_id in self._trivia_games:
                del self._trivia_games[channel_id]
            return False, correct_answer, True

        # Increment attempts
        game["attempts"] += 1

        # Get correct answer
        correct_answer = game["question"]["answer_text"]

        # Normalize for comparison
        user_ans = user_answer.strip().lower()
        correct_ans = correct_answer.strip().lower()

        # Check various match conditions
        is_correct = (
            user_ans == correct_ans
            or user_ans in correct_ans
            or correct_ans in user_ans
            or any(
                word in correct_ans.split()
                for word in user_ans.split()
                if len(word) > 3
            )
        )

        # End game if correct
        if is_correct:
            if channel_id in self._trivia_games:
                del self._trivia_games[channel_id]
            return True, correct_answer, True

        return False, correct_answer, False

    # ==================== FatTips Tools ====================

    async def fattips_get_balance(self, user_id: str) -> str:
        """Get a user's FatTips wallet balance (SOL, USDC, USDT)

        Args:
            user_id: Discord user ID to check balance for

        Returns:
            Formatted balance string or error message
        """
        if not self._check_rate_limit("fattips_get_balance", user_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            balance = await manager.get_formatted_balance(user_id)
            return balance
        except Exception as e:
            logger.error(f"Error in fattips_get_balance: {e}")
            return f"❌ Error getting balance: {str(e)}"

    async def fattips_send_tip(self, from_user_id: str, to_user_id: str, amount: float, token: str = "SOL", amount_type: str = "token") -> str:
        """Send a tip to another user using FatTips

        Args:
            from_user_id: Discord user ID of the sender (Jakey's ID)
            to_user_id: Discord user ID of the recipient
            amount: Amount to tip
            token: Token to tip in (SOL, USDC, USDT)
            amount_type: "token" or "usd"

        Returns:
            Success message with transaction details or error
        """
        if not self._check_rate_limit("fattips_send_tip", from_user_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED, FATTIPS_JAKEY_DISCORD_ID
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            # Use configured Jakey ID if from_user_id not provided
            sender_id = from_user_id or FATTIPS_JAKEY_DISCORD_ID
            if not sender_id:
                return "❌ No sender ID configured for FatTips."

            result = await manager.send_tip(sender_id, to_user_id, amount, token, amount_type)
            
            if "error" in result:
                return f"❌ Tip failed: {result['error']}"
            
            return f"💸 **Tip sent successfully!**\nFrom: <@{result['from']}>\nTo: <@{result['to']}>\nAmount: {result['amountToken']} {result['token']} (~${result['amountUsd']:.2f})\n[View on Solscan]({result.get('solscanUrl', '#')})"
        except Exception as e:
            logger.error(f"Error in fattips_send_tip: {e}")
            return f"❌ Error sending tip: {str(e)}"

    async def fattips_send_batch_tip(self, from_user_id: str, recipients: list, total_amount: float, token: str = "SOL", amount_type: str = "token") -> str:
        """Send tips to multiple users at once (Rain)

        Args:
            from_user_id: Discord user ID of the sender
            recipients: List of Discord user IDs to receive tips
            total_amount: Total amount to distribute
            token: Token to tip in
            amount_type: "token" or "usd"

        Returns:
            Success message with rain details or error
        """
        if not self._check_rate_limit("fattips_send_batch_tip", from_user_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED, FATTIPS_JAKEY_DISCORD_ID
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            sender_id = from_user_id or FATTIPS_JAKEY_DISCORD_ID
            if not sender_id:
                return "❌ No sender ID configured for FatTips."

            result = await manager.send_batch_tip(sender_id, recipients, total_amount, token, amount_type)
            
            if "error" in result:
                return f"❌ Batch tip failed: {result['error']}"
            
            winner_count = len(result.get('recipients', []))
            amount_per_user = result.get('amountPerUser', 0)
            
            return f"🌧️ **Rain sent successfully!**\nRecipients: {winner_count}\nAmount per user: {amount_per_user:.4f} {result['token']}\nTotal: {result['totalAmountToken']} {result['token']} (~${result['totalAmountUsd']:.2f})\n[View on Solscan]({result.get('solscanUrl', '#')})"
        except Exception as e:
            logger.error(f"Error in fattips_send_batch_tip: {e}")
            return f"❌ Error sending batch tip: {str(e)}"

    async def fattips_create_airdrop(self, creator_id: str, amount: float, token: str, duration: str, max_winners: int, amount_type: str = "token", channel_id: str = None) -> str:
        """Create a FatTips airdrop

        Args:
            creator_id: Discord user ID creating the airdrop
            amount: Total amount for the airdrop
            token: Token to airdrop
            duration: Duration string (e.g., "10m", "1h")
            max_winners: Maximum number of winners
            amount_type: "token" or "usd"
            channel_id: Discord channel ID to post the airdrop message with claim button (optional)

        Returns:
            Success message with airdrop ID or error
        """
        if not self._check_rate_limit("fattips_create_airdrop", creator_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED, FATTIPS_JAKEY_DISCORD_ID
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            creator = creator_id or FATTIPS_JAKEY_DISCORD_ID
            if not creator:
                return "❌ No creator ID configured for FatTips."

            result = await manager.create_airdrop(creator, amount, token, duration, max_winners, amount_type, channel_id)
            
            if "error" in result:
                error_msg = result['error']
                if "own wallet" in error_msg.lower():
                    return f"❌ **Airdrop creation failed**: The FatTips API key is tied to a different wallet. Airdrops can only be created from the wallet that owns the API key.\n\n**Fix options:**\n1. Use an API key from Jakey's FatTips wallet\n2. Or create the airdrop directly via FatTips dashboard"
                return f"❌ Airdrop creation failed: {error_msg}"
            
            response = f"🎁 **Airdrop created successfully!**\nID: `{result['airdropId']}`\nPot: {result['potSize']} {result['token']} (~${result['totalUsd']:.2f})\nMax Winners: {result.get('maxWinners', result.get('max_winners', 'Unlimited'))}\nExpires: {result.get('expiresAt', 'Unknown')}"
            
            if channel_id:
                response += "\n\n✅ **Airdrop message with claim button will be posted in this channel by the FatTips bot!**"
            
            return response
        except Exception as e:
            logger.error(f"Error in fattips_create_airdrop: {e}")
            return f"❌ Error creating airdrop: {str(e)}"

    async def fattips_claim_airdrop(self, airdrop_id: str, user_id: str) -> str:
        """Claim a FatTips airdrop

        Args:
            airdrop_id: ID of the airdrop to claim
            user_id: Discord user ID claiming the airdrop

        Returns:
            Success message with claim details or error
        """
        if not self._check_rate_limit("fattips_claim_airdrop", user_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            result = await manager.claim_airdrop(airdrop_id, user_id)
            
            if "error" in result:
                return f"❌ Airdrop claim failed: {result['error']}"
            
            return f"🎉 **Airdrop claimed!**\nYou received: {result['amountReceived']:.4f} tokens\n[View on Solscan]({result.get('solscanUrl', '#')})"
        except Exception as e:
            logger.error(f"Error in fattips_claim_airdrop: {e}")
            return f"❌ Error claiming airdrop: {str(e)}"

    async def fattips_list_airdrops(self, status: str = "ACTIVE", limit: int = 10) -> str:
        """List available FatTips airdrops

        Args:
            status: Filter by status (ACTIVE, EXPIRED, SETTLED, RECLAIMED)
            limit: Number of results to return

        Returns:
            Formatted list of airdrops or error message
        """
        try:
            from config import FATTIPS_ENABLED
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            result = await manager.list_airdrops(status, limit)
            
            if "error" in result:
                return f"❌ Failed to list airdrops: {result['error']}"
            
            airdrops = result.get('airdrops', [])
            total = result.get('total', 0)
            
            if not airdrops:
                return f"📭 No {status.lower()} airdrops found."
            
            lines = [f"🎁 **{status.title()} Airdrops** (showing {len(airdrops)} of {total}):\n"]
            
            for drop in airdrops:
                lines.append(f"ID: `{drop['id']}`")
                lines.append(f"  Pot: {drop['potSize']} tokens")
                lines.append(f"  Participants: {drop['participantCount']}/{drop['maxParticipants']}")
                lines.append(f"  Expires: {drop.get('expiresAt', 'Unknown')}")
                lines.append("")
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error in fattips_list_airdrops: {e}")
            return f"❌ Error listing airdrops: {str(e)}"

    async def fattips_create_rain(self, creator_id: str, amount: float, token: str, winners: list, amount_type: str = "token") -> str:
        """Create a FatTips rain (trivia winners, etc.)

        Args:
            creator_id: Discord user ID creating the rain
            amount: Total amount to rain
            token: Token to rain
            winners: List of Discord user IDs who receive the rain
            amount_type: "token" or "usd"

        Returns:
            Success message with rain details or error
        """
        if not self._check_rate_limit("fattips_create_rain", creator_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED, FATTIPS_JAKEY_DISCORD_ID
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            creator = creator_id or FATTIPS_JAKEY_DISCORD_ID
            if not creator:
                return "❌ No creator ID configured for FatTips."

            result = await manager.create_rain(creator, amount, token, winners, amount_type)
            
            if "error" in result:
                return f"❌ Rain creation failed: {result['error']}"
            
            winner_list = [f"<@{w['discordId']}>" for w in result.get('winners', [])]
            
            return f"🌧️ **Rain sent successfully!**\nWinners: {', '.join(winner_list)}\nAmount per winner: {result['amountPerUser']:.4f} {result['token']}\nTotal: {result['totalAmountToken']} {result['token']} (~${result['totalAmountUsd']:.2f})\n[View on Solscan]({result.get('solscanUrl', '#')})"
        except Exception as e:
            logger.error(f"Error in fattips_create_rain: {e}")
            return f"❌ Error creating rain: {str(e)}"

    async def fattips_get_wallet(self, user_id: str) -> str:
        """Get a user's FatTips wallet information

        Args:
            user_id: Discord user ID

        Returns:
            Wallet information or error message
        """
        if not self._check_rate_limit("fattips_get_wallet", user_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            result = await manager.get_wallet(user_id)
            
            if "error" in result:
                return f"❌ Wallet lookup failed: {result['error']}"
            
            pubkey = result.get('walletPubkey', 'Unknown')
            has_mnemonic = result.get('hasMnemonic', False)
            created = result.get('createdAt', 'Unknown')
            
            return f"💼 **Wallet Info**\nPublic Key: `{pubkey}`\nHas Recovery Phrase: {'Yes' if has_mnemonic else 'No'}\nCreated: {created}"
        except Exception as e:
            logger.error(f"Error in fattips_get_wallet: {e}")
            return f"❌ Error getting wallet: {str(e)}"

    async def fattips_create_wallet(self, user_id: str) -> str:
        """Create a new FatTips wallet for a user

        Args:
            user_id: Discord user ID

        Returns:
            Success message with wallet details (WARNING: includes private key - handle carefully)
        """
        if not self._check_rate_limit("fattips_create_wallet", user_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            result = await manager.create_wallet(user_id)
            
            if "error" in result:
                return f"❌ Wallet creation failed: {result['error']}"
            
            # WARNING: This contains sensitive data - only show in DMs
            return f"⚠️ **Wallet Created!** (SENSITIVE DATA - CHECK DMs)\nPublic Key: `{result['walletPubkey']}`\n⚠️ Private key and recovery phrase have been sent via DM. NEVER share these!"
        except Exception as e:
            logger.error(f"Error in fattips_create_wallet: {e}")
            return f"❌ Error creating wallet: {str(e)}"

    async def fattips_get_transactions(self, user_id: str, limit: int = 5) -> str:
        """Get a user's FatTips transaction history

        Args:
            user_id: Discord user ID
            limit: Number of transactions to retrieve (default: 5)

        Returns:
            Formatted transaction history or error message
        """
        if not self._check_rate_limit("fattips_get_transactions", user_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            return await manager.get_formatted_transactions(user_id, limit)
        except Exception as e:
            logger.error(f"Error in fattips_get_transactions: {e}")
            return f"❌ Error getting transactions: {str(e)}"

    async def fattips_withdraw(self, user_id: str, destination_address: str, amount: Optional[float], token: str = "SOL") -> str:
        """Withdraw funds to an external wallet

        Args:
            user_id: Discord user ID
            destination_address: External Solana wallet address
            amount: Amount to withdraw (None for max/all)
            token: Token to withdraw

        Returns:
            Success message with transaction details or error
        """
        if not self._check_rate_limit("fattips_withdraw", user_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED, FATTIPS_JAKEY_DISCORD_ID
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            withdraw_user = user_id or FATTIPS_JAKEY_DISCORD_ID
            if not withdraw_user:
                return "❌ No user ID configured for FatTips withdrawal."

            result = await manager.withdraw(withdraw_user, destination_address, amount, token)
            
            if "error" in result:
                return f"❌ Withdrawal failed: {result['error']}"
            
            amount_str = f"{result['amountToken']:.4f}" if result['amountToken'] else "ALL"
            
            return f"🏧 **Withdrawal successful!**\nAmount: {amount_str} {result['token']} (~${result['amountUsd']:.2f})\nTo: `{result['to']}`\n[View on Solscan]({result.get('solscanUrl', '#')})"
        except Exception as e:
            logger.error(f"Error in fattips_withdraw: {e}")
            return f"❌ Error withdrawing: {str(e)}"

    async def fattips_get_swap_quote(self, input_token: str, output_token: str, amount: float, amount_type: str = "token") -> str:
        """Get a quote for swapping tokens

        Args:
            input_token: Token to swap from (e.g., SOL)
            output_token: Token to swap to (e.g., USDC)
            amount: Amount to swap
            amount_type: "token" or "usd"

        Returns:
            Quote details or error message
        """
        try:
            from config import FATTIPS_ENABLED
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            result = await manager.get_swap_quote(input_token, output_token, amount, amount_type)
            
            if "error" in result:
                return f"❌ Quote failed: {result['error']}"
            
            return f"🔄 **Swap Quote**\n{result['inputAmount']} {result['inputToken']} → {result['outputAmount']:.4f} {result['outputToken']}\nInput Value: ${result['inputUsd']:.2f}\nOutput Value: ${result['outputUsd']:.2f}\nPrice Impact: {result.get('priceImpact', 0):.2f}%"
        except Exception as e:
            logger.error(f"Error in fattips_get_swap_quote: {e}")
            return f"❌ Error getting quote: {str(e)}"

    async def fattips_execute_swap(self, user_id: str, input_token: str, output_token: str, amount: float, amount_type: str = "token", slippage: float = 1.0) -> str:
        """Execute a token swap

        Args:
            user_id: Discord user ID
            input_token: Token to swap from
            output_token: Token to swap to
            amount: Amount to swap
            amount_type: "token" or "usd"
            slippage: Maximum slippage percentage (default: 1.0%)

        Returns:
            Success message with transaction details or error
        """
        if not self._check_rate_limit("fattips_execute_swap", user_id):
            return "⏰ Rate limit exceeded. Please wait a moment."

        try:
            from config import FATTIPS_ENABLED, FATTIPS_JAKEY_DISCORD_ID
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            swap_user = user_id or FATTIPS_JAKEY_DISCORD_ID
            if not swap_user:
                return "❌ No user ID configured for FatTips swap."

            result = await manager.execute_swap(swap_user, input_token, output_token, amount, amount_type, slippage)
            
            if "error" in result:
                return f"❌ Swap failed: {result['error']}"
            
            return f"🔄 **Swap executed!**\n{result['inputAmount']} {result['inputToken']} → {result['outputAmount']:.4f} {result['outputToken']}\nInput: ${result['inputUsd']:.2f} → Output: ${result['outputUsd']:.2f}\nPrice Impact: {result.get('priceImpact', 0):.2f}%\n[View on Solscan]({result.get('solscanUrl', '#')})"
        except Exception as e:
            logger.error(f"Error in fattips_execute_swap: {e}")
            return f"❌ Error executing swap: {str(e)}"

    async def fattips_get_leaderboard(self, type: str = "tippers", limit: int = 10) -> str:
        """Get FatTips leaderboard

        Args:
            type: Leaderboard type - "tippers" or "receivers"
            limit: Number of entries to show

        Returns:
            Formatted leaderboard or error message
        """
        try:
            from config import FATTIPS_ENABLED
            if not FATTIPS_ENABLED:
                return "❌ FatTips integration is disabled."

            from utils.fattips_manager import get_fattips_manager

            manager = get_fattips_manager()
            
            if type.lower() == "tippers":
                result = await manager.get_top_tippers(limit)
                title = "🏆 Top Tippers"
                value_key = "totalTippedUsd"
            else:
                result = await manager.get_top_receivers(limit)
                title = "🏆 Top Receivers"
                value_key = "totalReceivedUsd"
            
            if "error" in result:
                return f"❌ Failed to get leaderboard: {result['error']}"
            
            if not result:
                return f"📭 No {type} found on the leaderboard."
            
            lines = [f"{title}:\n"]
            
            for i, entry in enumerate(result[:limit], 1):
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"#{i}")
                user_id = entry.get('discordId', 'Unknown')
                value = entry.get(value_key, 0)
                lines.append(f"{medal} <@{user_id}>: ${value:.2f}")
            
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error in fattips_get_leaderboard: {e}")
            return f"❌ Error getting leaderboard: {str(e)}"


# Async helper functions for MCP operations
import asyncio


async def _run_mcp_with_context(
    user_id: str, information_type: str, information: str
) -> Dict[str, Any]:
    """Run MCP memory operation with proper context management"""
    from tools.mcp_memory_client import MCPMemoryClient

    async with MCPMemoryClient() as client:
        return await client.remember_user_info(user_id, information_type, information)


async def _run_mcp_search_with_context(
    user_id: str, query: Optional[str] = None
) -> Dict[str, Any]:
    """Run MCP memory search with proper context management"""
    from tools.mcp_memory_client import MCPMemoryClient

    async with MCPMemoryClient() as client:
        return await client.search_user_memory(user_id, query)


# Global tool manager instance
tool_manager = ToolManager()
