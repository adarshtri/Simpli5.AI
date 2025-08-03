import asyncio
import os
from typing import List
from ..common import SystemInfoResource
from .tools import GreetingTool, CalculatorTool, EchoTool
from .resources import FileResource
from .prompts import GreetingPrompt
from ...servers.fastmcp_server import FastMCPServer

class ExamplesMCPServer(FastMCPServer):
    """MCP server that provides example tools, resources, and prompts."""
    
    def __init__(self, host: str = "localhost", port: int = 8000, log_level: str = "WARNING"):
        super().__init__(name="Simpli5 Examples Server", host=host, port=port, log_level=log_level)
        self.server_name = "Simpli5 Examples Server"
        self.server_version = "1.0.0"
        self.host = host
        self.port = port
        self._server_task = None
        self._running = False
        
        # Register example tools
        self.add_tool(GreetingTool())
        self.add_tool(CalculatorTool())
        self.add_tool(EchoTool())
        
        # Register example resources
        self.add_resource(SystemInfoResource())
        self.add_resource(FileResource("examples/simple_server.py"))
        
        # Register example prompts
        self.add_prompt(GreetingPrompt())

    async def start(self):
        """Start the Examples MCP server."""
        if self._running:
            print("Server is already running.")
            return
            
        print(f"Starting Examples MCP server on {self.host}:{self.port}")
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
            print(f"Examples MCP server started successfully on {self.host}:{self.port}")
        except Exception as e:
            self._running = False
            print(f"Failed to start Examples MCP server: {e}")
            raise

    async def stop(self):
        """Stop the Examples MCP server."""
        if not self._running:
            return
            
        print("Shutting down Examples MCP server...")
        self._running = False
        
        if self._server_task and not self._server_task.done():
            self._server_task.cancel()
            try:
                await self._server_task
            except:
                pass  # Ignore any cancellation errors
        
        self._server_task = None
        print("Examples MCP server stopped.")

    @property
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running

if __name__ == "__main__":
    asyncio.run(ExamplesMCPServer().start()) 