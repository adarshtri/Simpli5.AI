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
        self.execution_history: List[Any] = []
        self.agent_context = {
            "agent_name": name,
            "agent_description": description,
            "execution_history": self.execution_history
        }
    
    async def initialize(self):
        """Initialize the agent and connect to MCP servers and LLM providers."""
        self.mcp_provider = MultiServerProvider(self.mcp_server_names)
        await self.mcp_provider.connect()
        
        self.llm_provider = MultiLLMProvider()
        self.agent_context["llm_provider"] = self.llm_provider
        self.agent_context["mcp_provider"] = self.mcp_provider
    
    async def cleanup(self):
        """Clean up resources and disconnect from MCP servers."""
        if self.mcp_provider:
            await self.mcp_provider.disconnect_all()
    
    def get_available_tools(self):
        """Get list of available tools from connected MCP servers."""
        if self.mcp_provider:
            return self.mcp_provider.list_all_tools()
        return []
    
    def add_to_execution_history(self, step_result: Any):
        """Add a step result to the execution history."""
        self.execution_history.append(step_result)
    
    def format_execution_history(self, user_message: str) -> str:
        """
        Format execution history into a readable string for step context.
        
        Args:
            user_message: The original user message that triggered the execution
            
        Returns:
            Formatted string showing user message and all step results
        """
        if not self.execution_history:
            return f"No steps executed yet."
        
        formatted_parts = []
        
        for i, step_result in enumerate(self.execution_history, 1):
            formatted_parts.append(f"Step {i}:")
            formatted_parts.append(f"Name: {step_result.step_name}")
            formatted_parts.append(f"Result: {step_result.result}")
            formatted_parts.append("\n")  # Empty line for readability
        
        return "\n".join(formatted_parts)
    
    async def execute_step(self, step, inputs, context: Dict[str, Any]):
        """
        Execute a step and automatically track its result in execution history.
        
        Args:
            step: The step to execute
            inputs: Input data for the step
            context: Execution context
            
        Returns:
            The step execution result
        """        
        # Merge agent context with step context to ensure steps have access to providers
        step_context = {**context, **self.agent_context}
        
        # Execute the step
        result = await step.execute(inputs, step_context)

        # Update execution history and agent context
        self.add_to_execution_history(result)        
        self.agent_context["execution_history"] = self.execution_history
        return result
    
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
