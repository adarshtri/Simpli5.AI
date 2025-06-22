import asyncio
import json
import signal
import sys
from typing import List, Optional
from .providers.mcp.multi import MultiServerProvider
from .providers.llm.multi import MultiLLMProvider
from .config import ConfigManager
from .servers.cli_server import CLIMCPServer

class ChatInterface:
    """Interactive chat interface for MCP servers."""
    
    def __init__(self, server_ids: Optional[List[str]] = None, cli_server_port: int = 8001, log_level: str = "WARNING"):
        self.config = ConfigManager()
        if server_ids is None:
            # Use all configured servers
            server_ids = [server_id for server_id, _ in self.config.list_servers()]
        
        self.server_ids = server_ids
        self.cli_server_port = cli_server_port
        self.log_level = log_level
        self.multi_provider: Optional[MultiServerProvider] = None
        self.cli_server: Optional[CLIMCPServer] = None
        self.running = False
        self.llm_manager: Optional[MultiLLMProvider] = None
        self.is_routing = False # Add a flag to prevent re-entrant calls
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        if self.running:
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            self.running = False
    
    async def start(self):
        """Start the chat interface."""
        try:
            # Initialize the LLM provider manager
            print("Initializing LLM providers...")
            self.llm_manager = MultiLLMProvider()

            # Start CLI MCP server
            print("Starting CLI MCP server...")
            self.cli_server = CLIMCPServer(host="localhost", port=self.cli_server_port, log_level=self.log_level)
            await self.cli_server.start()
            print(f"CLI MCP server started on localhost:{self.cli_server_port}")
            
            # Add CLI server to the list of servers to connect to, ensuring no duplicates
            server_ids_to_connect = self.server_ids.copy()
            if "cli" not in server_ids_to_connect:
                server_ids_to_connect.append("cli")
            
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
        
        # Stop CLI MCP server
        if self.cli_server and self.cli_server.is_running:
            await self.cli_server.stop()
        
        print("Chat interface stopped.")
    
    async def _chat_loop(self):
        """The main loop for handling user input."""
        while self.running:
            user_input = await self._prompt_for_input()

            if not user_input:
                continue

            if user_input.startswith('/'):
                await self._handle_command(user_input)
            elif self.llm_manager and self.llm_manager.has_provider() and not self.is_routing:
                await self._process_natural_language_input(user_input)
            elif self.is_routing:
                # This case is for the second pass, for a pure chat response
                response = self.llm_manager.generate_response(user_input)
                print(f"\n🤖 AI:\n{response}")
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
        print("-" * 40)
        for tool_name, server_id, tool_info in tools:
            print(f"• {tool_name}")
            if hasattr(tool_info, 'description') and tool_info.description:
                print(f"  {tool_info.description}")
    
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

    async def _process_natural_language_input(self, user_input: str):
        """
        Uses the LLM to determine if the user's input is a tool call or a chat message.
        """
        print("\n🤔 Thinking...")
        self.is_routing = True # Set flag to indicate we're in the routing phase

        # 1. Get the list of available tools in a structured format
        tools_list = []
        if self.multi_provider:
            for tool_name, (_, tool_info) in self.multi_provider.tools.items():
                tools_list.append({
                    "name": tool_name,
                    "description": tool_info.description,
                    "input_schema": getattr(tool_info, 'input_schema', {}),
                })

        # 2. Create the routing system prompt
        system_prompt = f"""
You are a helpful AI assistant that functions as a routing engine. Your task is to analyze the user's request and determine if it can be fulfilled by one of the available tools, or if it's a general conversational query.

Here are the available tools:
```json
{json.dumps(tools_list, indent=2)}
```

Based on the user's request, you must respond with a JSON object indicating the user's intent. Your response MUST be one of two formats:

1. If the request can be handled by a tool, respond with:
   {{"intent": "tool_call", "call": {{"tool_name": "<tool_name>", "arguments": {{<arguments_json>}}}}}}
   Please use user input and matched tool definition to create the arguments.
   
2. If the request is a general conversation (e.g., a greeting, or a question the tools cannot answer), respond with:
   {{"intent": "chat"}}

Do not add any other text to your response. Only provide the single JSON object.
"""
        # 3. Combine with user input and get the LLM's decision
        full_prompt = f"{system_prompt}\n\nUser request: \"{user_input}\""
        decision_str = self.llm_manager.generate_response(full_prompt)

        # 4. Parse the decision
        try:
            decision = json.loads(decision_str)
            intent = decision.get("intent")

            if intent == "tool_call":
                call_details = decision.get("call", {})
                tool_name = call_details.get("tool_name")
                arguments = json.dumps(call_details.get("arguments", {}))
                command_str = f"/call {tool_name} {arguments}"
                print(f"✅ Understood! Running command: {command_str}")
                await self._handle_command(command_str)
            elif intent == "chat":
                # If it's a chat, re-run the input for a conversational response
                await self._chat_loop_entry(user_input)
            else:
                print(f"🤖 AI:\nI'm not sure how to handle that. The LLM returned an unknown intent: '{intent}'")
                print(f"Raw response: {decision_str}")

        except json.JSONDecodeError:
            print(f"🤖 AI:\nI received an unexpected response. I'll treat this as a conversation.")
            # If the response isn't valid JSON, treat it as a conversational response.
            print(decision_str)
        finally:
            self.is_routing = False # Reset the flag

    async def _chat_loop_entry(self, user_input: str):
        """A re-entry point for the chat loop to avoid recursion issues."""
        if user_input.startswith('/'):
            await self._handle_command(user_input)
        elif self.llm_manager and self.llm_manager.has_provider():
            # This is the second pass, for a pure chat response
            response = self.llm_manager.generate_response(user_input)
            print(f"\n🤖 AI:\n{response}")
        else:
            # Fallback if somehow called without an LLM
            print("\nLLM provider not available.") 