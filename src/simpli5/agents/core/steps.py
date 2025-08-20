"""
AgenticStep classes for defining and executing agent steps.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from simpli5.agents.core.messages import Message, SystemMessage


class AgenticStepResult(BaseModel):
    """Result of executing an agentic step."""
    
    step_name: str = Field(..., description="Name of the step that was executed")
    result: Union[Dict[str, Any], SystemMessage] = Field(..., description="Result data from the step or SystemMessage object")
    
    def get_response_json(self) -> SystemMessage:
        """
        Always returns a SystemMessage object.
        If result is already a SystemMessage, returns it directly.
        If result is a dict, wraps it in a SystemMessage.
        """
        if isinstance(self.result, SystemMessage):
            return self.result
        else:
            return SystemMessage(message=self.result)


class AgenticStep(ABC):
    """Base class for all agentic steps."""
    
    def __init__(self, name: str, description: str, agent_context: Dict[str, Any]):
        self.name = name
        self.description = description
        self.agent_specific_context = agent_context
    
    @abstractmethod
    async def execute(self, inputs: Message, context: Dict[str, Any]) -> AgenticStepResult:
        """
        Execute this step with given inputs and context.
        
        Args:
            inputs: Message object containing the message
            context: Execution context (LLM provider, MCP provider, etc.)
            
        Returns:
            AgenticStepResult containing step execution results
        """
        pass
    
    @abstractmethod
    def get_prompt(self, inputs: Message, context: Dict[str, Any]) -> str:
        """
        Generate the prompt for this step.
        
        Args:
            inputs: Message object containing the message
            context: Execution context
            
        Returns:
            Prompt string for LLM or other processing
        """
        pass
    
    def __str__(self):
        return f"{self.name}"
    
    def __repr__(self):
        return f"AgenticStep(name='{self.name}')"