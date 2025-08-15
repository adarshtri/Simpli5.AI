"""
Job Agent for handling job-related operations.
"""

from .core.agents import Agent
from typing import Dict, Any, Optional, Union
import re
import json
import traceback
from mcp.types import Tool
from .models import LLMResponse, AgentResponse, LLMResponseParser


class JobAgent(Agent):
    """Agent specialized in job-related operations."""
    
    def __init__(self):
        """Initialize the Job Agent with access to job_agent MCP server."""
        super().__init__("JobAgent", ["job_agent"], "Handles job-related messages, applications, career discussions, and job search activities")
    
    async def handle(self, user_message: str, context: Dict[str, Any]) -> Union[AgentResponse, Dict[str, Any]]:
        """
        Handle job-related user messages using LLM-driven tool selection.
        
        Args:
            user_message: The user's message
            context: Additional context (e.g., user_id, metadata)
            
        Returns:
            Dict with response and status
        """
        print(f"💼 JobAgent: Received message: '{user_message}'")
        print(f"💼 JobAgent: Context: {context}")
        
        try:
            # Get available tools from MCP server
            available_tools = self.get_available_tools()
            print(f"💼 JobAgent: Available tools: {available_tools}")
            
            # Use LLM to determine intent, select tools, and format response
            result = await self._llm_driven_handling(user_message, context, available_tools)
            print(f"💼 JobAgent: LLM result: {result}")
            
            return result
                
        except Exception as e:
            print(f"💼 JobAgent: Error occurred: {str(e)}")
            print(f"💼 JobAgent: Error traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error processing job-related message: {str(e)}"
            }
    
    async def _llm_driven_handling(self, user_message: str, context: Dict[str, Any], available_tools: list) -> Union[AgentResponse, Dict[str, Any]]:
        """
        Use LLM to determine intent, select tools, and handle the user request.
        
        Args:
            user_message: The user's message
            context: Additional context
            available_tools: List of available MCP tools
            
        Returns:
            Dict with response and status
        """
        if not self.llm_provider or not self.llm_provider.has_provider():
            return {
                "status": "error",
                "message": "LLM provider not available. Cannot process job-related requests."
            }
        
        try:
            # Build comprehensive prompt for LLM
            prompt = self._build_llm_prompt(user_message, context, available_tools)
            
            print(f"💼 JobAgent: LLM Prompt:")
            print(f"   {prompt}")
            
            # Get LLM response
            print(f"💼 JobAgent: Calling LLM...")
            response = self.llm_provider.generate_response(prompt)
            print(f"💼 JobAgent: LLM Response: '{response}'")
            
            # Parse LLM response
            parsed_response = self._parse_llm_response(response)
            if not parsed_response:
                return {
                    "status": "error",
                    "message": "Could not understand LLM response. Please try rephrasing your request."
                }
            
            # Execute tool calls if any
            if parsed_response.tool_calls:
                tool_results = await self._execute_tool_calls(parsed_response.tool_calls, context)
                print(f"💼 JobAgent: Tool execution results: {tool_results}")
                
                # Let LLM format final response with tool results
                final_response = await self._format_final_response(user_message, parsed_response, tool_results, context)
                return final_response
            
            # No tool calls needed, return LLM response directly
            return AgentResponse(
                status="success",
                message=parsed_response.response,
                intent=parsed_response.intent
            )
            
        except Exception as e:
            print(f"💼 JobAgent: LLM-driven handling failed: {e}")
            print(f"💼 JobAgent: Error traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error in LLM processing: {str(e)}"
            }
    
    def _build_llm_prompt(self, user_message: str, context: Dict[str, Any], available_tools: list) -> str:
        """
        Build comprehensive prompt for LLM including available tools and context.
        
        Args:
            user_message: The user's message
            context: Additional context
            available_tools: List of available MCP tools
            
        Returns:
            Formatted prompt string
        """
        user_id = context.get("user_id", "unknown")
        
        # Format available tools for LLM
        tools_description = ""
        for tool in available_tools:
            tool_name = tool[0]
            server_id = tool[1]
            tool_info: Tool = tool[2]
            tools_description += f"- {tool_name}: {tool_info.description}\n"
            if tool_info.inputSchema:
                tools_description += f"  Parameters: {tool_info.inputSchema}\n"
        
        prompt = f"""
You are a Job Agent that helps users manage their job search activities. You have access to the following tools:

{tools_description}

User ID: {user_id}
User Message: "{user_message}"

Your task is to:
1. Understand what the user wants to do
2. Determine if you need to call any tools
3. If tools are needed, specify which tools to call and with what parameters
4. Provide a helpful response to the user

You have full autonomy to:
- Interpret the user's intent however you see fit
- Choose the most appropriate tools for the situation
- Handle any job-related request, not just predefined categories
- Be creative in how you help users with their job search

Respond with a JSON object in this exact format:
{{
    "intent": "brief description of what user wants",
    "tool_calls": [
        {{
            "tool_name": "name_of_tool_to_call",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
    ],
    "response": "Your helpful response to the user (will be shown after tool execution)"
}}

If no tools are needed, use:
{{
    "intent": "brief description",
    "tool_calls": [],
    "response": "Your response to the user"
}}

Examples:
- User: "save this job posting from LinkedIn"
  Response: {{
    "intent": "store job for later application",
    "tool_calls": [
        {{
            "tool_name": "job_agent:store_job_message",
            "parameters": {{
                "user_id": "{user_id}",
                "original_message": "save this job posting from LinkedIn",
                "extracted_job_link": "https://linkedin.com/jobs/...",
                "company_name": "Google",
                "metadata": {{"source": "linkedin"}}
            }}
        }}
    ],
    "response": "I'll save that LinkedIn job posting for you!"
  }}

- User: "how many jobs have I saved?"
  Response: {{
    "intent": "get job statistics summary",
    "tool_calls": [
        {{
            "tool_name": "job_agent:get_user_job_stats",
            "parameters": {{
                "user_id": "{user_id}"
            }}
        }}
    ],
    "response": "Let me check your job statistics for you."
  }}

- User: "I'm feeling overwhelmed with my job search"
  Response: {{
    "intent": "provide emotional support and job search guidance",
    "tool_calls": [
        {{
            "tool_name": "job_agent:get_user_job_stats",
            "parameters": {{
                "user_id": "{user_id}"
            }}
        }}
    ],
    "response": "I understand job searching can be overwhelming. Let me check your current progress and help you organize your search."
  }}

IMPORTANT: 
- Use the exact tool names from the available tools list
- Tool names are in the format of "server_id:tool_name"
- Provide helpful, user-friendly responses
- If you're unsure about parameters, make reasonable assumptions based on context
- You can handle any job-related request - be creative and helpful!
- Response should have 3 fields, intent, tool_calls, and response.
- Construct suitable response for the user's message.
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Optional[LLMResponse]:
        """
        Parse LLM response using structured parser.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed LLMResponse or None if parsing fails
        """
        try:
            # Use the structured parser
            parsed_response = LLMResponseParser.parse_llm_response(response)
            
            if parsed_response:
                print(f"💼 JobAgent: Successfully parsed LLM response with intent: {parsed_response.intent}")
                return parsed_response
            else:
                print(f"💼 JobAgent: Failed to parse LLM response")
                return None
                
        except Exception as e:
            print(f"💼 JobAgent: Error parsing LLM response: {e}")
            print(f"💼 JobAgent: Raw response: {response}")
            return None
    
    async def _execute_tool_calls(self, tool_calls: list, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the specified tool calls using MCP server.
        
        Args:
            tool_calls: List of tool call specifications
            context: Additional context
            
        Returns:
            Dict with tool execution results
        """
        if not self.mcp_provider:
            return {
                "error": "MCP provider not available"
            }
        
        results = {}
        
        for i, tool_call in enumerate(tool_calls):
            tool_name = tool_call.tool_name
            parameters = tool_call.parameters
            
            print(f"💼 JobAgent: Executing tool {tool_name} with parameters {parameters}")
            
            try:
                # Execute tool via MCP
                result = await self.mcp_provider.call_tool(tool_name, parameters)
                results[f"tool_{i}_{tool_name}"] = result
                print(f"💼 JobAgent: Tool {tool_name} executed successfully: {result}")
                
            except Exception as e:
                error_msg = f"Error executing tool {tool_name}: {str(e)}"
                print(f"💼 JobAgent: Error traceback: {traceback.format_exc()}")
                print(f"💼 JobAgent: {error_msg}")
                results[f"tool_{i}_{tool_name}"] = {
                    "success": False,
                    "error": error_msg
                }
        
        return results
    
    async def _format_final_response(self, user_message: str, parsed_response: LLMResponse, tool_results: Dict[str, Any], context: Dict[str, Any]) -> AgentResponse:
        """
        Let LLM format the final response incorporating tool execution results.
        
        Args:
            user_message: Original user message
            parsed_response: Parsed LLM response
            tool_results: Results from tool execution
            context: Additional context
            
        Returns:
            Final formatted response
        """
        if not self.llm_provider or not self.llm_provider.has_provider():
            # Fallback to simple response if no LLM available
            return AgentResponse(
                status="success",
                message=parsed_response.response,
                intent=parsed_response.intent,
                tool_results=tool_results
            )
        
        try:
            # Build prompt for final response formatting
            prompt = f"""
The user asked: "{user_message}"

You initially responded: "{parsed_response.response}"

Here are the results from executing the tools you requested:
{tool_results}

Now provide a final, helpful response to the user that:
1. Acknowledges what they asked for
2. Summarizes what you did (if tools were executed)
3. Provides the information they requested in a user-friendly way
4. Suggests next steps if appropriate

Keep your response conversational and helpful. Don't mention technical details about tools or parameters.
"""
            
            final_response = self.llm_provider.generate_response(prompt)
            
            return AgentResponse(
                status="success",
                message=final_response.strip(),
                intent=parsed_response.intent,
                tool_results=tool_results
            )
            
        except Exception as e:
            print(f"💼 JobAgent: Error formatting final response: {e}")
            # Fallback to original response
            return AgentResponse(
                status="success",
                message=parsed_response.response,
                intent=parsed_response.intent,
                tool_results=tool_results
            )
    
    def _extract_job_link(self, message: str) -> str:
        """
        Extract job link from message using simple regex.
        
        Args:
            message: The user message
            
        Returns:
            Extracted job link or empty string if none found
        """
        # Simple URL extraction - in practice, you might want more sophisticated parsing
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, message)
        
        if urls:
            return urls[0]  # Return first URL found
        
        # If no URL found, return empty string
        return ""

    