"""
Multi-Agent Controller for routing messages to appropriate agents.
"""

from typing import Dict, Any, List, Optional, Union
from .core.agents import Agent
from .job_agent import JobAgent
from .models import MultiAgentResponse, AgentResponse


class MultiAgentController(Agent):
    """Controller agent that routes messages to appropriate specialized agents."""
    
    def __init__(self, available_agents: List[Agent]):
        """
        Initialize the Multi-Agent Controller.
        
        Args:
            available_agents: List of available agents to route messages to
        """
        super().__init__("MultiAgentController", [], "Routes user messages to appropriate specialized agents using LLM-based selection")
        self.available_agents = available_agents
    
    async def initialize(self):
        """Initialize the controller and all available agents."""
        # Initialize the controller's own providers
        await super().initialize()
        
        # Initialize all available agents
        print(f"🔀 MultiAgentController: Initializing {len(self.available_agents)} agents...")
        for agent in self.available_agents:
            try:
                await agent.initialize()
                print(f"🔀 MultiAgentController: Successfully initialized {agent.name}")
            except Exception as e:
                print(f"🔀 MultiAgentController: Failed to initialize {agent.name}: {e}")
                # Continue with other agents even if one fails
    
    async def handle(self, user_message: str, context: Dict[str, Any]) -> Union[MultiAgentResponse, str]:
        """
        Route user message to appropriate agent using LLM.
        
        Args:
            user_message: The user's message
            context: Additional context (e.g., user_id, metadata)
            
        Returns:
            Dict with response from selected agent
        """
        print(f"🔀 MultiAgentController: Received message: '{user_message}'")
        print(f"🔀 MultiAgentController: Context: {context}")
        
        try:
            # Use LLM to determine which agent should handle the message
            print(f"🔀 MultiAgentController: Selecting agent for message...")
            selection_result = await self._select_agent(user_message)
            
            if selection_result:
                selected_agent = selection_result["agent"]
                selection_reason = selection_result["reason"]
                
                if selected_agent:
                    print(f"🔀 MultiAgentController: Selected agent: {selected_agent.name}")
                    print(f"🔀 MultiAgentController: Selection reason: {selection_reason}")
                    print(f"🔀 MultiAgentController: Routing message to {selected_agent.name}...")
                    
                    # Route message to selected agent and return its response
                    agent_response = await selected_agent.handle(user_message, context)
                    print(f"🔀 MultiAgentController: Got response from {selected_agent.name}: {agent_response}")
                    
                    # Return structured MultiAgentResponse
                    return MultiAgentResponse(
                        name=selected_agent.name,
                        reason=selection_reason,
                        response=agent_response
                    )
                else:
                    print(f"🔀 MultiAgentController: No agent selected, but have reason: {selection_reason}")
                    return f"No suitable agent found to handle this message. Reason: {selection_reason}"
                    
            else:
                print(f"🔀 MultiAgentController: No selection result available")
                return "No suitable agent found to handle this message."
                
        except Exception as e:
            print(f"🔀 MultiAgentController: Error occurred: {str(e)}")
            return f"Error routing message: {str(e)}"
    
    async def _select_agent(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM to select the most appropriate agent for the message.
        
        Args:
            user_message: The user's message
            
        Returns:
            Selected agent or None if no suitable agent found
        """
        if not self.llm_provider or not self.llm_provider.has_provider():
            return None
        
        try:
            # Create agent descriptions for LLM
            agent_descriptions = []
            for agent in self.available_agents:
                agent_descriptions.append(f"{agent.name}: {agent.description}")
            
            print(f"🔀 MultiAgentController: Available agents:")
            for desc in agent_descriptions:
                print(f"   - {desc}")
            
            # Build prompt for LLM
            prompt = f"""
You are a multi-agent controller. Your task is to select the most appropriate agent to handle a user message. Don't select an agent if you are not completely sure. It's better to not select an agent than to select an agent that is not suitable. Don't make guesses.

Available agents:
{chr(10).join(agent_descriptions)}

User message: "{user_message}"

Based on the user message, select the most appropriate agent and provide a reason for your selection.

IMPORTANT: You must ALWAYS provide a reason, whether you select an agent or not.

Respond with a JSON object in this exact format:
{{"name": "AgentName", "reason": "Your detailed reason for selecting this agent"}}

If no agent is suitable, respond with:
{{"name": "none", "reason": "Your detailed explanation of why no agent is suitable for this message"}}

Examples:
- For job-related messages: {{"name": "JobAgent", "reason": "This message discusses job applications and career activities, which directly matches the JobAgent's specialization in job-related messages and career discussions."}}
- For unrelated messages: {{"name": "none", "reason": "This message appears to be a general greeting or casual conversation that doesn't relate to any of the available specialized agents. The available agents are focused on specific domains (job-related activities) and this message doesn't fall within their scope."}}
"""
            
            print(f"🔀 MultiAgentController: LLM Prompt:")
            print(f"   {prompt}")
            
            # Get LLM response
            print(f"🔀 MultiAgentController: Calling LLM...")
            response = self.llm_provider.generate_response(prompt)
            print(f"🔀 MultiAgentController: LLM Response: '{response}'")
            
            # Parse JSON response from LLM
            try:
                import json
                llm_selection = json.loads(response.strip())
                selected_agent_name = llm_selection.get("name")
                selection_reason = llm_selection.get("reason")
                
                print(f"🔀 MultiAgentController: Parsed LLM response - Agent: '{selected_agent_name}', Reason: '{selection_reason}'")
                
                # Check if no agent selected
                if selected_agent_name.lower() == "none":
                    print(f"🔀 MultiAgentController: LLM selected 'none' - no suitable agent")
                    return {
                        "agent": None,
                        "reason": selection_reason
                    }
                
                # Find agent by name
                for agent in self.available_agents:
                    if agent.name.lower() == selected_agent_name.lower():
                        print(f"🔀 MultiAgentController: Found matching agent: {agent.name}")
                        return {
                            "agent": agent,
                            "reason": selection_reason
                        }
                
                print(f"🔀 MultiAgentController: No agent found with name: '{selected_agent_name}'")
                return None
                
            except json.JSONDecodeError as e:
                print(f"🔀 MultiAgentController: Failed to parse LLM response as JSON: {e}")
                print(f"🔀 MultiAgentController: Raw response: '{response}'")
                return None
                
        except Exception as e:
            return None
    

