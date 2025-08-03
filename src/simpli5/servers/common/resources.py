import json
import os
import platform
from typing import Dict, Any
from .base import BaseResource, ResourceResult
from ...config import ConfigManager

# Optional import for psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class ConfigResource(BaseResource):
    """Resource that provides configuration information."""
    
    @property
    def uri(self) -> str:
        return "config://config"
    
    @property
    def name(self) -> str:
        return "config"
    
    @property
    def description(self) -> str:
        return "CLI configuration information"
    
    async def read(self) -> ResourceResult:
        try:
            config = ConfigManager()
            # Get server configurations
            servers = {}
            for server_id, server_config in config.list_servers():
                servers[server_id] = {
                    "name": server_config.name,
                    "url": server_config.url,
                    "description": server_config.description,
                    "enabled": server_config.enabled
                }
            
            config_data = {
                "servers": servers,
                "note": "LLM providers and webhook config are configured via environment variables and CLI arguments"
            }
            return ResourceResult(json.dumps(config_data, indent=2), "application/json")
        except Exception as e:
            return ResourceResult(f"Error reading configuration: {str(e)}", "text/plain")

class ServersResource(BaseResource):
    """Resource that provides server information."""
    
    @property
    def uri(self) -> str:
        return "config://servers"
    
    @property
    def name(self) -> str:
        return "servers"
    
    @property
    def description(self) -> str:
        return "Configured MCP servers information"
    
    async def read(self) -> ResourceResult:
        try:
            config = ConfigManager()
            servers = config.list_servers()
            
            if not servers:
                return ResourceResult("No servers configured.", "text/plain")
            
            result = []
            for server_id, server_config in servers:
                result.append({
                    "id": server_id,
                    "name": server_config.name,
                    "url": server_config.url,
                    "description": server_config.description,
                    "enabled": server_config.enabled
                })
            
            return ResourceResult(json.dumps(result, indent=2), "application/json")
        except Exception as e:
            return ResourceResult(f"Error reading servers: {str(e)}", "text/plain")

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
        return "System information and statistics"
    
    async def read(self) -> ResourceResult:
        try:
            # Get system information
            system_info = {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor()
                },
                "python": {
                    "version": platform.python_version(),
                    "implementation": platform.python_implementation(),
                    "compiler": platform.python_compiler()
                }
            }
            
            # Add psutil-based info if available
            if PSUTIL_AVAILABLE:
                system_info.update({
                    "memory": {
                        "total": psutil.virtual_memory().total,
                        "available": psutil.virtual_memory().available,
                        "percent": psutil.virtual_memory().percent
                    },
                    "disk": {
                        "total": psutil.disk_usage('/').total,
                        "free": psutil.disk_usage('/').free,
                        "percent": psutil.disk_usage('/').percent
                    },
                    "cpu": {
                        "count": psutil.cpu_count(),
                        "percent": psutil.cpu_percent(interval=1)
                    }
                })
            else:
                system_info["note"] = "psutil not available - limited system info"
            
            return ResourceResult(json.dumps(system_info, indent=2), "application/json")
        except Exception as e:
            return ResourceResult(f"Error reading system info: {str(e)}", "text/plain")

class HelpResource(BaseResource):
    """Resource that provides help documentation."""
    
    @property
    def uri(self) -> str:
        return "help://help"
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def description(self) -> str:
        return "Help documentation and usage examples"
    
    async def read(self) -> ResourceResult:
        help_content = """# Simpli5.AI Help Documentation

## Overview
Simpli5.AI is an extensible AI CLI with MCP server support that allows you to interact with various tools, resources, and prompts through a unified interface.

## Available Commands

### Basic Commands
- `/help` - Show this help
- `/tools` - List available tools
- `/resources` - List available resources
- `/prompts` - List available prompts
- `/exit` - Quit the chat interface

### Tool Commands
- `/call <tool_name> <arguments>` - Execute a tool
- `/call cli:run_command {"command": "ls -la"}` - Run system command
- `/call cli:list_servers {}` - List configured servers
- `/call cli:get_config {"section": "servers"}` - Get configuration

### Resource Commands
- `/read <resource_uri>` - Read a resource
- `/read config://config` - Read configuration
- `/read system://info` - Get system information
- `/read help://help` - Get help documentation

### Prompt Commands
- `/generate <prompt_name> <arguments>` - Generate content
- `/generate help {"topic": "tools"}` - Get tools help
- `/generate greeting {"name": "Alice"}` - Generate greeting

### Memory Commands
- `/memory <message>` - Categorize and store memory

## Examples

### Running System Commands
```bash
/call cli:run_command {"command": "ls -la"}
/call cli:run_command {"command": "ps aux", "timeout": 30}
```

### Getting Information
```bash
/call cli:list_servers {}
/call cli:get_config {"section": "all"}
/read system://info
```

### Generating Content
```bash
/generate greeting {"name": "John", "style": "formal"}
/generate help {"topic": "tools"}
```

## Configuration
- Server configuration: `config/mcp_servers.yml`
- LLM providers: `config/llm_providers.yml`
- Webhook configuration: Environment variables and CLI arguments

## Troubleshooting
- If tools are not found, ensure the corresponding server is running
- Check configuration files for proper API keys and URLs
- Use `/call cli:ping_server {"server_id": "server_name"}` to test connectivity
"""
        
        return ResourceResult(help_content, "text/markdown") 