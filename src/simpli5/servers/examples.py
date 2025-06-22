import json
import os
from datetime import datetime
from typing import Dict, Any, List
from .base import BaseTool, BaseResource, BasePrompt, ToolResult, ResourceResult

class GreetingTool(BaseTool):
    """Simple greeting tool."""
    
    @property
    def name(self) -> str:
        return "greeting"
    
    @property
    def description(self) -> str:
        return "Generate a personalized greeting"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the person to greet"
                },
                "time_of_day": {
                    "type": "string",
                    "description": "Time of day (morning, afternoon, evening)",
                    "enum": ["morning", "afternoon", "evening"]
                }
            },
            "required": ["name"] 
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        name = arguments["name"]
        time_of_day = arguments.get("time_of_day", "day")
        
        greetings = {
            "morning": "Good morning",
            "afternoon": "Good afternoon", 
            "evening": "Good evening",
            "day": "Hello"
        }
        
        greeting = greetings.get(time_of_day, "Hello")
        return ToolResult(f"{greeting}, {name}! How can I help you today?")
    

class CalculatorTool(BaseTool):
    """Simple calculator tool."""
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Perform basic arithmetic operations"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": f"Possible values are {["add", "subtract", "multiply", "divide"]}"
                },
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "required": ["operation", "a", "b"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        operation = arguments["operation"]
        a = arguments["a"]
        b = arguments["b"]
        
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return ToolResult("Error: Division by zero")
            result = a / b
        else:
            return ToolResult("Error: Invalid operation")
        
        return ToolResult(f"Result: {result}")

class EchoTool(BaseTool):
    """Simple echo tool."""
    
    @property
    def name(self) -> str:
        return "echo"
    
    @property
    def description(self) -> str:
        return "Echo back the input message"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string"}
            },
            "required": ["message"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        message = arguments["message"]
        return ToolResult(f"Echo: {message}")

class SystemInfoResource(BaseResource):
    """System information resource."""
    
    @property
    def uri(self) -> str:
        return "system://info"
    
    @property
    def name(self) -> str:
        return "System Information"
    
    @property
    def description(self) -> str:
        return "Get current system information"
    
    async def read(self) -> ResourceResult:
        info = {
            "timestamp": datetime.now().isoformat(),
            "platform": os.name,
            "cwd": os.getcwd(),
            "env_vars": list(os.environ.keys())
        }
        return ResourceResult(
            content=json.dumps(info, indent=2),
            mime_type="application/json"
        )

class FileResource(BaseResource):
    """File reading resource."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    @property
    def uri(self) -> str:
        return f"file://{self.file_path}"
    
    @property
    def name(self) -> str:
        return f"File: {self.file_path}"
    
    @property
    def description(self) -> str:
        return f"Read content from {self.file_path}"
    
    async def read(self) -> ResourceResult:
        try:
            with open(self.file_path, 'r') as f:
                content = f.read()
            return ResourceResult(content=content, mime_type="text/plain")
        except Exception as e:
            return ResourceResult(content=f"Error reading file: {str(e)}", mime_type="text/plain")

class GreetingPrompt(BasePrompt):
    """Greeting prompt template."""
    
    @property
    def name(self) -> str:
        return "greeting"
    
    @property
    def description(self) -> str:
        return "Generate a personalized greeting"
    
    @property
    def arguments(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "name",
                "description": "Name of the person to greet",
                "type": "string",
                "required": True
            },
            {
                "name": "time_of_day",
                "description": "Time of day (morning, afternoon, evening)",
                "type": "string",
                "required": False
            }
        ]
    
    async def generate(self, arguments: Dict[str, Any]) -> str:
        name = arguments["name"]
        time_of_day = arguments.get("time_of_day", "day")
        
        greetings = {
            "morning": "Good morning",
            "afternoon": "Good afternoon", 
            "evening": "Good evening",
            "day": "Hello"
        }
        
        greeting = greetings.get(time_of_day, "Hello")
        return f"{greeting}, {name}! How can I help you today?" 