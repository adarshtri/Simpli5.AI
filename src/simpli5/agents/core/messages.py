from pydantic import BaseModel, Field
from typing import Union


class Message(BaseModel):
    """Base message class for all message types."""
    
    role: str = Field(..., description="Role of the message sender (e.g., user, assistant, system)")
    message: Union[str, dict] = Field(..., description="Content of the message (string or structured data)")


class UserMessage(Message):
    """Message class specifically for user messages with hard-coded role."""
    
    def __init__(self, message: Union[str, dict]):
        super().__init__(role="user", message=message)


class SystemMessage(Message):
    """Message class specifically for system messages with hard-coded role."""
    
    def __init__(self, message: Union[str, dict]):
        super().__init__(role="system", message=message)
