"""
Conditional Agent - Chooses different step paths based on conditions.
"""

from typing import Dict, Any, List, Union, Callable
from ...core.agents import Agent
from ...core.steps import AgenticStep, AgenticStepResult
from ...models import AgentResponse


class ConditionalAgent(Agent):
    """Agent that chooses different step paths based on conditions."""
    
    def __init__(self, name: str, mcp_servers: List[str], description: str):
        super().__init__(name, mcp_servers, description)
        self.step_paths = {}  # Dictionary of condition -> step lists
        self.default_path = []  # Default path if no conditions match
        self.execution_history = []
    
    def add_path(self, condition: str, steps: List[AgenticStep], description: str = ""):
        """
        Add a step path for a specific condition.
        
        Args:
            condition: The condition that triggers this path
            steps: List of steps to execute for this condition
            description: Description of what this path does
        """
        self.step_paths[condition] = {
            "steps": steps,
            "description": description
        }
        print(f"🔄 {self.name}: Added path for condition '{condition}' with {len(steps)} steps")
    
    def set_default_path(self, steps: List[AgenticStep], description: str = ""):
        """Set the default path when no conditions match."""
        self.default_path = {
            "steps": steps,
            "description": description
        }
        print(f"🔄 {self.name}: Set default path with {len(steps)} steps")
    
    async def handle(self, user_message: str, context: Dict[str, Any]) -> Union[AgentResponse, Dict[str, Any]]:
        """
        Choose and execute the appropriate step path based on conditions.
        
        Args:
            user_message: User's message
            context: Execution context
            
        Returns:
            Response from the executed path
        """
        print(f"🔄 {self.name}: Starting conditional execution")
        
        try:
            # Determine which path to take
            chosen_path = await self._choose_path(user_message, context)
            
            if not chosen_path:
                return AgentResponse(
                    status="error",
                    message="No suitable path found for the request"
                )
            
            print(f"🔄 {self.name}: Chosen path: {chosen_path['description']} with {len(chosen_path['steps'])} steps")
            
            # Execute the chosen path
            return await self._execute_path(chosen_path, user_message, context)
            
        except Exception as e:
            print(f"🔄 {self.name}: Error during conditional execution: {str(e)}")
            return AgentResponse(
                status="error",
                message=f"Conditional execution failed: {str(e)}"
            )
    
    async def _choose_path(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Choose which path to execute based on conditions.
        
        Args:
            user_message: User's message
            context: Execution context
            
        Returns:
            Dictionary containing the chosen path information
        """
        # For now, use a simple condition matching
        # In the future, this could use LLM to make intelligent decisions
        
        # Check each condition
        for condition, path_info in self.step_paths.items():
            if self._condition_matches(condition, user_message, context):
                return path_info
        
        # Return default path if no conditions match
        if self.default_path:
            return self.default_path
        
        return None
    
    def _condition_matches(self, condition: str, user_message: str, context: Dict[str, Any]) -> bool:
        """
        Check if a condition matches the current inputs.
        
        Args:
            condition: The condition to check
            user_message: User's message
            context: Execution context
            
        Returns:
            True if condition matches, False otherwise
        """
        # Simple keyword-based condition matching
        # In the future, this could be more sophisticated (LLM-based, regex, etc.)
        
        user_message_lower = user_message.lower()
        
        if condition.lower() in user_message_lower:
            return True
        
        # Check for common patterns
        if condition == "store_job" and any(word in user_message_lower for word in ["save", "store", "add"]):
            return True
        
        if condition == "find_jobs" and any(word in user_message_lower for word in ["find", "search", "get", "show"]):
            return True
        
        if condition == "apply_job" and any(word in user_message_lower for word in ["apply", "application", "submit"]):
            return True
        
        return False
    
    async def _execute_path(self, path_info: Dict[str, Any], user_message: str, context: Dict[str, Any]) -> AgentResponse:
        """
        Execute a specific step path.
        
        Args:
            path_info: Information about the path to execute
            user_message: User's message
            context: Execution context
            
        Returns:
            Response from the executed path
        """
        steps = path_info["steps"]
        current_inputs = {"user_message": user_message}
        
        print(f"🔄 {self.name}: Executing path with {len(steps)} steps")
        
        try:
            # Execute each step in the path
            for i, step in enumerate(steps):
                print(f"🔄 {self.name}: Executing step {i+1}/{len(steps)}: {step.name}")
                
                # Execute step
                step_result = await step.execute(current_inputs, context)
                
                # Record execution
                self.execution_history.append({
                    "step_name": step.name,
                    "path_description": path_info["description"],
                    "step_number": i + 1,
                    "inputs": current_inputs.copy(),
                    "result": step_result.result,
                    "timestamp": "now"
                })
                
                # Check for errors
                if step_result.result.get("error"):
                    print(f"🔄 {self.name}: Step {step.name} failed with error: {step_result.result['error']}")
                    return AgentResponse(
                        status="error",
                        message=f"Step '{step.name}' failed: {step_result.result['error']}"
                    )
                
                # Update inputs for next step
                current_inputs.update(step_result.result)
                print(f"🔄 {self.name}: Step {step.name} completed successfully")
            
            # Return final response
            print(f"🔄 {self.name}: Path completed successfully")
            return AgentResponse(
                status="success",
                message=current_inputs.get("final_response", "Task completed successfully"),
                intent=current_inputs.get("intent", "unknown")
            )
            
        except Exception as e:
            print(f"🔄 {self.name}: Error during path execution: {str(e)}")
            return AgentResponse(
                status="error",
                message=f"Path execution failed: {str(e)}"
            )
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history of all paths."""
        return self.execution_history
    
    def get_path_info(self) -> Dict[str, Any]:
        """Get information about all available paths."""
        return {
            "agent_name": self.name,
            "orchestration_type": "Conditional",
            "paths": {
                condition: {
                    "description": path_info["description"],
                    "steps": [
                        {
                            "name": step.name,
                            "description": step.description
                        }
                        for step in path_info["steps"]
                    ],
                    "total_steps": len(path_info["steps"])
                }
                for condition, path_info in self.step_paths.items()
            },
            "default_path": {
                "description": self.default_path.get("description", "No default path"),
                "steps": [
                    {
                        "name": step.name,
                        "description": step.description
                    }
                    for step in self.default_path.get("steps", [])
                ],
                "total_steps": len(self.default_path.get("steps", []))
            } if self.default_path else None
        }
