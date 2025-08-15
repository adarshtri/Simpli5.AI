import asyncio
from typing import Dict, List, Optional, Tuple
from .https_client import MCPClientProvider
from .stdio_client import MCPStdioManager, MCPStdioClientProvider
from ...config import ConfigManager

class MultiServerProvider:
    """Manages connections to multiple MCP servers with both HTTP and STDIO transports."""
    
    def __init__(self, server_ids: List[str]):
        self.server_ids = server_ids
        self.config = ConfigManager()
        self.http_providers: Dict[str, MCPClientProvider] = {}
        self.stdio_manager = MCPStdioManager()
        self.tools: Dict[str, Tuple[str, any]] = {}  # tool_name -> (server_id, tool_info)
        self.resources: Dict[str, Tuple[str, any]] = {}  # resource_uri -> (server_id, resource_info)
        self.prompts: Dict[str, Tuple[str, any]] = {}  # prompt_name -> (server_id, prompt_info)
    
    async def connect(self):
        """Connect to all configured servers (both HTTP and STDIO) and load their capabilities."""
        stdio_tasks = []
        
        for server_id in self.server_ids:
            server_config = self.config.get_server_config(server_id)
            if not server_config:
                print(f"Warning: No configuration found for server '{server_id}'")
                continue
                
            if not server_config.enabled:
                print(f"Skipping disabled server '{server_id}'")
                continue
            
            transport_type = getattr(server_config, 'transport', 'http')
            
            try:
                if transport_type == 'stdio':
                    # STDIO transport - no ports needed!
                    command = getattr(server_config, 'command', 'python')
                    args = getattr(server_config, 'args', [])
                    env = getattr(server_config, 'env', None)
                    working_dir = getattr(server_config, 'working_dir', None)
                    
                    stdio_tasks.append(self.stdio_manager.add_server(
                        server_id, command, args, env, working_dir
                    ))
                    
                    print(f"Configured STDIO server '{server_id}': {command} {' '.join(args)}")
                    
                elif transport_type == 'http':
                    # HTTP transport - existing logic
                    server_url = self.config.get_server_url(server_id)
                    if not server_url:
                        print(f"Warning: No URL found for HTTP server '{server_id}'")
                        continue
                    
                    provider = MCPClientProvider(server_url)
                    self.http_providers[server_id] = provider
                    print(f"Connected to HTTP server '{server_id}' at {server_url}")
                    
                else:
                    print(f"Unknown transport type '{transport_type}' for server '{server_id}'")
                    
            except Exception as e:
                print(f"Error configuring server '{server_id}': {e}")
        
        # Connect all STDIO servers in parallel
        if stdio_tasks:
            await asyncio.gather(*stdio_tasks)
            await self.stdio_manager.connect_all()
        
        # Load capabilities from all connected servers
        await self._load_capabilities()
    
    async def _load_capabilities(self):
        """Load capabilities (tools, resources, prompts) from all servers."""
        total_servers = len(self.http_providers) + len(self.stdio_manager.clients)
        print(f"Loading capabilities from {total_servers} servers...")
        
        # Load from HTTP servers
        for server_id, provider in self.http_providers.items():
            await self._load_server_capabilities(server_id, provider, "HTTP")
        
        # Load from STDIO servers
        for server_id, client in self.stdio_manager.clients.items():
            await self._load_server_capabilities(server_id, client, "STDIO")
    
    async def _load_server_capabilities(self, server_id: str, provider, transport_type: str):
        """Load capabilities from a single server."""
        try:
            print(f"Loading capabilities from {transport_type} server '{server_id}'...")
            
            # Load tools
            tools = await provider.list_tools()
            for tool in tools:
                tool_name = f"{server_id}:{tool.name}"
                self.tools[tool_name] = (server_id, tool)
                print(f"  Tool: {tool_name} (from {server_id} via {transport_type})")
            
            # Load resources
            try:
                resources = await provider.list_resources()
                for resource in resources:
                    resource_uri = str(resource.uri)
                    self.resources[resource_uri] = (server_id, resource)
                    print(f"  Resource: {resource_uri} (from {server_id} via {transport_type})")
            except Exception:
                # Some servers might not support resources
                pass
            
            # Load prompts
            try:
                prompts = await provider.list_prompts()
                for prompt in prompts:
                    prompt_name = f"{server_id}:{prompt.name}"
                    self.prompts[prompt_name] = (server_id, prompt)
                    print(f"  Prompt: {prompt_name} (from {server_id} via {transport_type})")
            except Exception:
                # Some servers might not support prompts
                pass
                
        except Exception as e:
            print(f"Error loading capabilities from {transport_type} server '{server_id}': {e}")
    
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
        """Call a tool on the appropriate server (HTTP or STDIO)."""
        tool_names = [tool.split(':', 1)[1] for tool in self.tools.keys()]
        if tool_name in self.tools.keys():
            server_id, _ = self.tools[tool_name]
            
            # Check HTTP providers first
            if server_id in self.http_providers:
                provider = self.http_providers[server_id]
                return await provider.call_tool(tool_name.split(':', 1)[1], arguments)
            
            # Check STDIO providers
            elif server_id in self.stdio_manager.clients:
                client = self.stdio_manager.clients[server_id]
                return await client.call_tool(tool_name.split(':', 1)[1], arguments)
            
            else:
                raise ValueError(f"Server '{server_id}' not found for tool '{tool_name}'")
        else:
            raise ValueError(f"Tool '{tool_name}' not found")
    
    async def read_resource(self, uri: str):
        """Read a resource from the appropriate server (HTTP or STDIO)."""
        if uri in self.resources:
            server_id, _ = self.resources[uri]
            
            # Check HTTP providers first
            if server_id in self.http_providers:
                provider = self.http_providers[server_id]
                return await provider.read_resource(uri)
            
            # Check STDIO providers
            elif server_id in self.stdio_manager.clients:
                client = self.stdio_manager.clients[server_id]
                return await client.read_resource(uri)
            
            else:
                raise ValueError(f"Server '{server_id}' not found for resource '{uri}'")
        else:
            raise ValueError(f"Resource '{uri}' not found")
    
    async def generate_prompt(self, prompt_name: str, arguments: dict):
        """Generate a prompt from the appropriate server (HTTP or STDIO)."""
        if prompt_name in self.prompts:
            server_id, _ = self.prompts[prompt_name]
            
            # For prompts, we'll need to implement this in the providers
            # This is a placeholder for now
            raise NotImplementedError("Prompt generation not yet implemented for multi-transport")
        else:
            raise ValueError(f"Prompt '{prompt_name}' not found")
    
    async def disconnect_all(self):
        """Disconnect from all servers (both HTTP and STDIO)."""
        # Disconnect STDIO servers
        await self.stdio_manager.disconnect_all()
        
        # HTTP providers don't need explicit disconnection in current implementation
        print("Disconnected from all MCP servers") 