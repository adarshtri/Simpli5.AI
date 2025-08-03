import json
import subprocess
import os
from typing import Dict, Any
from ..common.base import BaseTool, ToolResult

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