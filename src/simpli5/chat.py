import asyncio
import json
import signal
import sys
from typing import List, Optional
from .providers.mcp.multi import MultiServerProvider
from .providers.llm.multi import MultiLLMProvider
from .config import ConfigManager


class ChatInterface:
    """Interactive chat interface for MCP servers."""
    
    def __init__(self, server_ids: Optional[List[str]] = None, log_level: str = "WARNING"):
        self.config = ConfigManager()
        if server_ids is None:
            # Use all configured servers
            server_ids = [server_id for server_id, _ in self.config.list_servers()]
        
        self.server_ids = server_ids
        self.log_level = log_level
        self.multi_provider: Optional[MultiServerProvider] = None
        self.running = False
        self.llm_manager: Optional[MultiLLMProvider] = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        if self.running:
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            self.running = False
            # Note: We can't call async methods from signal handlers
            # The main loop will handle the cleanup
    
    async def start(self):
        """Start the chat interface."""
        try:
            # Initialize the LLM provider manager
            print("Initializing LLM providers...")
            self.llm_manager = MultiLLMProvider()

            # Connect to configured servers
            server_ids_to_connect = self.server_ids.copy()
            
            if not server_ids_to_connect:
                print("No servers configured. Please check your config/mcp_servers.yml file.")
                return
            
            print(f"Connecting to servers: {', '.join(server_ids_to_connect)}")
            self.multi_provider = MultiServerProvider(server_ids_to_connect)
            await self.multi_provider.connect()
            
            print("\n" + "="*50)
            print("Simpli5 Chat Interface")
            print("="*50)
            print("Type a message to chat with the AI, or /help for commands.")
            print("Type /exit to quit")
            print("="*50)
            
            self.running = True
            await self._chat_loop()
            
        except Exception as e:
            print(f"Error starting chat interface: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the chat interface and cleanup resources."""
        print("\nShutting down chat interface...")
        self.running = False
        
        # Cleanup MCP connections
        if self.multi_provider:
            try:
                await self.multi_provider.disconnect_all()
            except Exception as e:
                print(f"Warning: Error disconnecting from MCP servers: {e}")
        
        print("Chat interface stopped.")
    
    async def _chat_loop(self):
        """The main loop for handling user input."""
        while self.running:
            user_input = await self._prompt_for_input()

            if not user_input:
                continue

            if user_input.startswith('/'):
                await self._handle_command(user_input)
            elif self.llm_manager and self.llm_manager.has_provider():
                await self._process_natural_language_input(user_input)
            else:
                print("\nLLM provider is not configured. Please check your 'config/llm_providers.yml' and ensure API keys are set.")
                print("You can still use commands like /help, /tools, etc.")
        
        # Ensure cleanup happens
        try:
            await self.stop()
        except Exception as e:
            # Suppress shutdown-related errors
            if not any(keyword in str(e).lower() for keyword in ['cancelled', 'shutdown', 'closed']):
                print(f"Error during shutdown: {e}")
            else:
                print("Chat interface stopped.")
        finally:
            # Ensure we always mark as not running
            self.running = False
    
    async def _prompt_for_input(self) -> str:
        """Prompt for and read user input asynchronously."""
        return input("\n> ").strip()
    
    async def _handle_command(self, command: str):
        """Handle chat commands."""
        parts = command.split(' ', 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/help':
            self._show_help()
        elif cmd == '/tools':
            self._show_tools()
        elif cmd == '/resources':
            self._show_resources()
        elif cmd == '/prompts':
            self._show_prompts()
        elif cmd == '/call':
            await self._call_tool(args)
        elif cmd == '/read':
            await self._read_resource(args)
        elif cmd == '/generate':
            await self._generate_prompt(args)
        elif cmd == '/memory':
            await self._handle_memory_command(args)
        elif cmd == '/exit':
            self.running = False
        else:
            print(f"Unknown command: {cmd}. Type /help for available commands.")
    
    def _show_help(self):
        """Show available commands."""
        print("\nAvailable Commands:")
        print("  /help      - Show this help")
        print("  /tools     - List all available tools")
        print("  /resources - List all available resources")
        print("  /prompts   - List all available prompts")
        print("  /call <tool_name> <args> - Call a tool (e.g., /call local:calculator '{\"operation\": \"add\", \"a\": 5, \"b\": 3}')")
        print("  /read <uri> - Read a resource (e.g., /read system://info)")
        print("  /generate <prompt_name> <args> - Generate a prompt")
        print("  /memory <message> - Categorize and store memory (e.g., /memory \"I'm a software engineer\")")
        print("  /exit      - Exit the chat")
    
    def _show_tools(self):
        """Show all available tools."""
        if not self.multi_provider:
            print("Not connected to any servers.")
            return
        
        tools = self.multi_provider.list_all_tools()
        if not tools:
            print("No tools available.")
            return
        
        print(f"\nAvailable Tools ({len(tools)} total):")
        
        for tool_name, server_id, tool_info in sorted(tools):
            print("-" * 40)
            print(f"• {tool_name}")
            print(f"  (from: {server_id})")

            if hasattr(tool_info, 'description') and tool_info.description:
                print(f"\n  {tool_info.description}")
            
            if hasattr(tool_info, 'input_schema') and tool_info.input_schema:
                schema = tool_info.input_schema
                properties = schema.get("properties", {})
                
                if properties:
                    print("\n  Arguments:")
                    required = schema.get("required", [])
                    for name, details in properties.items():
                        arg_type = details.get("type", "any")
                        req_str = " (required)" if name in required else ""
                        desc = details.get("description", "No description.")
                        
                        default_val = details.get('default')
                        default_str = f" (default: {json.dumps(default_val)})" if default_val is not None else ""

                        print(f"    - {name} [{arg_type}]{req_str}{default_str}")
                        print(f"      {desc}")
            print()
    
    def _show_resources(self):
        """Show all available resources."""
        if not self.multi_provider:
            print("Not connected to any servers.")
            return
        
        resources = self.multi_provider.list_all_resources()
        if not resources:
            print("No resources available.")
            return
        
        print(f"\nAvailable Resources ({len(resources)} total):")
        print("-" * 40)
        for uri, server_id, resource_info in resources:
            print(f"• {uri}")
            if hasattr(resource_info, 'name') and resource_info.name:
                print(f"  {resource_info.name}")
            print(f"  Server: {server_id}")
            print()
    
    def _show_prompts(self):
        """Show all available prompts."""
        if not self.multi_provider:
            print("Not connected to any servers.")
            return
        
        prompts = self.multi_provider.list_all_prompts()
        if not prompts:
            print("No prompts available.")
            return
        
        print(f"\nAvailable Prompts ({len(prompts)} total):")
        print("-" * 40)
        for prompt_name, server_id, prompt_info in prompts:
            print(f"• {prompt_name}")
            if hasattr(prompt_info, 'description') and prompt_info.description:
                print(f"  {prompt_info.description}")
    
    async def _call_tool(self, args: str):
        """Call a tool with arguments."""
        if not self.multi_provider:
            print("Not connected to any servers.")
            return
        
        parts = args.split(' ', 1)
        if len(parts) < 2:
            print("Usage: /call <tool_name> <json_arguments>")
            return
        
        tool_name = parts[0]
        try:
            arguments = json.loads(parts[1])
        except json.JSONDecodeError:
            print("Error: Invalid JSON in arguments")
            return
        
        try:
            # Check if tool exists
            if tool_name not in self.multi_provider.tools:
                print(f"❌ Tool '{tool_name}' not found.")
                print("Available tools:")
                for available_tool in self.multi_provider.tools.keys():
                    print(f"  - {available_tool}")
                print("\n💡 Tip: Make sure the server with this tool is running.")
                if "local:" in tool_name:
                    print("   For local tools, start the calculator server with: python scripts/stdio_mcp_example.py")
                return
            
            result = await self.multi_provider.call_tool(tool_name, arguments)
            print(f"\nTool Result:")
            for content in result.content:
                if hasattr(content, 'type') and content.type == 'text':
                    print(content.text)
                else:
                    print(str(content))
        except Exception as e:
            print(f"Error calling tool: {e}")
    
    async def _read_resource(self, uri: str):
        """Read a resource."""
        if not self.multi_provider:
            print("Not connected to any servers.")
            return
        
        if not uri:
            print("Usage: /read <resource_uri>")
            return
        
        try:
            content, mime_type = await self.multi_provider.read_resource(uri)
            print(f"\nResource Content (MIME: {mime_type}):")
            print("-" * 40)
            print(content)
        except Exception as e:
            print(f"Error reading resource: {e}")
    
    async def _generate_prompt(self, args: str):
        """Generate a prompt."""
        if not self.multi_provider:
            print("Not connected to any servers.")
            return
        
        parts = args.split(' ', 1)
        if len(parts) < 2:
            print("Usage: /generate <prompt_name> <json_arguments>")
            return
        
        prompt_name = parts[0]
        try:
            arguments = json.loads(parts[1])
        except json.JSONDecodeError:
            print("Error: Invalid JSON in arguments")
            return
        
        try:
            result = await self.multi_provider.generate_prompt(prompt_name, arguments)
            print(f"\nGenerated Prompt:")
            print("-" * 40)
            for message in result.messages:
                print(f"[{message.role.upper()}]")
                for content in message.content:
                    content_type, content_value = content
                    if content_type == 'text':
                        print(content_value)
                    else:
                        print(f"({content_type} content)")
        except Exception as e:
            print(f"Error generating prompt: {e}")

    async def _handle_memory_command(self, message: str):
        """Handle the /memory command to categorize and store memory using the new prompt."""
        if not message.strip():
            print("Usage: /memory <message>")
            print("Example: /memory \"I'm a software engineer\"")
            return
        
        try:
            print(f"\n🧠 Processing memory: \"{message}\"")
            
            # Use the new memory categorization prompt
            result = await self.multi_provider.generate_prompt(
        
                {"user_message": message}
            )
            
            if result and result.messages:
                # Get the prompt content
                prompt_content = ""
                for message in result.messages:
                    for content in message.content:
                        content_type, content_value = content
                        if content_type == 'text':
                            # Clean up the content - remove JSON wrapper if present
                            if content_value.startswith('{') and '"content"' in content_value:
                                try:
                                    import json
                                    parsed = json.loads(content_value)
                                    prompt_content = parsed.get('content', content_value)
                                except:
                                    prompt_content = content_value
                            else:
                                prompt_content = content_value
                
                print(f"📋 Generated prompt:")
                print("-" * 40)
                print(prompt_content)
                print("-" * 40)
                
                # Send the prompt to LLM for categorization
                if self.llm_manager and self.llm_manager.has_provider():
                    print(f"🤖 Sending to LLM for categorization...")
                    llm_response = self.llm_manager.generate_response(prompt_content)
                    
                    # Clean up the response
                    category = llm_response.strip().lower()
                    valid_categories = ["profile", "preference", "context", "not_applicable"]
                    
                    if category in valid_categories:
                        print(f"✅ Memory categorized as: {category.upper()}")
                        print(f"📝 Original message: \"{message}\"")
                        print(f"🏷️  Category: {category}")
                        
                        if category == "not_applicable":
                            print(f"ℹ️  Message categorized as '{category}' - not stored (not applicable)")
                        else:
                            print(f"💾 Would store in: users/{{user_id}}/memories/{category}/")
                    else:
                        print(f"⚠️  LLM returned invalid category: '{category}'")
                        print(f"🔍 Valid categories: {', '.join(valid_categories)}")
                else:
                    print(f"❌ LLM provider not available. Please check your 'config/llm_providers.yml' and ensure API keys are set.")
                    print(f"📝 Message: \"{message}\"")
                    print(f"🔍 Next step: Send this prompt to an LLM for categorization")
                
            else:
                print(f"❌ Failed to generate memory categorization prompt")
                
        except Exception as e:
            print(f"❌ Error processing memory: {e}")

    async def _process_natural_language_input(self, user_input: str):
        """
        First tries to route the request through available MCP tools,
        then falls back to direct LLM response if no tools can handle it.
        """
        print("\n🤔 Thinking...")
        
        # First, try to route through available tools
        if self.multi_provider and self.llm_manager and self.llm_manager.has_provider():
            await self._route_through_tools(user_input)
        else:
            # Fallback to direct LLM response
            await self._handle_direct_llm_response(user_input)



    async def _route_through_tools(self, user_input: str):
        """
        Route user input through available MCP tools using LLM to determine
        which tools to call and with what arguments.
        """
        try:
            # Create a routing prompt that includes available tools
            available_tools = self.multi_provider.list_all_tools()
            
            if not available_tools:
                print("No tools available, falling back to direct LLM response.")
                await self._handle_direct_llm_response(user_input)
                return
            
            # Build detailed tool information including schemas
            tool_details = []
            for tool_name, server_id, tool_info in available_tools:
                tool_detail = f"- {tool_name}: {tool_info.description}"
                
                # Add input schema if available
                if hasattr(tool_info, 'inputSchema') and tool_info.inputSchema:
                    schema = tool_info.inputSchema
                    
                    # Handle both dict and object schemas
                    if isinstance(schema, dict) and 'properties' in schema:
                        # Schema is a dictionary
                        required = schema.get('required', [])
                        properties = schema['properties']
                        
                        tool_detail += f"\n  Input schema:"
                        for prop_name, prop_info in properties.items():
                            prop_type = prop_info.get('type', 'unknown')
                            prop_desc = prop_info.get('description', '')
                            required_mark = " (required)" if prop_name in required else " (optional)"
                            tool_detail += f"\n    - {prop_name}: {prop_type}{required_mark}"
                            if prop_desc:
                                tool_detail += f" - {prop_desc}"
                    elif hasattr(schema, 'properties'):
                        # Schema is an object with attributes
                        required = getattr(schema, 'required', [])
                        properties = schema.properties
                        
                        tool_detail += f"\n  Input schema:"
                        for prop_name, prop_info in properties.items():
                            prop_type = getattr(prop_info, 'type', 'unknown')
                            prop_desc = getattr(prop_info, 'description', '')
                            required_mark = " (required)" if prop_name in required else " (optional)"
                            tool_detail += f"\n    - {prop_name}: {prop_type}{required_mark}"
                            if prop_desc:
                                tool_detail += f" - {prop_desc}"
                
                tool_details.append(tool_detail)
            
            routing_prompt = f"""You have access to the following tools with their input schemas:

{chr(10).join(tool_details)}

User request: "{user_input}"

Based on the user's request and the tool schemas above, determine which tool(s) to call and with what arguments.
IMPORTANT: Only use the exact argument names and types specified in the tool schemas.

If the request can be handled by available tools, respond with a JSON object like:
{{
    "tool_calls": [
        {{
            "tool_name": "exact_tool_name_from_list",
            "arguments": {{"exact_arg_name": "value"}}
        }}
    ]
}}

If no tools can handle the request, respond with:
{{
    "tool_calls": [],
    "fallback": "explanation of why no tools can handle this"
}}

Respond with only the JSON, no other text."""

            # Get LLM routing decision
            routing_response = self.llm_manager.generate_response(routing_prompt)
            
            try:
                import json
                routing_data = json.loads(routing_response.strip())
                
                if routing_data.get("tool_calls"):
                    # Execute tool calls
                    print("🔧 Executing tools...")
                    for tool_call in routing_data["tool_calls"]:
                        tool_name = tool_call["tool_name"]
                        arguments = tool_call["arguments"]
                        
                        print(f"📞 Calling tool: {tool_name}")
                        print(f"📝 Arguments: {arguments}")
                        
                        # Validate tool arguments against schema
                        if not await self._validate_tool_arguments(tool_name, arguments):
                            print(f"❌ Tool arguments validation failed for {tool_name}")
                            continue
                        
                        try:
                            result = await self.multi_provider.call_tool(tool_name, arguments)
                            print(f"✅ Tool result: {result}")
                        except Exception as e:
                            print(f"❌ Tool call failed: {e}")
                    
                    # Provide a brief summary of the tool execution
                    print("\n✅ Tool execution completed. You can ask another question or request.")
                else:
                    # No tools can handle this, fall back to direct LLM
                    if "fallback" in routing_data:
                        print(f"ℹ️  {routing_data['fallback']}")
                    print("🔄 Falling back to direct LLM response...")
                    await self._handle_direct_llm_response(user_input)
                    
            except json.JSONDecodeError:
                print("❌ Failed to parse LLM routing response, falling back to direct response...")
                await self._handle_direct_llm_response(user_input)
                
        except Exception as e:
            print(f"❌ Error in tool routing: {e}")
            print("🔄 Falling back to direct LLM response...")
            await self._handle_direct_llm_response(user_input)

    async def _handle_direct_llm_response(self, user_input: str):
        """Handle user input with direct LLM response."""
        if self.llm_manager and self.llm_manager.has_provider():
            response = self.llm_manager.generate_response(user_input)
            print(f"\n🤖 AI:\n{response}")
        else:
            print("\nLLM provider is not configured. Please check your 'config/llm_providers.yml' and ensure API keys are set.")

    async def _validate_tool_arguments(self, tool_name: str, arguments: dict) -> bool:
        """
        Validate that the provided arguments match the tool's input schema.
        Returns True if valid, False otherwise.
        """
        try:
            # Find the tool in our available tools
            available_tools = self.multi_provider.list_all_tools()
            tool_info = None
            
            for name, server_id, info in available_tools:
                if name == tool_name:
                    tool_info = info
                    break
            
            if not tool_info:
                print(f"❌ Tool '{tool_name}' not found in available tools")
                return False
            
            # Check if tool has input schema
            if not hasattr(tool_info, 'inputSchema') or not tool_info.inputSchema:
                print(f"⚠️  Tool '{tool_name}' has no input schema, proceeding without validation")
                return True
            
            schema = tool_info.inputSchema
            
            # Handle both dict and object schemas
            if isinstance(schema, dict):
                if 'properties' not in schema:
                    print(f"⚠️  Tool '{tool_name}' has incomplete schema (no properties), proceeding without validation")
                    return True
                properties = schema['properties']
                required = schema.get('required', [])
            elif hasattr(schema, 'properties'):
                properties = schema.properties
                required = getattr(schema, 'required', [])
            else:
                print(f"⚠️  Tool '{tool_name}' has incomplete schema, proceeding without validation")
                return True
            
            # Check required arguments
            for req_arg in required:
                if req_arg not in arguments:
                    print(f"❌ Missing required argument '{req_arg}' for tool '{tool_name}'")
                    return False
            
            # Check argument types (basic validation)
            for arg_name, arg_value in arguments.items():
                if arg_name in properties:
                    prop_info = properties[arg_name]
                    
                    # Handle both dict and object property info
                    if isinstance(prop_info, dict):
                        expected_type = prop_info.get('type')
                    else:
                        expected_type = getattr(prop_info, 'type', None)
                    
                    if expected_type == 'string' and not isinstance(arg_value, str):
                        print(f"❌ Argument '{arg_name}' should be string, got {type(arg_value).__name__}")
                        return False
                    elif expected_type == 'number' and not isinstance(arg_value, (int, float)):
                        print(f"❌ Argument '{arg_name}' should be number, got {type(arg_value).__name__}")
                        return False
                    elif expected_type == 'boolean' and not isinstance(arg_value, bool):
                        print(f"❌ Argument '{arg_name}' should be boolean, got {type(arg_value).__name__}")
                        return False
            
            print(f"✅ Tool arguments validation passed for '{tool_name}'")
            return True
            
        except Exception as e:
            print(f"⚠️  Error during tool validation: {e}, proceeding anyway")
            return True 