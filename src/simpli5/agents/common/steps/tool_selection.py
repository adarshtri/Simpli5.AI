"""
Tool selection and execution step for all agents.
This step analyzes the user's intent, selects appropriate tools, and executes them.
"""

from typing import Dict, Any
from ...core.steps import AgenticStep, AgenticStepResult
from ...core.messages import SystemMessage, Message
from simpli5.providers.mcp.multi import MultiServerProvider


class ToolSelectionAndExecutionStep(AgenticStep):
    """Generic step for selecting and executing appropriate tools based on available inputs and capabilities."""
    
    def __init__(self, agent_specific_context: Dict[str, str]):
        super().__init__(
            name="ToolSelectionAndExecution",
            description="Selects and executes appropriate tools based on message and available capabilities",
            agent_context=agent_specific_context
        )
        self.agent_specific_context = agent_specific_context
    
    def get_prompt(self, inputs: Message, context: Dict[str, Any]) -> str:
        user_message = inputs.message
        agent_name = self.agent_specific_context.get("agent_name", "Unknown Agent")
        agent_description = self.agent_specific_context.get("agent_description", "No description available")
        
        # Get available tools from MultiServerProvider
        mcp_provider = context.get("mcp_provider")
        available_tools = mcp_provider.list_all_tools()
        
        # Build tools description
        tools_description = ""
        if available_tools:
            tools_description = "\nAvailable Tools:\n"
            for tool_name, server_id, tool_info in available_tools:
                tool_description = tool_info.description
                tools_description += f"- Tool Name: {tool_name}\n- Tool Description: {tool_description}\n- Tool InputSchema: {tool_info.inputSchema}\n"
        else:
            tools_description = "\nNo tools available."
        
        # Extract user_id from context if available (commonly needed for job-related tools)
        user_id = context.get("user_id", "unknown")
        
        return f"""

IMPORTANT: 
- USE ORIGINAL TOOL NAMES and DON'T CHANGE THEM.
- KEEP TOOL PARAMETER NAME AND TYPE CONSISTENT WITH THE TOOL INPUTSCHEMA DEFINITION WHEN GENEATING TOOL PARAMETERS.
You are part of the {agent_name} agent.

Agent Description: {agent_description}

Message: "{user_message}"

User ID: {user_id}

{tools_description}

Your task is to select the most appropriate tools to accomplish what the user wants. Consider:

1. **Tool Sequence**: In what order should tools be executed?
2. **Tool Parameters**: What parameters might be needed for each tool? Each tool should have it's own entry for it's respective parameters. Tool parameters should be a mapping of tool name to a dictionary of tool parameters.
   - If a tool requires user_id, use the User ID provided above
   - For other parameters, infer them from the user message

Select only the tools that are necessary and appropriate for the user's request. If no tools are necessary, return an empty list.
"""
    
    async def execute(self, inputs: Message, context: Dict[str, Any]) -> AgenticStepResult:
        # Get LLM to select tools
        llm_provider = context.get("llm_provider")
        if not llm_provider:
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message={
                    "error": "LLM provider not available",
                    "selected_tools": [],
                    "executed_tools": [],
                    "results": [],
                    "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent")
                })
            )
        
        # Get MultiServerProvider for tool listing and execution
        mcp_provider = context.get("mcp_provider")
        if not mcp_provider or not isinstance(mcp_provider, MultiServerProvider):
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message={
                    "error": "MultiServerProvider not available in context",
                    "selected_tools": [],
                    "executed_tools": [],
                    "results": [],
                    "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent")
                })
            )
        
        try:
            prompt = self.get_prompt(inputs, context)
            
            # Define the required JSON fields and their descriptions
            required_fields = {
                "selected_tools": "List of tool names that should be executed. The order of the list is the order of execution of tools.",
                "tool_parameters": "Dictionary mapping tool names to their required parameters. For every tool in selected_tools, provide the respective tool's parameters.",
            }
            
            # Use the JSON-enforced method to get structured response from LLM
            json_response = llm_provider.generate_json_response(prompt, required_fields)
            
            # Extract tool information from the LLM response
            if isinstance(json_response, SystemMessage):
                tool_data = json_response.message
            else:
                tool_data = json_response
            
            selected_tools = tool_data.get("selected_tools", [])
            tool_parameters = tool_data.get("tool_parameters", {})
            
            if not selected_tools:
                return AgenticStepResult(
                    step_name=self.name,
                    result=SystemMessage(message={
                        "message": "No tools selected for execution",
                        "selected_tools": [],
                        "executed_tools": [],
                        "results": [],
                        "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent")
                    })
                )
            
            # Execute the selected tools
            executed_tools = []
            execution_results = []
            errors = []
            
            for tool_name in selected_tools:
                try:
                    # Get parameters for this tool
                    tool_args = tool_parameters.get(tool_name, {})
                    
                    # Execute the tool
                    result = await mcp_provider.call_tool(tool_name, tool_args)
                    
                    executed_tools.append(tool_name)
                    execution_results.append({
                        "tool_name": tool_name,
                        "status": "success",
                        "result": result,
                        "parameters": tool_args
                    })
                    
                except Exception as e:
                    errors.append(f"Failed to execute tool '{tool_name}': {str(e)}")
                    execution_results.append({
                        "tool_name": tool_name,
                        "status": "failed",
                        "error": str(e),
                        "parameters": tool_parameters.get(tool_name, {})
                    })
            
            # Prepare the final result combining selection and execution
            result_data = {
                "selected_tools": selected_tools,
                "tool_parameters": tool_parameters,
                "executed_tools": executed_tools,
                "total_tools": len(selected_tools),
                "successful_executions": len(executed_tools),
                "failed_executions": len(errors),
                "execution_results": execution_results,
                "errors": errors,
                "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent"),
                "agent_description": self.agent_specific_context.get("agent_description", "No description available"),
                "user_message": inputs.message,
                "reasoning": f"Tool selection and execution based on {self.agent_specific_context.get('agent_name', 'Unknown')} agent capabilities and user request",
                "execution_summary": f"Executed {len(executed_tools)} out of {len(selected_tools)} tools successfully"
            }
            
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message=result_data)
            )
            
        except Exception as e:
            return AgenticStepResult(
                step_name=self.name,
                result=SystemMessage(message={
                    "error": f"Failed to select and execute tools: {str(e)}",
                    "selected_tools": [],
                    "executed_tools": [],
                    "results": [],
                    "agent_name": self.agent_specific_context.get("agent_name", "Unknown Agent")
                })
            )
