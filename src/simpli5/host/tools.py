import json
import subprocess
import os
from typing import Dict, Any, List
from ..servers.base import BaseTool, ToolResult
from ..config import ConfigManager

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

class RunCommandTool(BaseTool):
    """Tool to run system commands."""
    
    @property
    def name(self) -> str:
        return "run_command"
    
    @property
    def description(self) -> str:
        return "Run a system command and return the output"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The command to run"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30)",
                    "default": 30
                }
            },
            "required": ["command"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        command = arguments["command"]
        timeout = arguments.get("timeout", 30)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = {
                "command": command,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            return ToolResult(json.dumps(output, indent=2))
        except subprocess.TimeoutExpired:
            return ToolResult(f"Command timed out after {timeout} seconds")
        except Exception as e:
            return ToolResult(f"Error running command: {str(e)}")

class GetConfigTool(BaseTool):
    """Tool to get CLI configuration information."""
    
    @property
    def name(self) -> str:
        return "get_config"
    
    @property
    def description(self) -> str:
        return "Get CLI configuration and system information"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "description": "Configuration section to retrieve (servers, system, all)",
                    "enum": ["servers", "system", "all"],
                    "default": "all"
                }
            },
            "required": []
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        section = arguments.get("section", "all")
        config = ConfigManager()
        
        result = {}
        
        if section in ["servers", "all"]:
            servers = config.list_servers()
            result["servers"] = {
                server_id: {
                    "name": server_config.name,
                    "url": server_config.url,
                    "description": server_config.description,
                    "enabled": server_config.enabled
                }
                for server_id, server_config in servers
            }
        
        if section in ["system", "all"]:
            result["system"] = {
                "cwd": os.getcwd(),
                "platform": os.name,
                "config_path": config.config_path,
                "config_exists": os.path.exists(config.config_path)
            }
        
        return ToolResult(json.dumps(result, indent=2))

class PingServerTool(BaseTool):
    """Tool to test connectivity to MCP servers."""
    
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
                    "description": "Server ID to ping"
                }
            },
            "required": ["server_id"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        server_id = arguments["server_id"]
        config = ConfigManager()
        
        server = config.get_server(server_id)
        if not server:
            return ToolResult(f"Server '{server_id}' not found in configuration")
        
        try:
            from ..providers.mcp_client import MCPClientProvider
            provider = MCPClientProvider(server.url)
            tools = await provider.list_tools()
            return ToolResult(f"Successfully connected to {server_id}. Found {len(tools)} tools.")
        except Exception as e:
            return ToolResult(f"Failed to connect to {server_id}: {str(e)}") 