"""
User response generation step for all agents.
This step creates a final response based on the original user request and all executed steps.
"""

from typing import Dict, Any, List
from ...core.steps import AgenticStep, AgenticStepResult
from ...core.messages import SystemMessage, Message


class ResponseGenerationStep(AgenticStep):
    """Generic step for generating final user responses based on executed steps."""
    
    def __init__(self, agent_specific_context: Dict[str, str]):
        super().__init__(
            name="ResponseGeneration",
            description="Generates final user response based on executed steps and original request",
            agent_context=agent_specific_context
        )
        self.agent_specific_context = agent_specific_context
    
    def get_prompt(self, inputs: Message, context: Dict[str, Any]) -> str:
        """
        Generate a prompt for response generation.
        This step uses LLM to synthesize a coherent response.
        IMPORTANT: Don't hallucinate or make up any information. It is crucial that the final response is context aware of the previous steps and other related information.
        """
        user_message = inputs.message
        agent_name = self.agent_specific_context.get("agent_name", "Unknown Agent")
        agent_description = self.agent_specific_context.get("agent_description", "No description available")
        
        execution_history = context.get("execution_history")

        if len(execution_history) == 0:
            print(f"\n\n\n*********\n\n💼 ResponseGenerationStep: No execution history\n\n*********\n\n")
        
        return f"""
IMPORTANT: Don't reveal any internal information in the response. Try to just respond to the user's request.
You are a helpful assistant responding to a user's request. The user asked: "{user_message}"

Based on what has been accomplished, provide a natural, helpful response that directly addresses their request.

Your response should:
- Be conversational and human-like
- Focus on what the user asked for
- Provide helpful information or assistance
- Feel like a natural conversation between two people
- Not mention any technical details about how the response was generated

Respond as if you're a helpful person who just helped them with their request.

Step Summary: {execution_history}

Use step summary to derive information to base your response on. Don't hallucinate or make up any information.
"""
    
    async def execute(self, inputs: Message, context: Dict[str, Any]) -> AgenticStepResult:
        """Generate the final user response based on executed steps."""
        # Get LLM provider for response generation
        llm_provider = context.get("llm_provider")
        if not llm_provider:
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message={
                    "error": "LLM provider not available",
                    "response": "I'm sorry, but I'm unable to generate a response at the moment due to technical difficulties.",
                    "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent")
                })
            )
        
        try:
            prompt = self.get_prompt(inputs, context)
            
            # Generate the response using the LLM
            response = llm_provider.generate_response(prompt)
            
            # Prepare the final result
            result_data = {
                "response": response,
                "original_request": inputs.message,
                "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent"),
                "agent_description": self.agent_specific_context.get("agent_description", "No description available"),
                "step_name": self.name,
                "response_type": "final_user_response",
                "generation_timestamp": "now",  # Could be enhanced with actual timestamp
                "summary": "Final response generated based on user request and executed steps"
            }
            
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message=result_data)
            )
            
        except Exception as e:
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message={
                    "error": f"Failed to generate response: {str(e)}",
                    "response": "I apologize, but I encountered an error while generating your response. Please try again.",
                    "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent")
                })
            )
