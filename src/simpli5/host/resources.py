import json
import os
from typing import Dict, Any, List
from ..servers.base import BaseResource, ResourceResult
from ..config import ConfigManager

class ConfigResource(BaseResource):
    """Resource that provides CLI configuration information."""
    
    @property
    def uri(self) -> str:
        return "config://config"
    
    @property
    def name(self) -> str:
        return "config"
    
    @property
    def description(self) -> str:
        return "CLI configuration and system information"
    
    @property
    def mime_type(self) -> str:
        return "application/json"
    
    async def read(self, uri: str = None) -> ResourceResult:
        config = ConfigManager()
        
        result = {
            "config_path": config.config_path,
            "config_exists": os.path.exists(config.config_path),
            "current_working_directory": os.getcwd(),
            "platform": os.name,
            "servers": {}
        }
        
        # Add server information
        servers = config.list_servers()
        for server_id, server_config in servers:
            result["servers"][server_id] = {
                "name": server_config.name,
                "url": server_config.url,
                "description": server_config.description,
                "enabled": server_config.enabled
            }
        
        return ResourceResult(json.dumps(result, indent=2))

class ServersResource(BaseResource):
    """Resource that provides detailed server information."""
    
    @property
    def uri(self) -> str:
        return "config://servers"
    
    @property
    def name(self) -> str:
        return "servers"
    
    @property
    def description(self) -> str:
        return "Detailed information about configured MCP servers"
    
    @property
    def mime_type(self) -> str:
        return "application/json"
    
    async def read(self, uri: str = None) -> ResourceResult:
        config = ConfigManager()
        servers = config.list_servers()
        
        if not servers:
            return ResourceResult("No servers configured.")
        
        result = []
        for server_id, server_config in servers:
            server_info = {
                "id": server_id,
                "name": server_config.name,
                "url": server_config.url,
                "description": server_config.description,
                "enabled": server_config.enabled
            }
            
            # Try to get additional info if server is enabled
            if server_config.enabled:
                try:
                    from ..providers.mcp.client import MCPClientProvider
                    provider = MCPClientProvider(server_config.url)
                    tools = await provider.list_tools()
                    resources = await provider.list_resources()
                    prompts = await provider.list_prompts()
                    
                    server_info["capabilities"] = {
                        "tools_count": len(tools),
                        "resources_count": len(resources),
                        "prompts_count": len(prompts)
                    }
                except Exception as e:
                    server_info["capabilities"] = {
                        "error": str(e)
                    }
            
            result.append(server_info)
        
        return ResourceResult(json.dumps(result, indent=2))

class SystemInfoResource(BaseResource):
    """Resource that provides system information."""
    
    @property
    def uri(self) -> str:
        return "system://info"
    
    @property
    def name(self) -> str:
        return "system_info"
    
    @property
    def description(self) -> str:
        return "System information and environment details"
    
    @property
    def mime_type(self) -> str:
        return "application/json"
    
    async def read(self, uri: str = None) -> ResourceResult:
        import platform
        import sys
        
        result = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "python": {
                "version": sys.version,
                "executable": sys.executable,
                "path": sys.path
            },
            "environment": {
                "cwd": os.getcwd(),
                "user": os.getenv("USER", "unknown"),
                "home": os.getenv("HOME", "unknown"),
                "path": os.getenv("PATH", "").split(":")
            }
        }
        
        return ResourceResult(json.dumps(result, indent=2))

class HelpResource(BaseResource):
    """Resource that provides CLI help information."""
    
    @property
    def uri(self) -> str:
        return "help://help"
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def description(self) -> str:
        return "CLI help and usage information"
    
    @property
    def mime_type(self) -> str:
        return "text/markdown"
    
    async def read(self, uri: str = None) -> ResourceResult:
        help_text = """# Simpli5.AI CLI Help

## Available Commands

### Chat Interface
- `/help` - Show this help message
- `/tools` - List all available tools
- `/resources` - List all available resources  
- `/prompts` - List all available prompts
- `/call <tool_name> <args>` - Call a specific tool
- `/read <resource_uri>` - Read a specific resource
- `/generate <prompt_name> <args>` - Generate using a prompt
- `/exit` - Exit the chat interface

### Server Management
- `/list-servers` - List configured MCP servers
- `/add-server <id> <name> <url> <description>` - Add a new server
- `/remove-server <id>` - Remove a server
- `/enable-server <id>` - Enable a server
- `/disable-server <id>` - Disable a server

### Examples
```
/call calculator_add {\"a\": 5, \"b\": 3}
/read file:///path/to/file.txt
/generate greeting {\"name\": \"Alice\"}
```

## MCP Server Integration

The CLI can connect to multiple MCP servers simultaneously. Each server's tools, resources, and prompts are available with server-prefixed names.

For example, if you have a server called "math" with a tool called "add", you can call it as:
```
/call math:add {\"a\": 5, \"b\": 3}
```

## Configuration

Server configurations are stored in `~/.simpli5/config.yml`. You can edit this file directly or use the CLI commands to manage servers.
"""
        
        return ResourceResult(help_text) 