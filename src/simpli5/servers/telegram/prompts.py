from typing import Dict, List, Any
from ..common import BasePrompt, PromptResult

class MemoryCategorizationPrompt(BasePrompt):
    """Prompt for categorizing user messages into memory types."""
    
    @property
    def name(self) -> str:
        return "memory_categorization"
    
    @property
    def description(self) -> str:
        return "Categorizes user messages into memory types for storage"
    
    @property
    def arguments(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "user_message",
                "type": "string",
                "description": "The user's message to categorize",
                "required": True
            }
        ]
    
    async def generate(self, arguments: Dict[str, Any]) -> PromptResult:
        """Generate the memory categorization prompt."""
        user_message = arguments.get("user_message", "")
        
        prompt_text = f"""You are a memory categorization system. Your job is to analyze user messages and categorize them into appropriate memory types for storage.

Categorize the following user message into one of these categories:

1. **profile** - Personal information like age, birthday, gender, location, job, etc.
2. **preference** - Long-term preferences, likes/dislikes, habits, etc.
3. **context** - Short-term contextual information, current activities, temporary situations
4. **not_applicable** - Messages that shouldn't be stored as memory

Examples:
- "I'm 25 years old" → profile
- "My birthday is March 15th" → profile
- "I don't like sweet food" → preference
- "I prefer rock music" → preference
- "I'm learning guitar right now" → context
- "I'm working on a new project" → context
- "Hello" → not_applicable
- "How are you?" → not_applicable

User message: "{user_message}"

Respond with ONLY the category name (profile, preference, context, or not_applicable)."""
        
        return PromptResult(content=prompt_text) 