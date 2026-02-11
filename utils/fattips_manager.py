"""
FatTips API Manager for JakeySelfBot
Handles all FatTips API interactions including tipping, wallet management, airdrops, and rain
"""

import aiohttp
import asyncio
import os
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

from utils.logging_config import get_logger

logger = get_logger(__name__)


class FatTipsManager:
    """Manager for FatTips API interactions"""

    CURRENCY_NAMES = {
        "SOL": "Solana",
        "USDC": "USD Coin",
        "USDT": "Tether",
    }

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, bot_instance=None):
        self.bot = bot_instance
        self.api_key = api_key or os.getenv("FATTIPS_API_KEY")
        self.base_url = base_url or os.getenv("FATTIPS_API_URL", "https://codestats.gg/api")
        self.session: Optional[aiohttp.ClientSession] = None

        # Jakey's wallet info
        from config import FATTIPS_JAKEY_DISCORD_ID
        self.jakey_discord_id = FATTIPS_JAKEY_DISCORD_ID
        self._jakey_wallet_created = False
        self._jakey_balance_cache = None
        self._jakey_balance_cache_time = 0
        self._balance_cache_ttl = 30  # Cache balance for 30 seconds
        
        # Rate limiting
        self.last_call_time = {}
        self.rate_limits = {
            "health_check": 5.0,  # 5 seconds between health checks
            "get_user": 1.0,
            "create_wallet": 2.0,
            "get_wallet": 1.0,
            "delete_wallet": 2.0,
            "get_balance": 1.0,
            "send_tip": 1.0,
            "send_batch_tip": 2.0,
            "withdraw": 2.0,
            "get_transaction": 1.0,
            "get_user_transactions": 1.0,
            "create_airdrop": 2.0,
            "get_airdrop": 1.0,
            "claim_airdrop": 1.0,
            "list_airdrops": 1.0,
            "create_rain": 2.0,
            "get_swap_quote": 2.0,
            "execute_swap": 2.0,
            "get_supported_tokens": 60.0,  # Cache for 1 minute
            "get_leaderboard": 60.0,  # Cache for 1 minute
        }
        
        # Cache for expensive operations
        self._cache = {}
        self._cache_ttl = {
            "supported_tokens": 300,  # 5 minutes
            "leaderboard": 300,  # 5 minutes
        }

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _close_session(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def _check_rate_limit(self, operation: str) -> bool:
        """Check if operation can be performed based on rate limits"""
        current_time = asyncio.get_event_loop().time()
        if operation in self.last_call_time:
            time_since_last = current_time - self.last_call_time[operation]
            if time_since_last < self.rate_limits.get(operation, 1.0):
                return False
        self.last_call_time[operation] = current_time
        return True

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "JakeyBot/1.0"
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, operation: str = "") -> Dict[str, Any]:
        """Make an API request with error handling"""
        await self._ensure_session()
        
        if not self._check_rate_limit(operation or endpoint):
            return {"error": "Rate limit exceeded", "success": False}
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method, 
                url, 
                headers=self._get_headers(),
                json=data if data else None
            ) as response:
                if response.status == 200 or response.status == 201:
                    return await response.json()
                elif response.status == 401:
                    return {"error": "Unauthorized - Invalid API key", "success": False}
                elif response.status == 403:
                    error_data = await response.json()
                    return {"error": error_data.get("error", "Forbidden - API key can only access its own wallet"), "success": False}
                elif response.status == 404:
                    return {"error": "Resource not found", "success": False}
                elif response.status == 400:
                    error_data = await response.json()
                    return {"error": error_data.get("error", "Bad request"), "success": False}
                else:
                    return {"error": f"HTTP {response.status}", "success": False}
        except aiohttp.ClientError as e:
            logger.error(f"FatTips API request failed: {e}")
            return {"error": f"Network error: {str(e)}", "success": False}
        except Exception as e:
            logger.error(f"Unexpected error in FatTips API request: {e}")
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    # Health Check
    async def health_check(self) -> Dict[str, Any]:
        """Check if FatTips API is healthy"""
        return await self._make_request("GET", "/health", operation="health_check")

    # User Operations
    async def get_user(self, discord_id: str) -> Dict[str, Any]:
        """Get user information by Discord ID"""
        return await self._make_request("GET", f"/api/users/{discord_id}", operation="get_user")

    # Wallet Operations
    async def create_wallet(self, discord_id: str) -> Dict[str, Any]:
        """Create a new wallet for a Discord user"""
        return await self._make_request(
            "POST", 
            "/api/wallet/create", 
            data={"discordId": discord_id},
            operation="create_wallet"
        )

    async def get_wallet(self, discord_id: str) -> Dict[str, Any]:
        """Get wallet information for a Discord user"""
        return await self._make_request("GET", f"/api/wallet/{discord_id}", operation="get_wallet")

    async def delete_wallet(self, discord_id: str) -> Dict[str, Any]:
        """Delete a user's wallet"""
        return await self._make_request("DELETE", f"/api/wallet/{discord_id}", operation="delete_wallet")

    # Balance Operations
    async def get_balance(self, discord_id: str) -> Dict[str, Any]:
        """Get user's token balances (SOL, USDC, USDT)"""
        return await self._make_request("GET", f"/api/balance/{discord_id}", operation="get_balance")

    # Security check helper
    def _verify_jakey_only(self, sender_id: str, operation: str) -> Optional[Dict[str, Any]]:
        """Verify that only Jakey's wallet can be used for spending operations"""
        if not self.jakey_discord_id:
            return {"error": "Jakey Discord ID not configured", "success": False}
        
        if sender_id != self.jakey_discord_id:
            logger.warning(f"SECURITY BLOCK: Attempted {operation} from wallet {sender_id} but Jakey can only spend from his own wallet ({self.jakey_discord_id})")
            return {"error": f"Jakey can only spend from his own wallet. Cannot spend from {sender_id}", "success": False}
        
        return None  # No error, allowed

    # Tip Operations
    async def send_tip(
        self, 
        from_discord_id: str, 
        to_discord_id: str, 
        amount: float, 
        token: str = "SOL",
        amount_type: str = "token"
    ) -> Dict[str, Any]:
        """Send a tip to a single user"""
        data = {
            "fromDiscordId": from_discord_id,
            "toDiscordId": to_discord_id,
            "amount": amount,
            "token": token.upper(),
            "amountType": amount_type
        }
        return await self._make_request("POST", "/api/send/tip", data=data, operation="send_tip")

    async def send_batch_tip(
        self, 
        from_discord_id: str, 
        recipients: List[str], 
        total_amount: float, 
        token: str = "SOL",
        amount_type: str = "token"
    ) -> Dict[str, Any]:
        """Send tips to multiple users (Rain)"""
        recipient_list = [{"discordId": rid} for rid in recipients]
        data = {
            "fromDiscordId": from_discord_id,
            "recipients": recipient_list,
            "totalAmount": total_amount,
            "token": token.upper(),
            "amountType": amount_type
        }
        return await self._make_request("POST", "/api/send/batch-tip", data=data, operation="send_batch_tip")

    async def withdraw(
        self, 
        discord_id: str, 
        destination_address: str, 
        amount: Optional[float], 
        token: str = "SOL"
    ) -> Dict[str, Any]:
        """Withdraw funds to an external wallet"""
        data = {
            "discordId": discord_id,
            "destinationAddress": destination_address,
            "amount": amount,
            "token": token.upper()
        }
        return await self._make_request("POST", "/api/send/withdraw", data=data, operation="withdraw")

    # Transaction Operations
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Get transaction details by ID or signature"""
        return await self._make_request("GET", f"/api/transactions/{transaction_id}", operation="get_transaction")

    async def get_user_transactions(self, discord_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's transaction history"""
        params = f"?limit={limit}&offset={offset}"
        return await self._make_request(
            "GET", 
            f"/api/transactions/user/{discord_id}{params}", 
            operation="get_user_transactions"
        )

    # Airdrop Operations
    async def create_airdrop(
        self, 
        creator_discord_id: str, 
        amount: float, 
        token: str, 
        duration: str, 
        max_winners: int,
        amount_type: str = "token",
        channel_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new airdrop"""
        data = {
            "creatorDiscordId": creator_discord_id,
            "amount": amount,
            "token": token.upper(),
            "duration": duration,
            "maxWinners": max_winners,
            "amountType": amount_type
        }
        if channel_id:
            data["channelId"] = channel_id
        return await self._make_request("POST", "/api/airdrops/create", data=data, operation="create_airdrop")

    async def get_airdrop(self, airdrop_id: str) -> Dict[str, Any]:
        """Get airdrop details"""
        return await self._make_request("GET", f"/api/airdrops/{airdrop_id}", operation="get_airdrop")

    async def claim_airdrop(self, airdrop_id: str, discord_id: str) -> Dict[str, Any]:
        """Claim an airdrop"""
        data = {"discordId": discord_id}
        return await self._make_request("POST", f"/api/airdrops/{airdrop_id}/claim", data=data, operation="claim_airdrop")

    async def list_airdrops(self, status: Optional[str] = None, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """List active/expired airdrops"""
        params = f"?limit={limit}&offset={offset}"
        if status:
            params += f"&status={status}"
        return await self._make_request("GET", f"/api/airdrops{params}", operation="list_airdrops")

    # Rain Operations
    async def create_rain(
        self, 
        creator_discord_id: str, 
        amount: float, 
        token: str, 
        winners: List[str],
        amount_type: str = "token"
    ) -> Dict[str, Any]:
        """Create a rain (send to specific winners)"""
        data = {
            "creatorDiscordId": creator_discord_id,
            "amount": amount,
            "token": token.upper(),
            "winners": winners,
            "amountType": amount_type
        }
        return await self._make_request("POST", "/api/rain/create", data=data, operation="create_rain")

    # Swap Operations
    async def get_swap_quote(
        self, 
        input_token: str, 
        output_token: str, 
        amount: float, 
        amount_type: str = "token"
    ) -> Dict[str, Any]:
        """Get a swap quote"""
        params = f"?inputToken={input_token}&outputToken={output_token}&amount={amount}&amountType={amount_type}"
        return await self._make_request("GET", f"/api/swap/quote{params}", operation="get_swap_quote")

    async def execute_swap(
        self, 
        discord_id: str, 
        input_token: str, 
        output_token: str, 
        amount: float,
        amount_type: str = "token",
        slippage: float = 1.0
    ) -> Dict[str, Any]:
        """Execute a token swap"""
        data = {
            "discordId": discord_id,
            "inputToken": input_token.upper(),
            "outputToken": output_token.upper(),
            "amount": amount,
            "amountType": amount_type,
            "slippage": slippage
        }
        return await self._make_request("POST", "/api/swap/execute", data=data, operation="execute_swap")

    async def get_supported_tokens(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get list of supported tokens for swapping"""
        cache_key = "supported_tokens"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if asyncio.get_event_loop().time() - cached_time < self._cache_ttl.get(cache_key, 300):
                return cached_data
        
        result = await self._make_request("GET", "/api/swap/supported-tokens", operation="get_supported_tokens")
        
        # Update cache
        if "error" not in result:
            self._cache[cache_key] = (asyncio.get_event_loop().time(), result)
        
        return result

    # Leaderboard Operations
    async def get_top_tippers(self, limit: int = 10, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get top tippers leaderboard"""
        cache_key = "top_tippers"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if asyncio.get_event_loop().time() - cached_time < self._cache_ttl.get("leaderboard", 300):
                return cached_data
        
        result = await self._make_request("GET", f"/api/leaderboard/top-tippers?limit={limit}", operation="get_leaderboard")
        
        # Update cache
        if isinstance(result, list):
            self._cache[cache_key] = (asyncio.get_event_loop().time(), result)
        
        return result

    async def get_top_receivers(self, limit: int = 10, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get top receivers leaderboard"""
        cache_key = "top_receivers"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if asyncio.get_event_loop().time() - cached_time < self._cache_ttl.get("leaderboard", 300):
                return cached_data
        
        result = await self._make_request("GET", f"/api/leaderboard/top-receivers?limit={limit}", operation="get_leaderboard")
        
        # Update cache
        if isinstance(result, list):
            self._cache[cache_key] = (asyncio.get_event_loop().time(), result)
        
        return result

    # Utility Methods
    async def has_wallet(self, discord_id: str) -> bool:
        """Check if a user has a wallet"""
        wallet = await self.get_wallet(discord_id)
        return wallet.get("success", True) and "walletPubkey" in wallet

    async def get_formatted_balance(self, discord_id: str) -> str:
        """Get formatted balance string for display"""
        balance = await self.get_balance(discord_id)
        
        if "error" in balance:
            return f"💀 **Error**: {balance['error']}"
        
        if "balances" not in balance:
            return "💀 **No wallet found** - Use `%fattipswallet create` to create one"
        
        balances = balance.get("balances", {})
        wallet_pubkey = balance.get("walletPubkey", "Unknown")[:8] + "..."
        
        if not balances:
            return f"💰 **Wallet**: `{wallet_pubkey}`\n📭 **No balances**"
        
        lines = [f"💰 **Wallet**: `{wallet_pubkey}`\n"]

        for token, amount in balances.items():
            token_upper = token.upper()
            currency_name = self.CURRENCY_NAMES.get(token_upper, token_upper)
            lines.append(f"**{currency_name} ({token_upper})**: {amount:.4f}")

        return "\n".join(lines)

    async def format_transaction(self, tx: Dict[str, Any]) -> str:
        """Format a single transaction for display"""
        tx_type = tx.get("txType", "UNKNOWN")
        status = tx.get("status", "UNKNOWN")
        amount = tx.get("amount", 0)
        token = tx.get("token", "SOL")
        amount_usd = tx.get("amountUsd", 0)
        from_id = tx.get("fromId", "?")
        to_id = tx.get("toId", "?")
        
        emoji_map = {
            "TIP": "💸",
            "AIRDROP": "🎁",
            "WITHDRAW": "🏧",
            "DEPOSIT": "💰",
            "SWAP": "🔄",
            "RAIN": "🌧️"
        }
        
        emoji = emoji_map.get(tx_type, "💱")
        status_emoji = "✅" if status == "CONFIRMED" else "⏳" if status == "PENDING" else "❌"

        token_upper = token.upper()
        currency_name = self.CURRENCY_NAMES.get(token_upper, token_upper)

        result = f"{emoji} {status_emoji} **{tx_type.title()}**: {amount:.4f} {currency_name} ({token_upper}) (~${amount_usd:.2f})"
        
        if from_id and from_id != "?":
            result += f"\n   From: <@{from_id}>"
        if to_id and to_id != "?":
            result += f"\n   To: <@{to_id}>"
        
        return result

    async def get_formatted_transactions(self, discord_id: str, limit: int = 5) -> str:
        """Get formatted transaction history"""
        transactions = await self.get_user_transactions(discord_id, limit=limit)
        
        if isinstance(transactions, dict) and "error" in transactions:
            return f"💀 **Error**: {transactions['error']}"
        
        if not transactions:
            return "📭 **No transactions found**"
        
        lines = [f"📊 **Recent Transactions** (last {len(transactions)}):\n"]
        
        for tx in transactions:
            lines.append(await self.format_transaction(tx))
            lines.append("")  # Empty line between transactions
        
        return "\n".join(lines)

    # Jakey-specific methods
    async def ensure_jakey_wallet(self) -> Dict[str, Any]:
        """Ensure Jakey has a FatTips wallet, create one if not exists"""
        if not self.jakey_discord_id:
            logger.warning("FATTIPS_JAKEY_DISCORD_ID not configured, cannot create wallet")
            return {"error": "Jakey Discord ID not configured"}
        
        # Check if wallet exists
        wallet = await self.get_wallet(self.jakey_discord_id)
        if wallet.get("walletPubkey"):
            self._jakey_wallet_created = True
            logger.info(f"Jakey already has FatTips wallet: {wallet['walletPubkey'][:8]}...")
            return {"success": True, "wallet": wallet, "created": False}
        
        # Create wallet for Jakey
        logger.info("Creating FatTips wallet for Jakey...")
        new_wallet = await self.create_wallet(self.jakey_discord_id)
        
        if "error" in new_wallet:
            # Check if wallet already exists (not actually an error)
            if "already has" in new_wallet['error'].lower() or "already exists" in new_wallet['error'].lower():
                logger.info(f"Jakey already has a FatTips wallet (detected on creation attempt)")
                self._jakey_wallet_created = True
                return {"success": True, "wallet": None, "created": False, "already_exists": True}
            logger.error(f"Failed to create Jakey's wallet: {new_wallet['error']}")
            return {"error": new_wallet['error']}
        
        self._jakey_wallet_created = True
        logger.info(f"Created FatTips wallet for Jakey: {new_wallet.get('walletPubkey', 'unknown')[:8]}...")
        
        # Log the private key for the user to save securely
        if "privateKey" in new_wallet:
            logger.warning("=" * 60)
            logger.warning("JAKEY'S FATTIPS WALLET CREATED - SAVE THIS SECURELY:")
            logger.warning(f"Public Key: {new_wallet.get('walletPubkey', 'N/A')}")
            logger.warning(f"Private Key: {new_wallet.get('privateKey', 'N/A')[:20]}...")
            logger.warning(f"Mnemonic: {new_wallet.get('mnemonic', 'N/A').split()[:3]}...")
            logger.warning("=" * 60)
        
        return {"success": True, "wallet": new_wallet, "created": True}
    
    async def get_jakey_balance(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get Jakey's FatTips balance with caching"""
        if not self.jakey_discord_id:
            return {"error": "Jakey Discord ID not configured"}
        
        # Check cache
        current_time = asyncio.get_event_loop().time()
        if use_cache and self._jakey_balance_cache is not None:
            if current_time - self._jakey_balance_cache_time < self._balance_cache_ttl:
                return self._jakey_balance_cache
        
        # Fetch fresh balance
        balance = await self.get_balance(self.jakey_discord_id)
        
        # If wallet doesn't exist (and we haven't created it yet), try to create it now
        if "error" in balance and "not found" in balance["error"].lower() and not self._jakey_wallet_created:
            logger.info("Wallet not found on balance check, attempting to create...")
            wallet_result = await self.ensure_jakey_wallet()
            if wallet_result.get("success"):
                # Try getting balance again after wallet creation
                balance = await self.get_balance(self.jakey_discord_id)
        
        # Update cache
        self._jakey_balance_cache = balance
        self._jakey_balance_cache_time = current_time
        
        return balance
    
    async def get_jakey_formatted_balance(self) -> str:
        """Get Jakey's formatted balance string"""
        balance = await self.get_jakey_balance()
        
        if "error" in balance:
            if "not found" in balance["error"].lower():
                return "💀 **No FatTips wallet yet** - Jakey needs a wallet created!"
            return f"💀 **Error**: {balance['error']}"
        
        if "balances" not in balance:
            return "💀 **No FatTips wallet found** - Create one first!"
        
        balances = balance.get("balances", {})
        wallet_pubkey = balance.get("walletPubkey", "Unknown")
        
        if not balances:
            return f"💰 **Jakey's FatTips Wallet**: `{wallet_pubkey[:8]}...`\n📭 **Balance**: 0 {self.CURRENCY_NAMES.get('SOL', 'SOL')} (Empty wallet)"
        
        lines = [f"💰 **Jakey's FatTips Wallet**: `{wallet_pubkey}`\n"]

        for token, amount in balances.items():
            token_upper = token.upper()
            currency_name = self.CURRENCY_NAMES.get(token_upper, token_upper)
            lines.append(f"**{currency_name} ({token_upper})**: {amount:.4f}")

        return "\n".join(lines)


# Global FatTips manager instance
_fattips_manager = None


def get_fattips_manager(api_key: Optional[str] = None, base_url: Optional[str] = None, bot_instance=None) -> FatTipsManager:
    """Get or create the global FatTips manager instance"""
    global _fattips_manager
    if _fattips_manager is None:
        _fattips_manager = FatTipsManager(api_key, base_url, bot_instance)
    return _fattips_manager


def init_fattips_manager(api_key: Optional[str] = None, base_url: Optional[str] = None, bot_instance=None) -> FatTipsManager:
    """Initialize the global FatTips manager"""
    global _fattips_manager
    _fattips_manager = FatTipsManager(api_key, base_url, bot_instance)
    return _fattips_manager
