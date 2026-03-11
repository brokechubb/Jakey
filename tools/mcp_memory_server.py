"""
Simple MCP Memory Server for Jakey
Provides HTTP API endpoints for memory storage and retrieval
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from aiohttp import web, ClientSession
import logging
import uuid
import socket
import random
import os
import secrets
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_available_port(start_port=8501, max_port=9000):
    """Find an available port in the given range"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    # If no port found in range, use a random high port
    return random.randint(10000, 65535)


class MCPMemoryServer:
    """Simple HTTP server for MCP memory operations with authentication"""

    def __init__(self, port=None):
        self.app = web.Application()
        self.port = port or get_available_port()
        self.auth_token = self._generate_auth_token()
        self.token_file = os.path.join(os.path.dirname(__file__), "..", ".mcp_token")
        self._db = None
        self.setup_routes()
        self.setup_middleware()

    def _get_db(self):
        """Lazily import and return the database manager"""
        if self._db is None:
            from data.database import db
            self._db = db
        return self._db

    def _generate_auth_token(self) -> str:
        """Generate a cryptographically secure authentication token"""
        return secrets.token_urlsafe(32)

    def setup_middleware(self):
        """Setup authentication middleware"""
        self.app.middlewares.append(self.auth_middleware)

    @web.middleware
    async def auth_middleware(self, request, handler):
        """Authentication middleware to validate Bearer tokens"""
        # Allow health check without authentication
        if request.path == "/health":
            return await handler(request)
        
        # Extract authorization header
        auth_header = request.headers.get("Authorization", "")
        
        # Validate Bearer token format
        if not auth_header.startswith("Bearer "):
            logger.warning(f"Missing or invalid Authorization header from {request.remote}")
            return web.json_response(
                {"error": "Missing or invalid Authorization header. Expected 'Bearer <token>'"}, 
                status=401
            )
        
        # Extract token
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Validate token
        if not self._validate_token(token):
            logger.warning(f"Invalid authentication token from {request.remote}")
            return web.json_response(
                {"error": "Invalid authentication token"}, 
                status=401
            )
        
        # Token is valid, proceed with request
        return await handler(request)

    def _validate_token(self, token: str) -> bool:
        """Validate authentication token"""
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(token, self.auth_token)

    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get("/health", self.health_check)
        self.app.router.add_post("/memories", self.store_memory)
        self.app.router.add_get("/memories", self.get_memories)
        self.app.router.add_get("/memories/search", self.search_memories)
        self.app.router.add_delete("/memories", self.delete_memories)

    async def health_check(self, request):
        """Health check endpoint (no authentication required)"""
        return web.json_response(
            {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "authentication_enabled": True,
                "auth_required": True
            }
        )

    async def store_memory(self, request):
        """Store a new memory"""
        try:
            data = await request.json()

            # Validate required fields
            required_fields = ["user_id", "information_type", "information"]
            for field in required_fields:
                if field not in data:
                    return web.json_response(
                        {"error": f"Missing required field: {field}"}, status=400
                    )

            user_id = data["user_id"]
            information_type = data["information_type"]
            information = data["information"]
            memory_id = str(uuid.uuid4())

            db = self._get_db()
            db.add_memory(user_id, information_type, information)

            logger.info(f"Stored memory for user {user_id}: {information_type}")

            return web.json_response(
                {
                    "status": "success",
                    "memory_id": memory_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def get_memories(self, request):
        """Get memories for a user"""
        try:
            user_id = request.query.get("user_id")
            if not user_id:
                return web.json_response(
                    {"error": "user_id parameter required"}, status=400
                )

            limit = int(request.query.get("limit", 10))

            db = self._get_db()
            raw = db.get_memories(user_id)

            memories = [
                {
                    "id": f"{user_id}:{k}",
                    "user_id": user_id,
                    "information_type": k,
                    "information": v,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                for k, v in list(raw.items())[:limit]
            ]

            return web.json_response(
                {"memories": memories, "total": len(memories)}
            )

        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def search_memories(self, request):
        """Search memories for a user"""
        try:
            user_id = request.query.get("user_id")
            if not user_id:
                return web.json_response(
                    {"error": "user_id parameter required"}, status=400
                )

            query = request.query.get("query", "").lower()

            db = self._get_db()
            raw = db.get_memories(user_id)

            memories = []
            for k, v in raw.items():
                if not query or query in k.lower() or query in v.lower():
                    memories.append(
                        {
                            "id": f"{user_id}:{k}",
                            "user_id": user_id,
                            "information_type": k,
                            "information": v,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

            return web.json_response(
                {
                    "memories": memories,
                    "total": len(memories),
                    "query": query,
                }
            )

        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def delete_memories(self, request):
        """Delete memories for a user"""
        try:
            user_id = request.query.get("user_id")
            if not user_id:
                return web.json_response(
                    {"error": "user_id parameter required"}, status=400
                )

            memory_type = request.query.get("type")
            db = self._get_db()

            if memory_type:
                deleted = db.delete_memory(user_id, memory_type)
                deleted_count = 1 if deleted else 0
            else:
                deleted_count = db.delete_memories(user_id)

            logger.info(f"Deleted {deleted_count} memories for user {user_id}")

            return web.json_response(
                {"status": "success", "deleted_count": deleted_count}
            )

        except Exception as e:
            logger.error(f"Error deleting memories: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def run(self, host="localhost", port=None):
        """Run the server"""
        port = port or self.port
        logger.info(f"Starting MCP Memory Server on {host}:{port}")

        # Save port to file for client to read
        port_file = os.path.join(os.path.dirname(__file__), "..", ".mcp_port")
        with open(port_file, "w") as f:
            f.write(str(port))
        logger.info(f"Port {port} saved to {port_file}")

        # Save authentication token to file for client to read
        try:
            with open(self.token_file, "w") as f:
                f.write(self.auth_token)
            # Set restrictive file permissions (owner read/write only)
            os.chmod(self.token_file, 0o600)
            logger.info(f"Authentication token saved to {self.token_file}")
            logger.info(f"Authentication token: {self.auth_token[:16]}... (keep this secret!)")
        except Exception as e:
            logger.error(f"Failed to save authentication token: {e}")
            raise

        # Set environment variable for immediate client access
        os.environ["MCP_MEMORY_TOKEN"] = self.auth_token

        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info("MCP Memory Server started (auth enabled)")

        try:
            # Keep server running
            await asyncio.Future()
        except asyncio.CancelledError:
            logger.info("Shutting down MCP Memory Server")
            await runner.cleanup()
            # Clean up files
            for file_path in [port_file, self.token_file]:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Cleaned up {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {file_path}: {e}")
            # Clean up environment variable
            if "MCP_MEMORY_TOKEN" in os.environ:
                del os.environ["MCP_MEMORY_TOKEN"]


async def main():
    """Main function to run the server"""
    import sys

    # Allow port to be passed as command line argument
    port = None
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.warning(f"Invalid port argument: {sys.argv[1]}, using random port")

    server = MCPMemoryServer(port=port)
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down MCP Memory Server...")
