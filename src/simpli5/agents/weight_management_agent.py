"""
New Weight Management Agent for handling weight-related operations using the new step architecture.
"""

from .core.agents import Agent
from .common.steps import IntentIdentificationStep, ToolSelectionAndExecutionStep, ResponseGenerationStep
from .core.messages import UserMessage
from typing import Dict, Any, Optional
import traceback


class WeightManagementAgent(Agent):
    """New Weight Management Agent using step-based architecture for weight tracking and fitness goals."""
    
    def __init__(self):
        """Initialize the Weight Management Agent with access to weight_management_agent MCP server."""
        super().__init__("WeightManagementAgent", ["weight_management_agent"], "Handles weight management messages, tracking, and fitness goal activities")
        
        # Initialize the steps
        self.intent_step = IntentIdentificationStep(self.agent_context)
        self.tool_step = ToolSelectionAndExecutionStep(self.agent_context)
        self.response_step = ResponseGenerationStep(self.agent_context)
    
    async def handle(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle weight management user messages using the new step-based architecture.
        
        Args:
            user_message: The user's message
            context: Additional context (e.g., user_id, metadata)
            
        Returns:
            Dict with response and status
        """
        print(f"⚖️ WeightManagementAgent: Received message: '{user_message}'")
        print(f"⚖️ WeightManagementAgent: Context: {context}")

        context = self.agent_context | context

        try:
            # Create user message object
            user_msg = UserMessage(user_message)
            
            # Step 1: Identify user intent
            print(f"⚖️ WeightManagementAgent: Executing Intent Identification step...")
            intent_result = await self.execute_step(self.intent_step, user_msg, context)
            print(f"\n\n⚖️ WeightManagementAgent: Intent result: {intent_result}\n\n")
            
            # Step 2: Select and execute tools
            print(f"⚖️ WeightManagementAgent: Executing Tool Selection and Execution step...")
            tool_result = await self.execute_step(self.tool_step, user_msg, context)
            print(f"\n\n⚖️ WeightManagementAgent: Tool result: {tool_result}\n\n")
            
            # Step 3: Generate final response
            print(f"⚖️ WeightManagementAgent: Executing Response Generation step...")
            response_result = await self.execute_step(self.response_step, user_msg, context)
            print(f"\n\n⚖️ WeightManagementAgent: Response result: {response_result}\n\n")
            
            # Extract the final response
            if hasattr(response_result, 'result') and hasattr(response_result.result, 'message'):
                final_response = response_result.result.message.get('response', 'No response generated')
            else:
                final_response = str(response_result)
            
            print(f"⚖️ WeightManagementAgent: Final response: {final_response}")
            
            return {
                "status": "success",
                "message": final_response,
                "execution_history": self.execution_history
            }
                
        except Exception as e:
            print(f"⚖️ WeightManagementAgent: Error occurred: {str(e)}")
            print(f"⚖️ WeightManagementAgent: Error traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error processing weight management message: {str(e)}",
                "execution_history": self.execution_history
            }
    
    def get_available_tools(self):
        """Get list of available tools from connected MCP servers."""
        if self.mcp_provider:
            return self.mcp_provider.list_all_tools()
        return []
