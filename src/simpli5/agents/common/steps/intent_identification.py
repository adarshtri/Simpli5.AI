"""
Intent identification step for all agents.
This step analyzes user messages to determine what the user wants to accomplish.
"""

from typing import Dict, Any

from simpli5.agents.core.messages import Message, SystemMessage
from ...core.steps import AgenticStep, AgenticStepResult


class IntentIdentificationStep(AgenticStep):
    """Generic step for identifying user intent that can be used by any agent."""
    
    def __init__(self, agent_specific_context: Dict[str, str]):
        super().__init__(
            name="IntentIdentification",
            description="Identifies user intent based on agent context and capabilities",
            agent_context=agent_specific_context
        )
        self.agent_specific_context = agent_specific_context
    
    def get_prompt(self, inputs: Message, context: Dict[str, Any]) -> str:
        user_message = inputs.message
        available_tools = context.get("available_tools", [])
        agent_name = self.agent_specific_context.get("agent_name", "Unknown Agent")
        agent_description = self.agent_specific_context.get("agent_description", "No description available")
        
        # Build tools description
        tools_description = ""
        if available_tools:
            tools_description = "\nAvailable Tools:\n"
            for tool in available_tools:
                if isinstance(tool, (list, tuple)) and len(tool) >= 3:
                    tool_name = tool[0]
                    tool_info = tool[2]
                    tools_description += f"- {tool_name}: {tool_info.description}\n"
                else:
                    tools_description += f"- {tool}\n"
        
        return f"""
You are part of the {agent_name} agent.

Agent Description: {agent_description}

User Message: "{user_message}"

{tools_description}

Your task is to identify the user's intent. Consider:

1. **Primary Intent**: What is the user trying to accomplish?
2. **Action Required**: What action should your agent take?
3. **Information Needed**: What information does the user need?
4. **Tool Requirements**: Which tools (if any) might be needed?
5. **Context Understanding**: What additional context can you infer?

Respond with a clear, specific intent that your agent can act upon.
Be concise but comprehensive in your analysis.
"""
    
    async def execute(self, inputs: Message, context: Dict[str, Any]) -> AgenticStepResult:
        # Get LLM to identify intent
        llm_provider = context.get("llm_provider")
        if not llm_provider:
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message={
                    "error": "LLM provider not available",
                    "intent": "unknown",
                    "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent")
                })
            )
        
        try:
            prompt = self.get_prompt(inputs, context)
            
            # Define the required JSON fields and their descriptions
            required_fields = {
                "intent": "The primary intent of the user's message",
                "confidence": "Confidence level in the intent identification (high/medium/low)",
                "entities": "List of key entities mentioned in the message",
            }
            
            # Use the JSON-enforced method to get structured response from LLM
            json_response = llm_provider.generate_json_response(prompt, required_fields)
            
            # Create a new SystemMessage with additional agent context
            result_data = json_response.message.copy() if hasattr(json_response, 'message') else json_response
            result_data.update({
                "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent"),
                "agent_description": self.agent_specific_context.get("agent_description", "No description available"),
                "user_message": inputs.message,
                "reasoning": f"Intent identified based on {self.agent_specific_context.get('agent_name', 'Unknown')} agent context and capabilities"
            })
            
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message=result_data)
            )
            
        except Exception as e:
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message={
                    "error": f"Failed to identify intent: {str(e)}",
                    "intent": "unknown",
                    "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent")
                })
            )
