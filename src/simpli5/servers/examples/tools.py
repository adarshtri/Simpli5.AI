import json
import os
from datetime import datetime
from typing import Dict, Any
from ..common.base import BaseTool, ToolResult

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
                "message": {
                    "type": "string",
                    "description": "Message to echo back"
                }
            },
            "required": ["message"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        message = arguments["message"]
        return ToolResult(f"Echo: {message}") 