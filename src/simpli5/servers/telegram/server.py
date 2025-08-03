import asyncio
import logging
from typing import List
from .tools import TelegramMemoryCategorizerTool
from .prompts import MemoryCategorizationPrompt
from ...servers.fastmcp_server import FastMCPServer

logger = logging.getLogger(__name__)

class TelegramMCPServer(FastMCPServer):
    """MCP Server for Telegram bot functionality."""
    
    def __init__(self, host: str = "localhost", port: int = 8002, log_level: str = "WARNING"):
        super().__init__(name="Simpli5 Telegram Server", host=host, port=port, log_level=log_level)
        self.server_name = "Simpli5 Telegram Server"
        self.server_version = "1.0.0"
        self.host = host
        self.port = port
        self._server_task = None
        self._running = False
        
        # Register Telegram-specific tools
        self.add_tool(TelegramMemoryCategorizerTool())
        
        # Register Telegram-specific prompts
        self.add_prompt(MemoryCategorizationPrompt())

    async def start(self):
        """Start the Telegram MCP server."""
        if self._running:
            print("Server is already running.")
            return
            
        print(f"Starting Telegram MCP server on {self.host}:{self.port}")
        print(f"Server name: {self.server_name}")
        print(f"Server version: {self.server_version}")
        print("Available capabilities:")
        print(f"  - Tools: {len(self.tools)}")
        print(f"  - Resources: {len(self.resources)}")
        print(f"  - Prompts: {len(self.prompts)}")
        
        self._running = True
        
        # Start FastMCP HTTP server using async method
        try:
            self._server_task = asyncio.create_task(
                self.mcp.run_streamable_http_async()
            )
            print(f"Telegram MCP server started successfully on {self.host}:{self.port}")
        except Exception as e:
            self._running = False
            print(f"Failed to start Telegram MCP server: {e}")
            raise

    async def stop(self):
        """Stop the Telegram MCP server."""
        if not self._running:
            return
            
        print("Shutting down Telegram MCP server...")
        self._running = False
        
        if self._server_task and not self._server_task.done():
            self._server_task.cancel()
            try:
                await self._server_task
            except:
                pass  # Ignore any cancellation errors
        
        self._server_task = None
        print("Telegram MCP server stopped.")

    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running

if __name__ == "__main__":
    asyncio.run(TelegramMCPServer().start()) 