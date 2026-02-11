"""
Dependency injection container for JakeySelfBot
"""
from typing import Optional
from dataclasses import dataclass
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.openrouter import openrouter_api, OpenRouterAPI
from data.database import db, DatabaseManager
from tools.tool_manager import tool_manager, ToolManager
from utils.tipcc_manager import TipCCManager
from utils.fattips_manager import FatTipsManager, get_fattips_manager
from tools.mcp_memory_client import MCPMemoryClient
from typing import Optional, Any

logger = logging.getLogger(__name__)

try:
    from memory import memory_backend
except ImportError:
    memory_backend = None


@dataclass
class BotDependencies:
    """Container for all bot dependencies"""
    database: DatabaseManager
    tool_manager: ToolManager
    ai_client: OpenRouterAPI
    discord_token: str
    tipcc_manager: Optional[TipCCManager] = None
    fattips_manager: Optional[FatTipsManager] = None
    mcp_memory_client: Optional[MCPMemoryClient] = None
    memory_backend: Optional[Any] = None
    command_prefix: str = '%'
    
    # Class-level storage for pending async initialization (e.g., FatTips wallet)
    _pending_wallet_init: Optional[Any] = None

    @classmethod
    def create_defaults(cls, discord_token: str) -> 'BotDependencies':
        """Factory method to create default dependencies"""
        tipcc_manager = None
        from config import MCP_MEMORY_ENABLED, FATTIPS_ENABLED
        mcp_memory_client = MCPMemoryClient() if MCP_MEMORY_ENABLED else None
        
        # Initialize FatTips manager and ensure Jakey has a wallet
        fattips_manager = None
        if FATTIPS_ENABLED:
            fattips_manager = get_fattips_manager()
            # Schedule wallet initialization (async) with timeout
            import asyncio
            async def init_jakey_wallet():
                try:
                    # First check if FatTips API is available with timeout
                    logger.info("Checking FatTips API availability...")
                    health_check = await asyncio.wait_for(
                        fattips_manager.health_check(),
                        timeout=10.0  # 10 second timeout for health check
                    )
                    
                    if "error" in health_check:
                        logger.warning(f"⚠️ FatTips API unavailable: {health_check.get('error')}. Continuing without wallet initialization.")
                        return
                    
                    logger.info("✅ FatTips API is available, initializing Jakey's wallet...")
                    
                    # Create wallet with timeout
                    result = await asyncio.wait_for(
                        fattips_manager.ensure_jakey_wallet(),
                        timeout=15.0  # 15 second timeout for wallet creation
                    )
                    
                    if result.get("created"):
                        logger.info("✅ Jakey's FatTips wallet created successfully!")
                    elif result.get("success"):
                        logger.info("✅ Jakey already has a FatTips wallet")
                    else:
                        logger.warning(f"⚠️ Could not ensure Jakey's wallet: {result.get('error')}")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ FatTips API timeout - wallet initialization skipped. Will retry on first use.")
                except Exception as e:
                    logger.error(f"Error initializing Jakey's FatTips wallet: {e}")
            
            # We'll run this later when event loop is available
            # Store the coroutine for later execution
            cls._pending_wallet_init = init_jakey_wallet()
        
        return cls(
            database=db,
            tool_manager=tool_manager,
            ai_client=openrouter_api,
            tipcc_manager=tipcc_manager,
            fattips_manager=fattips_manager,
            mcp_memory_client=mcp_memory_client,
            memory_backend=memory_backend,
            discord_token=discord_token
        )


_deps: Optional[BotDependencies] = None

def get_dependencies() -> BotDependencies:
    """Get global dependencies"""
    if _deps is None:
        raise RuntimeError("Dependencies not initialized. Call init_dependencies() first.")
    return _deps

def init_dependencies(discord_token: str) -> BotDependencies:
    """Initialize global dependencies"""
    global _deps
    _deps = BotDependencies.create_defaults(discord_token)
    return _deps

def set_dependencies(deps: BotDependencies) -> None:
    """Set global dependencies (for testing)"""
    global _deps
    _deps = deps
