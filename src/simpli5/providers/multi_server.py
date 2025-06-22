import asyncio
from typing import Dict, List, Optional, Tuple
from .mcp_client import MCPClientProvider
from ..config import ConfigManager

class MultiServerProvider:
    """Manages connections to multiple MCP servers simultaneously."""
    
    def __init__(self, server_ids: List[str]):
        self.server_ids = server_ids
        self.config = ConfigManager()
        self.providers: Dict[str, MCPClientProvider] = {}
        self.tools: Dict[str, Tuple[str, any]] = {}  # tool_name -> (server_id, tool_info)
        self.resources: Dict[str, Tuple[str, any]] = {}  # resource_uri -> (server_id, resource_info)
        self.prompts: Dict[str, Tuple[str, any]] = {}  # prompt_name -> (server_id, prompt_info)
    
    async def connect(self):
        """Connect to all configured servers and load their capabilities."""
        for server_id in self.server_ids:
            if server_id == "cli":
                # Special handling for CLI server
                server_url = "http://localhost:8001"
                print(f"Connecting to CLI server: {server_url}")
            else:
                server_url = self.config.get_server_url(server_id)
                if not server_url:
                    print(f"Warning: No URL found for server '{server_id}'")
                    continue
            
            try:
                provider = MCPClientProvider(server_url)
                self.providers[server_id] = provider
                print(f"Connected to {server_id}: {server_url}")
            except Exception as e:
                print(f"Error connecting to {server_id}: {e}")
        
        # Load capabilities from all connected servers
        await self._load_capabilities()
    
    async def _load_capabilities(self):
        """Load tools, resources, and prompts from all connected servers."""
        for server_id, provider in self.providers.items():
            try:
                # Load tools
                tools = await provider.list_tools()
                for tool in tools:
                    tool_name = f"{server_id}:{tool.name}"
                    self.tools[tool_name] = (server_id, tool)
                
                # Load resources
                resources = await provider.list_resources()
                for resource in resources:
                    # Convert AnyUrl to string for consistent lookup
                    resource_uri = str(resource.uri)
                    self.resources[resource_uri] = (server_id, resource)
                
                # Load prompts
                prompts = await provider.list_prompts()
                for prompt in prompts:
                    prompt_name = f"{server_id}:{prompt.name}"
                    self.prompts[prompt_name] = (server_id, prompt)
                    
            except Exception as e:
                print(f"Error loading capabilities from {server_id}: {e}")
    
    def list_all_tools(self) -> List[Tuple[str, str, any]]:
        """List all tools from all servers with server prefixes."""
        return [(tool_name, server_id, tool_info) 
                for tool_name, (server_id, tool_info) in self.tools.items()]
    
    def list_all_resources(self) -> List[Tuple[str, str, any]]:
        """List all resources from all servers."""
        return [(str(uri), server_id, resource_info) 
                for uri, (server_id, resource_info) in self.resources.items()]
    
    def list_all_prompts(self) -> List[Tuple[str, str, any]]:
        """List all prompts from all servers with server prefixes."""
        return [(prompt_name, server_id, prompt_info) 
                for prompt_name, (server_id, prompt_info) in self.prompts.items()]
    
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool on the appropriate server."""
        if tool_name in self.tools:
            server_id, _ = self.tools[tool_name]
            provider = self.providers[server_id]
            return await provider.call_tool(tool_name.split(':', 1)[1], arguments)
        else:
            raise ValueError(f"Tool '{tool_name}' not found")
    
    async def read_resource(self, uri: str):
        """Read a resource from the appropriate server."""
        if uri in self.resources:
            server_id, _ = self.resources[uri]
            provider = self.providers[server_id]
            return await provider.read_resource(uri)
        else:
            raise ValueError(f"Resource '{uri}' not found")
    
    async def generate_prompt(self, prompt_name: str, arguments: dict):
        """Generate a prompt from the appropriate server."""
        if prompt_name in self.prompts:
            server_id, _ = self.prompts[prompt_name]
            provider = self.providers[server_id]
            return await provider.generate_prompt(prompt_name.split(':', 1)[1], arguments)
        else:
            raise ValueError(f"Prompt '{prompt_name}' not found") 