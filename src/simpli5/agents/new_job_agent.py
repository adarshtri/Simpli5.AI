"""
New Job Agent for handling job-related operations using the new step architecture.
"""

from .core.agents import Agent
from .common.steps import IntentIdentificationStep, ToolSelectionAndExecutionStep, ResponseGenerationStep
from .core.messages import UserMessage
from typing import Dict, Any, Optional
import traceback


class NewJobAgent(Agent):
    """New Job Agent using step-based architecture for job-related operations."""
    
    def __init__(self):
        """Initialize the New Job Agent with access to job_agent MCP server."""
        super().__init__("NewJobAgent", ["job_agent"], "Handles job-related messages, applications, career discussions, and job search activities")
        
        # Initialize the steps
        self.intent_step = IntentIdentificationStep(self.agent_context)
        self.tool_step = ToolSelectionAndExecutionStep(self.agent_context)
        self.response_step = ResponseGenerationStep(self.agent_context)
    
    async def handle(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle job-related user messages using the new step-based architecture.
        
        Args:
            user_message: The user's message
            context: Additional context (e.g., user_id, metadata)
            
        Returns:
            Dict with response and status
        """
        print(f"💼 NewJobAgent: Received message: '{user_message}'")

        self.execution_history = []
        self.agent_context["execution_history"] = []

        context = self.agent_context | context

        try:
            # Create user message object
            user_msg = UserMessage(user_message)
            
            # Step 1: Identify user intent
            intent_result = await self.execute_step(self.intent_step, user_msg, context)
            
            # Step 2: Select and execute tools
            tool_result = await self.execute_step(self.tool_step, user_msg, context)
            
            # Step 3: Generate final response
            response_result = await self.execute_step(self.response_step, user_msg, context)
             
            # Extract the final response
            if hasattr(response_result, 'result') and hasattr(response_result.result, 'message'):
                final_response = response_result.result.message.get('response', 'No response generated')
            else:
                final_response = str(response_result)
                        
            return {
                "status": "success",
                "message": final_response,
                "execution_history": self.execution_history
            }
                
        except Exception as e:
            print(f"💼 NewJobAgent: Error occurred: {str(e)}")
            print(f"💼 NewJobAgent: Error traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error processing job-related message: {str(e)}",
                "execution_history": self.execution_history
            }
    
    def get_available_tools(self):
        """Get list of available tools from connected MCP servers."""
        if self.mcp_provider:
            return self.mcp_provider.list_all_tools()
        return []
