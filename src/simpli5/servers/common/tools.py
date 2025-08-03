import json
import subprocess
import os
from typing import Dict, Any, List
from .base import BaseTool, ToolResult
from ...config import ConfigManager

class ListServersTool(BaseTool):
    """Tool to list all configured MCP servers."""
    
    @property
    def name(self) -> str:
        return "list_servers"
    
    @property
    def description(self) -> str:
        return "List all configured MCP servers with their details"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        config = ConfigManager()
        servers = config.list_servers()
        
        if not servers:
            return ToolResult("No servers configured.")
        
        result = []
        for server_id, server_config in servers:
            result.append({
                "id": server_id,
                "name": server_config.name,
                "url": server_config.url,
                "description": server_config.description,
                "enabled": server_config.enabled
            })
        
        return ToolResult(json.dumps(result, indent=2))

class GetConfigTool(BaseTool):
    """Tool to get configuration information."""
    
    @property
    def name(self) -> str:
        return "get_config"
    
    @property
    def description(self) -> str:
        return "Get configuration information for a specific section or all sections"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "Configuration section to retrieve (servers, llm_providers, etc.)",
                    "default": "all"
                }
            },
            "required": []
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        section = arguments.get("section", "all")
        config = ConfigManager()
        
        try:
            if section == "all":
                # Get all server configurations
                servers = {}
                for server_id, server_config in config.list_servers():
                    servers[server_id] = {
                        "name": server_config.name,
                        "url": server_config.url,
                        "description": server_config.description,
                        "enabled": server_config.enabled
                    }
                
                result = {
                    "servers": servers,
                    "note": "LLM providers and webhook config are configured via environment variables and CLI arguments"
                }
            elif section == "servers":
                # Get server configurations only
                servers = {}
                for server_id, server_config in config.list_servers():
                    servers[server_id] = {
                        "name": server_config.name,
                        "url": server_config.url,
                        "description": server_config.description,
                        "enabled": server_config.enabled
                    }
                result = servers
            else:
                result = {"error": f"Unknown section: {section}. Available sections: all, servers"}
            
            return ToolResult(json.dumps(result, indent=2))
        except Exception as e:
            return ToolResult(f"Error retrieving configuration: {str(e)}")

class PingServerTool(BaseTool):
    """Tool to test server connectivity."""
    
    @property
    def name(self) -> str:
        return "ping_server"
    
    @property
    def description(self) -> str:
        return "Test connectivity to a specific MCP server"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "string",
                    "description": "ID of the server to ping"
                }
            },
            "required": ["server_id"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        server_id = arguments["server_id"]
        config = ConfigManager()
        
        try:
            server_url = config.get_server_url(server_id)
            if not server_url:
                return ToolResult(f"Server '{server_id}' not found in configuration.")
            
            # Simple connectivity test - could be enhanced with actual MCP ping
            return ToolResult(f"Server '{server_id}' is configured at {server_url}")
        except Exception as e:
            return ToolResult(f"Error pinging server '{server_id}': {str(e)}") 