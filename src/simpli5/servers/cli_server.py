import asyncio
import os
from typing import List
from .fastmcp_server import FastMCPServer
from ..host import (
    ListServersTool, RunCommandTool, GetConfigTool, PingServerTool,
    ConfigResource, ServersResource, SystemInfoResource, HelpResource,
    HelpPrompt, GreetingPrompt, CommandSuggestionPrompt
)

class CLIMCPServer(FastMCPServer):
    """MCP server that exposes CLI functionality as tools, resources, and prompts."""
    
    def __init__(self, host: str = "localhost", port: int = 8001, log_level: str = "WARNING"):
        super().__init__(name="Simpli5 CLI Server", host=host, port=port, log_level=log_level)
        self.server_name = "Simpli5 CLI Server"
        self.server_version = "1.0.0"
        self.host = host
        self.port = port
        self._server_task = None
        self._running = False
        
        # Register host tools
        self.add_tool(ListServersTool())
        self.add_tool(RunCommandTool())
        self.add_tool(GetConfigTool())
        self.add_tool(PingServerTool())
        
        # Register host resources
        self.add_resource(ConfigResource())
        self.add_resource(ServersResource())
        self.add_resource(SystemInfoResource())
        self.add_resource(HelpResource())
        
        # Register host prompts
        self.add_prompt(HelpPrompt())
        self.add_prompt(GreetingPrompt())
        self.add_prompt(CommandSuggestionPrompt())

    async def start(self):
        """Start the CLI MCP server."""
        if self._running:
            print("Server is already running.")
            return
            
        print(f"Starting CLI MCP server on {self.host}:{self.port}")
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
            print(f"CLI MCP server started successfully on {self.host}:{self.port}")
        except Exception as e:
            self._running = False
            print(f"Failed to start CLI MCP server: {e}")
            raise

    async def stop(self):
        """Stop the CLI MCP server."""
        if not self._running:
            return
            
        print("Shutting down CLI MCP server...")
        self._running = False
        
        if self._server_task and not self._server_task.done():
            self._server_task.cancel()
            try:
                await self._server_task
            except:
                pass  # Ignore any cancellation errors
        
        self._server_task = None
        print("CLI MCP server stopped.")

    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running

if __name__ == "__main__":
    asyncio.run(CLIMCPServer().start()) 