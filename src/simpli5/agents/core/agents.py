"""
Core agents module for the multi-agent system.
"""

from typing import List, Optional, Dict, Any
from ...providers.mcp.multi import MultiServerProvider
from ...providers.llm.multi import MultiLLMProvider


class Agent:
    """Base class for agents with MCP server access."""
    
    def __init__(self, name: str, mcp_server_names: List[str], description: str):
        self.name = name
        self.mcp_server_names = mcp_server_names
        self.description = description
        self.mcp_provider: Optional[MultiServerProvider] = None
        self.llm_provider: Optional[MultiLLMProvider] = None
    
    async def initialize(self):
        """Initialize the agent and connect to MCP servers and LLM providers."""
        self.mcp_provider = MultiServerProvider(self.mcp_server_names)
        await self.mcp_provider.connect()
        
        self.llm_provider = MultiLLMProvider()
    
    async def cleanup(self):
        """Clean up resources and disconnect from MCP servers."""
        if self.mcp_provider:
            await self.mcp_provider.disconnect_all()
    
    def get_available_tools(self):
        """Get list of available tools from connected MCP servers."""
        if self.mcp_provider:
            return self.mcp_provider.list_all_tools()
        return []
    
    async def handle(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a user message. Must be implemented by subclasses.
        
        Args:
            user_message: The user's message
            context: Additional context for handling the message
            
        Returns:
            Dict with response and status
        """
        raise NotImplementedError("Subclasses must implement handle method")
