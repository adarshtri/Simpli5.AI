import json
from typing import Dict, Any, List
from ..common.base import BasePrompt, PromptResult

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