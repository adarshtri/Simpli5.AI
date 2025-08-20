"""
Sequential Agent - Executes steps in a fixed sequence.
"""

from typing import Dict, Any, List, Union
from ...core.agents import Agent
from ...core.steps import AgenticStep, AgenticStepResult
from ...models import AgentResponse


class SequentialAgent(Agent):
    """Agent that executes steps in a fixed sequence."""
    
    def __init__(self, name: str, mcp_servers: List[str], description: str, steps: List[AgenticStep]):
        super().__init__(name, mcp_servers, description)
        self.steps = steps
        self.execution_history = []
    
    async def handle(self, user_message: str, context: Dict[str, Any]) -> Union[AgentResponse, Dict[str, Any]]:
        """
        Execute steps in sequence.
        
        Args:
            user_message: User's message
            context: Execution context
            
        Returns:
            Final response from the last step
        """
        print(f"🔄 {self.name}: Starting sequential execution with {len(self.steps)} steps")
        
        # Initialize inputs for first step
        current_inputs = {"user_message": user_message}
        
        try:
            # Execute each step in sequence
            for i, step in enumerate(self.steps):
                print(f"🔄 {self.name}: Executing step {i+1}/{len(self.steps)}: {step.name}")
                
                # Execute step
                step_result = await step.execute(current_inputs, context)
                
                # Record execution
                self.execution_history.append({
                    "step_name": step.name,
                    "step_number": i + 1,
                    "inputs": current_inputs.copy(),
                    "result": step_result.result,
                    "timestamp": "now"  # Could use actual datetime
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
            print(f"🔄 {self.name}: All steps completed successfully")
            return AgentResponse(
                status="success",
                message=current_inputs.get("final_response", "Task completed successfully"),
                intent=current_inputs.get("intent", "unknown")
            )
            
        except Exception as e:
            print(f"🔄 {self.name}: Error during execution: {str(e)}")
            return AgentResponse(
                status="error",
                message=f"Sequential execution failed: {str(e)}"
            )
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Get the execution history of all steps."""
        return self.execution_history
    
    def get_step_info(self) -> Dict[str, Any]:
        """Get information about the steps this agent uses."""
        return {
            "agent_name": self.name,
            "orchestration_type": "Sequential",
            "steps": [
                {
                    "name": step.name,
                    "description": step.description,
                    "order": i + 1
                }
                for i, step in enumerate(self.steps)
            ],
            "total_steps": len(self.steps)
        }
    
    def add_step(self, step: AgenticStep):
        """Add a new step to the sequence."""
        self.steps.append(step)
        print(f"🔄 {self.name}: Added step '{step.name}' to sequence")
    
    def remove_step(self, step_name: str):
        """Remove a step from the sequence."""
        self.steps = [step for step in self.steps if step.name != step_name]
        print(f"🔄 {self.name}: Removed step '{step_name}' from sequence")
