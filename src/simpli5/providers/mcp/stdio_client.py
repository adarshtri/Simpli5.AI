"""
STDIO Transport Client for MCP - Communicates with MCP servers via subprocess pipes.

This module provides STDIO-based transport for MCP communication, allowing
the client to spawn MCP server processes and communicate through stdin/stdout
pipes instead of HTTP. This eliminates the need for port management and 
provides better process isolation.
"""

import asyncio
import json
import logging
import subprocess
import sys
from typing import Dict, Any, Optional, List, AsyncGenerator

# Try to import MCP SDK components
try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
    MCP_SDK_AVAILABLE = True
except ImportError:
    MCP_SDK_AVAILABLE = False

logger = logging.getLogger(__name__)

class MCPStdioClientProvider:
    """MCP Client that communicates with servers via STDIO transport."""
    
    def __init__(self, server_command: str, server_args: List[str] = None, 
                 server_env: Dict[str, str] = None, working_dir: str = None):
        """
        Initialize STDIO MCP client.
        
        Args:
            server_command: Command to start the MCP server (e.g., "python", "node")
            server_args: Arguments for the server command (e.g., ["server.py"])
            server_env: Environment variables for the server process
            working_dir: Working directory for the server process
        """
        self.server_command = server_command
        self.server_args = server_args or []
        self.server_env = server_env
        self.working_dir = working_dir
        self.session: Optional[ClientSession] = None
        self._process: Optional[subprocess.Popen] = None
        
    async def __aenter__(self):
        """Async context manager entry - start the server and connect."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup connection."""
        await self.disconnect()
        
    async def connect(self):
        """Start the MCP server process and establish STDIO connection."""
        if not MCP_SDK_AVAILABLE:
            raise RuntimeError("MCP SDK not available. Please install: pip install mcp")
            
        try:
            # Prepare server parameters
            server_params = StdioServerParameters(
                command=self.server_command,
                args=self.server_args,
                env=self.server_env
            )
            
            logger.info(f"Starting MCP server: {self.server_command} {' '.join(self.server_args)}")
            
            # Connect using MCP's stdio_client
            self._stdio_context = stdio_client(server_params)
            self._read_stream, self._write_stream = await self._stdio_context.__aenter__()
            
            # Create client session
            self._session_context = ClientSession(self._read_stream, self._write_stream)
            self.session = await self._session_context.__aenter__()
            
            # Initialize the session
            await self.session.initialize()
            
            logger.info("MCP STDIO connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server via STDIO: {e}")
            await self.disconnect()
            raise
            
    async def disconnect(self):
        """Close the STDIO connection and terminate the server process."""
        try:
            # Clean up session context if it exists
            if hasattr(self, '_session_context') and self._session_context:
                try:
                    await self._session_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning(f"Error closing session context: {e}")
                finally:
                    self._session_context = None
                    self.session = None
                
            # Clean up stdio context if it exists
            if hasattr(self, '_stdio_context') and self._stdio_context:
                try:
                    await self._stdio_context.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning(f"Error closing stdio context: {e}")
                finally:
                    self._stdio_context = None
                
            logger.info("MCP STDIO connection closed")
            
        except Exception as e:
            logger.error(f"Error disconnecting from MCP server: {e}")
        finally:
            # Ensure cleanup happens even if there are errors
            self.session = None
            if hasattr(self, '_stdio_context'):
                self._stdio_context = None
            
    async def list_tools(self):
        """List all available tools from the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        try:
            tools_response = await self.session.list_tools()
            return tools_response.tools
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise
            
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a tool on the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        try:
            logger.info(f"Calling tool '{tool_name}' with arguments: {arguments}")
            result = await self.session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Failed to call tool '{tool_name}': {e}")
            raise
            
    async def list_resources(self):
        """List all available resources from the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        try:
            resources_response = await self.session.list_resources()
            return resources_response.resources
        except Exception as e:
            logger.error(f"Failed to list resources: {e}")
            raise
            
    async def read_resource(self, uri: str):
        """Read a resource from the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        try:
            result = await self.session.read_resource(uri)
            return result.contents
        except Exception as e:
            logger.error(f"Failed to read resource '{uri}': {e}")
            raise
            
    async def list_prompts(self):
        """List all available prompts from the MCP server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
            
        try:
            prompts_response = await self.session.list_prompts()
            return prompts_response.prompts
        except Exception as e:
            logger.error(f"Failed to list prompts: {e}")
            raise

class MCPStdioManager:
    """Manages multiple STDIO MCP server connections."""
    
    def __init__(self):
        self.clients: Dict[str, MCPStdioClientProvider] = {}
        self._initialized = False
        
    async def add_server(self, server_id: str, command: str, args: List[str] = None, 
                        env: Dict[str, str] = None, working_dir: str = None):
        """Add a new MCP server configuration."""
        if server_id in self.clients:
            logger.warning(f"Server '{server_id}' already exists, replacing...")
            await self.remove_server(server_id)
            
        client = MCPStdioClientProvider(
            server_command=command,
            server_args=args,
            server_env=env,
            working_dir=working_dir
        )
        
        self.clients[server_id] = client
        
        # If manager is already initialized, connect this client immediately
        if self._initialized:
            await client.connect()
            
        logger.info(f"Added MCP server '{server_id}': {command} {' '.join(args or [])}")
        
    async def remove_server(self, server_id: str):
        """Remove and disconnect an MCP server."""
        if server_id in self.clients:
            client = self.clients[server_id]
            await client.disconnect()
            del self.clients[server_id]
            logger.info(f"Removed MCP server '{server_id}'")
            
    async def connect_all(self):
        """Connect to all configured MCP servers."""
        connection_tasks = []
        for server_id, client in self.clients.items():
            task = asyncio.create_task(
                self._connect_server_with_retry(server_id, client)
            )
            connection_tasks.append(task)
            
        if connection_tasks:
            await asyncio.gather(*connection_tasks, return_exceptions=True)
            
        self._initialized = True
        logger.info(f"Connected to {len(self.clients)} MCP servers via STDIO")
        
    async def _connect_server_with_retry(self, server_id: str, client: MCPStdioClientProvider, 
                                       max_retries: int = 3):
        """Connect to a server with retry logic."""
        for attempt in range(max_retries):
            try:
                await client.connect()
                logger.info(f"Connected to MCP server '{server_id}'")
                return
            except Exception as e:
                logger.error(f"Failed to connect to '{server_id}' (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Giving up on server '{server_id}' after {max_retries} attempts")
                    
    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        if not self.clients:
            self._initialized = False
            return
            
        # Disconnect clients sequentially to avoid task context issues
        for server_id, client in list(self.clients.items()):
            try:
                await client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting from server '{server_id}': {e}")
            finally:
                # Remove client even if disconnect failed
                if server_id in self.clients:
                    del self.clients[server_id]
            
        self._initialized = False
        logger.info("Disconnected from all MCP servers")
        
    def get_client(self, server_id: str) -> Optional[MCPStdioClientProvider]:
        """Get a specific MCP client by server ID."""
        return self.clients.get(server_id)
        
    async def call_tool_on_server(self, server_id: str, tool_name: str, 
                                 arguments: Dict[str, Any]):
        """Call a tool on a specific server."""
        client = self.get_client(server_id)
        if not client:
            raise ValueError(f"Server '{server_id}' not found")
            
        return await client.call_tool(tool_name, arguments)
        
    async def list_all_tools(self) -> Dict[str, List[Any]]:
        """List tools from all connected servers."""
        all_tools = {}
        
        for server_id, client in self.clients.items():
            try:
                tools = await client.list_tools()
                all_tools[server_id] = tools
            except Exception as e:
                logger.error(f"Failed to list tools from '{server_id}': {e}")
                all_tools[server_id] = []
                
        return all_tools 