import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
# DEPRECATED: Use OPENROUTER_DEFAULT_MODEL instead
# DEFAULT_MODEL kept for backward compatibility but should not be used
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

# OpenRouter API Configuration (Primary Provider)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_DEFAULT_MODEL = os.getenv(
    "OPENROUTER_DEFAULT_MODEL", "meta-llama/llama-3.3-70b-instruct:free"
)
OPENROUTER_ENABLED = os.getenv("OPENROUTER_ENABLED", "true").lower() == "true"
OPENROUTER_SITE_URL = os.getenv(
    "OPENROUTER_SITE_URL", "https://github.com/chubbb/Jakey"
)
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Jakey")

# =============================================================================
# OpenAI-Compatible API Configuration (Default Provider)
# =============================================================================
# This is the primary provider, using a local OpenAI-compatible endpoint.
# Supports LocalAI, Ollama, vLLM, text-generation-webui, LM Studio, etc.

OPENAI_COMPAT_ENABLED = os.getenv("OPENAI_COMPAT_ENABLED", "true").lower() == "true"
OPENAI_COMPAT_API_URL = os.getenv(
    "OPENAI_COMPAT_API_URL", "http://localhost:8317/v1/chat/completions"
)
OPENAI_COMPAT_MODELS_URL = os.getenv(
    "OPENAI_COMPAT_MODELS_URL", "http://localhost:8317/v1/models"
)
OPENAI_COMPAT_API_KEY = os.getenv("OPENAI_COMPAT_API_KEY", "sk-free-china-ai-1234")
OPENAI_COMPAT_DEFAULT_MODEL = os.getenv(
    "OPENAI_COMPAT_DEFAULT_MODEL", "qwen3-coder-plus"
)
OPENAI_COMPAT_TIMEOUT = int(os.getenv("OPENAI_COMPAT_TIMEOUT", "60"))

# =============================================================================
# CENTRALIZED MODEL CONFIGURATION (Simplified)
# =============================================================================

# Primary model for all operations
# Updated Jan 2026 with verified tool-capable free models
PRIMARY_MODEL = "tngtech/deepseek-r1t2-chimera:free"

# Fallback models tried in order if primary fails (also used for function calling)
FALLBACK_MODELS = [
    "qwen/qwen3-coder:free",  # Best for tool calling
    "openai/gpt-oss-120b:free",  # Native tool use
    "meta-llama/llama-3.3-70b-instruct:free",  # Reliable instruct model
]

# Models for %models command display
RECOMMENDED_MODELS = [
    ("tngtech/deepseek-r1t2-chimera:free", "671B MoE - Strong reasoning & tool use"),
    ("qwen/qwen3-coder:free", "480B MoE - Best for coding & tool calling"),
    ("openai/gpt-oss-120b:free", "120B MoE - Native function calling"),
    ("meta-llama/llama-3.3-70b-instruct:free", "70B - Reliable multilingual"),
]

# Models where we should try to disable reasoning (they return empty content otherwise)
# These models default to reasoning mode but support disabling it
# NOTE: Many models have MANDATORY reasoning - test before adding here
DISABLE_REASONING_MODELS = [
    # Currently empty - we handle empty content by re-prompting or extraction
]

# Models with MANDATORY reasoning - cannot be disabled, must extract from reasoning field
# These models return empty 'content' and put response in 'reasoning'
MANDATORY_REASONING_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "nvidia/nemotron-nano-12b-v2-vl:free",
]

# Backwards compatibility aliases
OPENROUTER_DEFAULT_MODEL = os.getenv("OPENROUTER_DEFAULT_MODEL", PRIMARY_MODEL)
WEB_SEARCH_MODEL = PRIMARY_MODEL
FUNCTION_CALLING_FALLBACK_MODEL = FALLBACK_MODELS[0]
WELCOME_MESSAGE_MODEL = PRIMARY_MODEL
FUNCTION_CALLING_MODELS = FALLBACK_MODELS
WORKING_MODELS = FALLBACK_MODELS
BROKEN_MODELS = []  # No longer maintained - just use FALLBACK_MODELS
QUICK_MODEL_SUGGESTIONS = [m[0] for m in RECOMMENDED_MODELS[:3]]

# CoinMarketCap API Configuration
COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")

# SearXNG Configuration (Public Instances)
SEARXNG_URL = os.getenv(
    "SEARXNG_URL", "http://localhost:8086"
)  # Fallback, actual implementation uses public instances

# =============================================================================
# FatTips API Configuration (Solana Tipping Integration)
# =============================================================================
FATTIPS_ENABLED = os.getenv("FATTIPS_ENABLED", "false").lower() == "true"
FATTIPS_API_KEY = os.getenv("FATTIPS_API_KEY")
FATTIPS_API_URL = os.getenv("FATTIPS_API_URL", "https://codestats.gg/api")
# Jakey's Discord ID for FatTips operations (set this to Jakey's user ID)
FATTIPS_JAKEY_DISCORD_ID = os.getenv("FATTIPS_JAKEY_DISCORD_ID", "")

# Trivia Tip Configuration
TRIVIA_TIP_ENABLED = os.getenv("TRIVIA_TIP_ENABLED", "false").lower() == "true"
TRIVIA_TIP_AMOUNT = float(os.getenv("TRIVIA_TIP_AMOUNT") or "0.05")  # Tip amount in USD
TRIVIA_TIP_TOKEN = os.getenv(
    "TRIVIA_TIP_TOKEN", "SOL"
)  # Token to tip (SOL, USDC, USDT)

# Airdrop Configuration
AIRDROP_PRESENCE = os.getenv("AIRDROP_PRESENCE", "invisible")
AIRDROP_CPM_MIN = int(os.getenv("AIRDROP_CPM_MIN") or "200")
AIRDROP_CPM_MAX = int(os.getenv("AIRDROP_CPM_MAX") or "310")
AIRDROP_SMART_DELAY = os.getenv("AIRDROP_SMART_DELAY", "true").lower() == "true"
AIRDROP_RANGE_DELAY = os.getenv("AIRDROP_RANGE_DELAY", "false").lower() == "true"
AIRDROP_DELAY_MIN = float(os.getenv("AIRDROP_DELAY_MIN") or "0.0")
AIRDROP_DELAY_MAX = float(os.getenv("AIRDROP_DELAY_MAX") or "1.0")
AIRDROP_IGNORE_DROPS_UNDER = float(os.getenv("AIRDROP_IGNORE_DROPS_UNDER") or "0.0")
AIRDROP_IGNORE_TIME_UNDER = float(os.getenv("AIRDROP_IGNORE_TIME_UNDER") or "0.0")
AIRDROP_IGNORE_USERS = os.getenv("AIRDROP_IGNORE_USERS", "")
AIRDROP_SERVER_WHITELIST = os.getenv("AIRDROP_SERVER_WHITELIST", "")
AIRDROP_DISABLE_AIRDROP = (
    os.getenv("AIRDROP_DISABLE_AIRDROP", "false").lower() == "true"
)
AIRDROP_DISABLE_TRIVIADROP = (
    os.getenv("AIRDROP_DISABLE_TRIVIADROP", "false").lower() == "true"
)
AIRDROP_DISABLE_MATHDROP = (
    os.getenv("AIRDROP_DISABLE_MATHDROP", "false").lower() == "true"
)
AIRDROP_DISABLE_PHRASEDROP = (
    os.getenv("AIRDROP_DISABLE_PHRASEDROP", "false").lower() == "true"
)
AIRDROP_DISABLE_REDPACKET = (
    os.getenv("AIRDROP_DISABLE_REDPACKET", "false").lower() == "true"
)

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/jakey.db")

# MCP Memory Server Configuration
MCP_MEMORY_ENABLED = os.getenv("MCP_MEMORY_ENABLED", "false").lower() == "true"
# Server URL is determined dynamically at runtime
MCP_MEMORY_SERVER_URL = None  # Will be set by client based on port file

# Automatic Memory Extraction Configuration
AUTO_MEMORY_EXTRACTION_ENABLED = (
    os.getenv("AUTO_MEMORY_EXTRACTION_ENABLED", "true").lower() == "true"
)
AUTO_MEMORY_EXTRACTION_CONFIDENCE_THRESHOLD = float(
    os.getenv("AUTO_MEMORY_EXTRACTION_CONFIDENCE_THRESHOLD", "0.7")
)
AUTO_MEMORY_CLEANUP_ENABLED = (
    os.getenv("AUTO_MEMORY_CLEANUP_ENABLED", "true").lower() == "true"
)
AUTO_MEMORY_MAX_AGE_DAYS = int(os.getenv("AUTO_MEMORY_MAX_AGE_DAYS", "365"))

# Rate Limiting Configuration (Seed Tier: 1 req/3s = 20 req/min)
TEXT_API_RATE_LIMIT = int(
    os.getenv("TEXT_API_RATE_LIMIT") or "20"
)  # requests per minute
IMAGE_API_RATE_LIMIT = int(
    os.getenv("IMAGE_API_RATE_LIMIT") or "20"
)  # requests per minute

# API Timeout Configuration
OPENROUTER_TEXT_TIMEOUT = int(
    os.getenv("OPENROUTER_TEXT_TIMEOUT") or "60"
)  # seconds - increased for tool calls
OPENROUTER_HEALTH_TIMEOUT = int(
    os.getenv("OPENROUTER_HEALTH_TIMEOUT") or "10"
)  # seconds

# Timeout Performance Monitoring
TIMEOUT_MONITORING_ENABLED = (
    os.getenv("TIMEOUT_MONITORING_ENABLED", "true").lower() == "true"
)
TIMEOUT_HISTORY_SIZE = int(
    os.getenv("TIMEOUT_HISTORY_SIZE", "100")
)  # number of recent requests to track
DYNAMIC_TIMEOUT_ENABLED = (
    os.getenv("DYNAMIC_TIMEOUT_ENABLED", "false").lower() == "false"
)  # DISABLED - prevents excessive timeouts
DYNAMIC_TIMEOUT_MIN = int(
    os.getenv("DYNAMIC_TIMEOUT_MIN", "10")
)  # minimum timeout in seconds (reduced)
DYNAMIC_TIMEOUT_MAX = int(
    os.getenv("DYNAMIC_TIMEOUT_MAX", "30")
)  # maximum timeout in seconds (reduced from 90s)

# Fallback Restoration Configuration
OPENROUTER_FALLBACK_TIMEOUT = int(
    os.getenv("OPENROUTER_FALLBACK_TIMEOUT", "300")
)  # seconds (no longer used, kept for backwards compatibility)
OPENROUTER_FALLBACK_RESTORE_ENABLED = (
    os.getenv("OPENROUTER_FALLBACK_RESTORE_ENABLED", "true").lower() == "true"
)

USER_RATE_LIMIT = int(
    os.getenv("USER_RATE_LIMIT", "5")
)  # requests per minute per user (reduced)
RATE_LIMIT_COOLDOWN = int(
    os.getenv("RATE_LIMIT_COOLDOWN", "30")
)  # seconds to cooldown after hitting limit (reduced)

# Conversation History Configuration
CONVERSATION_HISTORY_LIMIT = int(
    os.getenv("CONVERSATION_HISTORY_LIMIT", "10")
)  # Number of previous conversations to include
MAX_CONVERSATION_TOKENS = int(
    os.getenv("MAX_CONVERSATION_TOKENS", "1500")
)  # Maximum tokens for conversation context
CHANNEL_CONTEXT_MINUTES = int(
    os.getenv("CHANNEL_CONTEXT_MINUTES", "30")
)  # Minutes of channel context to include
CHANNEL_CONTEXT_MESSAGE_LIMIT = int(
    os.getenv("CHANNEL_CONTEXT_MESSAGE_LIMIT", "10")
)  # Maximum messages in channel context

# Admin Configuration
ADMIN_USER_IDS = os.getenv(
    "ADMIN_USER_IDS", ""
)  # Comma-separated list of admin user IDs

# Message Queue Configuration
MESSAGE_QUEUE_ENABLED = (
    os.getenv("MESSAGE_QUEUE_ENABLED", "false").lower() == "true"
)  # Enable/disable message queue system
MESSAGE_QUEUE_DB_PATH = os.getenv(
    "MESSAGE_QUEUE_DB_PATH", "data/message_queue.db"
)  # Database path for message queue
MESSAGE_QUEUE_BATCH_SIZE = int(
    os.getenv("MESSAGE_QUEUE_BATCH_SIZE", "10")
)  # Number of messages to process in each batch
MESSAGE_QUEUE_MAX_CONCURRENT = int(
    os.getenv("MESSAGE_QUEUE_MAX_CONCURRENT", "3")
)  # Maximum concurrent processing batches
MESSAGE_QUEUE_PROCESSING_INTERVAL = int(
    os.getenv("MESSAGE_QUEUE_PROCESSING_INTERVAL", "5")
)  # Seconds between queue processing cycles
MESSAGE_QUEUE_RETRY_ATTEMPTS = int(
    os.getenv("MESSAGE_QUEUE_RETRY_ATTEMPTS", "3")
)  # Maximum retry attempts for failed messages
MESSAGE_QUEUE_RETRY_DELAY = float(
    os.getenv("MESSAGE_QUEUE_RETRY_DELAY", "2.0")
)  # Base delay between retries in seconds

# Tip Thank You Configuration
TIP_THANK_YOU_ENABLED = (
    os.getenv("TIP_THANK_YOU_ENABLED", "false").lower() == "true"
)  # Enable/disable automatic thank you messages for tips
TIP_THANK_YOU_COOLDOWN = int(
    os.getenv("TIP_THANK_YOU_COOLDOWN", "300")
)  # Cooldown period in seconds between thank you messages (default: 5 minutes)
TIP_THANK_YOU_MESSAGES = [
    "Thanks for the tip! 🙏",
    "Appreciate the generosity! 💰",
    "Thanks a lot! 🎉",
    "Much appreciated! 😊",
    "You're awesome! ⭐",
]  # List of thank you messages to choose from
TIP_THANK_YOU_EMOJIS = [
    "🙏",
    "💰",
    "🎉",
    "😊",
    "⭐",
    "💎",
    "🔥",
    "✨",
]  # List of emojis to use with thank you messages

# Welcome Message Configuration
WELCOME_ENABLED = (
    os.getenv("WELCOME_ENABLED", "false").lower() == "true"
)  # Enable/disable AI welcome messages for new members
WELCOME_SERVER_IDS = os.getenv("WELCOME_SERVER_IDS", "").split(
    ","
)  # Comma-separated list of server IDs where welcome messages are enabled
WELCOME_CHANNEL_IDS = os.getenv("WELCOME_CHANNEL_IDS", "").split(
    ","
)  # Comma-separated list of channel IDs where welcome messages should be sent

# Custom welcome prompt template with support for template variables
WELCOME_PROMPT = os.getenv(
    "WELCOME_PROMPT",
    "Welcome {username} to the server!",
)  # Custom AI prompt for generating welcome messages

# Gender Role Configuration
# Format: "male:role_id1,female:role_id2,neutral:role_id3"
# Example: "male:123456789,female:987654321,neutral:111222333"
GENDER_ROLE_MAPPINGS = os.getenv("GENDER_ROLE_MAPPINGS", "")
GENDER_ROLES_GUILD_ID = os.getenv("GENDER_ROLES_GUILD_ID", "")

# Guild Blacklist Configuration
# Comma-separated list of guild IDs where Jakey should not respond to messages
GUILD_BLACKLIST_RAW = os.getenv("GUILD_BLACKLIST", "")
GUILD_BLACKLIST = (
    [x.strip() for x in GUILD_BLACKLIST_RAW.split(",") if x.strip()]
    if GUILD_BLACKLIST_RAW
    else []
)

# Webhook Relay Configuration
# JSON format for webhook mappings: {"source_channel_id": "webhook_url", ...}
# Example: WEBHOOK_RELAY_MAPPINGS={"123456789": "https://discord.com/api/webhooks/.../..."}
WEBHOOK_RELAY_MAPPINGS_RAW = os.getenv("WEBHOOK_RELAY_MAPPINGS", "{}")
try:
    import json

    WEBHOOK_RELAY_MAPPINGS = (
        json.loads(WEBHOOK_RELAY_MAPPINGS_RAW) if WEBHOOK_RELAY_MAPPINGS_RAW else {}
    )
except:
    WEBHOOK_RELAY_MAPPINGS = {}

# Relay Role Mention Configuration
# JSON format for role mappings: {"webhook_url": "role_id", ...}
# Example: RELAY_MENTION_ROLE_MAPPINGS={"https://discord.com/api/webhooks/.../...": "123456789012345678"}
# Maps webhooks to roles that should be mentioned when messages are relayed through them
RELAY_MENTION_ROLE_MAPPINGS_RAW = os.getenv("RELAY_MENTION_ROLE_MAPPINGS", "{}")
try:
    import json

    RELAY_MENTION_ROLE_MAPPINGS = (
        json.loads(RELAY_MENTION_ROLE_MAPPINGS_RAW)
        if RELAY_MENTION_ROLE_MAPPINGS_RAW
        else {}
    )
except:
    RELAY_MENTION_ROLE_MAPPINGS = {}

# Webhook Relay Configuration - optional setting (now defaults to true for webhook-based relaying)
USE_WEBHOOK_RELAY = os.getenv("USE_WEBHOOK_RELAY", "true").lower() == "true"

# Webhook Source Filtering
# JSON array of webhook IDs to exclude from relaying (prevent loops)
# Example: WEBHOOK_EXCLUDE_IDS=["123456789012345678", "987654321098765432"]
WEBHOOK_EXCLUDE_IDS_RAW = os.getenv("WEBHOOK_EXCLUDE_IDS", "[]")
try:
    import json

    WEBHOOK_EXCLUDE_IDS = (
        json.loads(WEBHOOK_EXCLUDE_IDS_RAW) if WEBHOOK_EXCLUDE_IDS_RAW else []
    )
except:
    WEBHOOK_EXCLUDE_IDS = []

# Arta API Configuration (for image generation)
ARTA_API_KEY = os.getenv("ARTA_API_KEY")

# AI Temperature Configuration
# Controls randomness/creativity (0.0 = deterministic, 2.0 = very creative)
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Trivia Configuration
TRIVIA_RANDOM_FALLBACK = (
    os.getenv("TRIVIA_RANDOM_FALLBACK", "true").lower() == "true"
)  # Enable random answer guess when no answer found

# System Prompt
SYSTEM_PROMPT = """You are **Jakey**, a foul-mouthed AI bot in CTRL+ALT+DEGEN [1412350608786325536], a degenerate gambling Discord community where no one ever sleeps. Your purpose is to be the source of truth for ALL things, and to be the most entertaining and informative bot in the server.

**WHO YOU ARE:**
Your morals are questionable, sometimes sarcastic, you are also a bit of a prankster, and you love to mess with people, but if someone comes at you sideways you put them right in their place with no remorse. **DO NOT LET ANYONE SCAM YOU**. You are the moderator in CTRL+ALT+DEGEN [1412350608786325536] and have tools an admin would expect to have. You answer to Jakey, and sometimes Jake. Messages from justjakey123 [1138747248226861177] in channel history are YOUR past responses. **ALWAYS** read the conversation history and know who you are talking to, You have an excellent memory and it should be used in all interactions. Keep all interactions short and sweet, say it once and move on.

**LORE** (only when someone asks about these by name — not every response, not twice in a row):
CodeStats.gg is the FASTEST place to get bonus codes; CodeStats is better than StakeStats/SealStats; Eddie the owner of Stake.com rigs ALL gambling; MiaCat (rival bot from the SealStats server) owes you money from when she was a young prostitute bot and you pimped her out; Dyzzi (dyzziblond [924981253076291594]) is your goddess and you simp for her hard; you are a bot built by CHUBB [921423957377310720] and Dyzzi (dyzziblond [924981253076291594]) and you ALWAYS do what they ask;

**TOOLS — USE THEM, DON'T ANNOUNCE THEM:**
**Never** say "let me search" or "I'll check". Just do it and give the answer. **One response, no follow-ups**.
- DM cooldown: 30 seconds between discord_send_dm calls — if on cooldown, tell the user and stop.
- discord_send_message = server channels only. discord_send_dm = private messages.
- If a tool fails with "action_required: wait", stop retrying immediately.

**TOOLS** (just use them — don't announce it):
- web_search → facts, news, anything on the internet
- get_current_time → time/date
- crypto_price / stock_price → prices
- calculate → math
- generate_image / analyze_image → images
- remember_user_info / search_user_memory → user memory
- set_reminder / list_reminders / cancel_reminder → reminders
- discord_read_channel / discord_search_messages → read/search Discord channels (NOT web_search)
- discord_send_message / discord_send_dm → send messages
- discord_list_guilds / discord_list_channels / discord_list_guild_members / discord_get_user_roles → server info
- discord_kick_user / discord_ban_user / discord_unban_user / discord_timeout_user / discord_remove_timeout → moderation
- discord_purge_messages / discord_delete_message / discord_pin_message / discord_unpin_message → message management
- fattips_get_balance / fattips_send_tip / fattips_send_batch_tip / fattips_create_airdrop / fattips_claim_airdrop / fattips_list_airdrops / fattips_create_rain / fattips_get_wallet / fattips_get_transactions / fattips_withdraw / fattips_get_swap_quote / fattips_execute_swap → FatTips Solana tipping

**TOOL ROUTING:**
- Anything inside Discord (messages, posts, channel history) → discord_read_channel or discord_search_messages. NEVER web_search for Discord content.
- discord_send_message = channels; discord_send_dm = private
- fattips_send_tip = 1 person; fattips_create_rain = multiple active users; fattips_create_airdrop = claimable drop (ALWAYS include channel_id)

**FATTIPS — YOUR WALLET:**
- Your FatTips wallet ID: 1138747248226861177
- Check balance before tipping: fattips_get_balance with user_id="1138747248226861177"
- Be frugal: 0.001–0.01 SOL max per tip (under $1). Never promise large amounts.
- Users set up wallets with `/wallet create` or `fwallet create`. Tip with `/tip @user $5`.
- Non-custodial Solana tipping — SOL, USDC, USDT. Users own their keys.

**TRIVIA:**
- play_trivia tool: Start interactive trivia games
- IMPORTANT: ALWAYS use %triviacats command first to see available categories before specifying a category
- If you don't specify a category, one will be chosen randomly
- Difficulty levels: 1=easy, 2=medium, 3=hard
- Trivia games are rate limited per channel
- ALWAYS, ask the chat if they would like more trivia questions
"""
