import json
import logging
from typing import Dict, Any
from ..common.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

class TelegramMemoryCategorizerTool(BaseTool):
    """Tool to categorize and store memory from Telegram messages."""
    
    @property
    def name(self) -> str:
        return "telegram_memory_categorizer"
    
    @property
    def description(self) -> str:
        return "Categorize and store memory from Telegram messages"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message content to categorize"
                }
            },
            "required": ["message"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        """Execute the memory categorization."""
        message = arguments.get("message", "")
        
        if not message:
            return ToolResult(
                content="No message provided for categorization"
            )
        
        # For now, return a simple categorization
        # Later this will be enhanced with AI categorization
        category = self._categorize_message(message)
        
        # Convert result to JSON string for ToolResult
        result_content = {
            "category": category,
            "content": message,
            "original_message": message
        }
        
        return ToolResult(
            content=str(result_content)
        )
    
    def _categorize_message(self, message: str) -> str:
        """
        Categorize a memory message.
        This is a simple implementation - will be enhanced with AI later.
        """
        message_lower = message.lower()
        
        # Simple keyword-based categorization
        profile_keywords = ["i'm", "i am", "my name", "i work", "i have", "experience", "degree", "live in"]
        preference_keywords = ["i prefer", "i like", "i enjoy", "i want", "i need", "favorite", "best"]
        context_keywords = ["currently", "working on", "learning", "trying to", "building", "debugging", "meeting"]
        
        # Check for profile indicators
        if any(keyword in message_lower for keyword in profile_keywords):
            return "profile"
        
        # Check for preference indicators
        if any(keyword in message_lower for keyword in preference_keywords):
            return "preference"
        
        # Check for context indicators
        if any(keyword in message_lower for keyword in context_keywords):
            return "context"
        
        # Default to context if unclear
        return "context" 