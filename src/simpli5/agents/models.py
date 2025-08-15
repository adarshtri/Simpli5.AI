"""
Pydantic models for structured LLM responses and agent communication.
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class ToolCall(BaseModel):
    """Model for a single tool call specification."""
    tool_name: str = Field(..., description="Name of the tool to call")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool call")


class LLMResponse(BaseModel):
    """Model for structured LLM responses."""
    intent: str = Field(..., description="Brief description of what the user wants")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="List of tools to call")
    response: str = Field(..., description="Helpful response to the user")
    
    @validator('tool_calls')
    def validate_tool_calls(cls, v):
        """Ensure tool calls have valid structure."""
        for tool_call in v:
            if not tool_call.tool_name:
                raise ValueError("Tool name cannot be empty")
        return v


class AgentResponse(BaseModel):
    """Model for agent responses."""
    status: str = Field(..., description="Response status (success, error, etc.)")
    message: str = Field(..., description="Main response message")
    intent: Optional[str] = Field(None, description="Intent classification")
    tool_results: Optional[Dict[str, Any]] = Field(None, description="Results from tool execution")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class MultiAgentResponse(BaseModel):
    """Model for multi-agent controller responses."""
    name: str = Field(..., description="Name of the selected agent")
    reason: str = Field(..., description="Reason for selecting this agent")
    response: Union[AgentResponse, str] = Field(..., description="Response from the selected agent")


class LLMResponseParser:
    """Helper class to parse and validate LLM responses."""
    
    @staticmethod
    def parse_llm_response(response_text: str) -> Optional[LLMResponse]:
        """
        Parse LLM response text into structured LLMResponse object.
        
        Args:
            response_text: Raw text response from LLM
            
        Returns:
            Parsed LLMResponse or None if parsing fails
        """
        try:
            # Clean up response and try to extract JSON
            cleaned_response = response_text.strip()
            
            # Try to find JSON in the response
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = cleaned_response[start_idx:end_idx]
                import json
                parsed_data = json.loads(json_str)
                
                # Create LLMResponse object (this will validate the structure)
                return LLMResponse(**parsed_data)
            else:
                return None
                
        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return None
    
    @staticmethod
    def create_fallback_response(user_message: str, error: str) -> LLMResponse:
        """
        Create a fallback response when LLM parsing fails.
        
        Args:
            user_message: Original user message
            error: Error description
            
        Returns:
            Fallback LLMResponse
        """
        return LLMResponse(
            intent="fallback_response",
            tool_calls=[],
            response=f"I'm sorry, I'm having trouble understanding your request right now. Please try rephrasing: '{user_message}'"
        )


class ResponseFormatter:
    """Helper class to format responses for different output types."""
    
    @staticmethod
    def format_for_telegram(response: Union[MultiAgentResponse, AgentResponse, str]) -> str:
        """
        Format response for Telegram output.
        
        Args:
            response: Response from agent or multi-agent controller
            
        Returns:
            Formatted string for Telegram
        """
        if isinstance(response, MultiAgentResponse):
            # Extract the actual message from nested response
            if isinstance(response.response, AgentResponse):
                return response.response.message
            else:
                return str(response.response)
        
        elif isinstance(response, AgentResponse):
            return response.message
        
        else:
            return str(response)
    
    @staticmethod
    def format_for_logging(response: Union[MultiAgentResponse, AgentResponse, str]) -> str:
        """
        Format response for logging purposes.
        
        Args:
            response: Response from agent or multi-agent controller
            
        Returns:
            Formatted string for logging
        """
        if isinstance(response, MultiAgentResponse):
            return f"MultiAgent[{response.name}]: {response.reason}"
        
        elif isinstance(response, AgentResponse):
            return f"Agent[{response.status}]: {response.message}"
        
        else:
            return f"String: {response}"
