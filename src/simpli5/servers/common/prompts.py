import json
from typing import Dict, Any, List
from .base import BasePrompt, PromptResult

class HelpPrompt(BasePrompt):
    """Prompt that generates help content."""
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def description(self) -> str:
        return "Generate help content for different topics"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Help topic (general, tools, resources, servers, prompts)",
                    "enum": ["general", "tools", "resources", "servers", "prompts"],
                    "default": "general"
                }
            },
            "required": []
        }
    
    @property
    def arguments(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "topic",
                "type": "string",
                "description": "Help topic",
                "enum": ["general", "tools", "resources", "servers", "prompts"],
                "default": "general",
                "required": False
            }
        ]
    
    async def generate(self, arguments: Dict[str, Any]) -> PromptResult:
        topic = arguments.get("topic", "general")
        
        help_content = {
            "general": """# Simpli5.AI Help

## Available Commands:
- `/help` - Show this help
- `/tools` - List available tools
- `/resources` - List available resources
- `/prompts` - List available prompts
- `/call <tool> <args>` - Call a tool
- `/read <resource>` - Read a resource
- `/generate <prompt> <args>` - Generate content with a prompt
- `/memory <message>` - Categorize and store memory
- `/exit` - Quit the chat interface

## Examples:
```bash
# Call a tool
/call cli:run_command {"command": "ls -la"}

# Read a resource
/read config://config

# Generate content
/generate greeting {"name": "Alice"}
```""",
            
            "tools": """# Tools Help

## Available Tools:
- `cli:run_command` - Execute system commands
- `cli:list_servers` - List configured servers
- `cli:get_config` - Get configuration info
- `cli:ping_server` - Test server connectivity

## Usage:
```bash
/call cli:run_command {"command": "ls -la"}
/call cli:list_servers {}
/call cli:get_config {"section": "servers"}
/call cli:ping_server {"server_id": "local"}
```""",
            
            "resources": """# Resources Help

## Available Resources:
- `config://config` - CLI configuration
- `system://info` - System information
- `help://help` - Help documentation

## Usage:
```bash
/read config://config
/read system://info
/read help://help
```""",
            
            "servers": """# Servers Help

## Server Management:
- List servers: `/call cli:list_servers {}`
- Ping server: `/call cli:ping_server {"server_id": "server_name"}`
- Get server config: `/call cli:get_config {"section": "servers"}`

## Server Types:
- **CLI Server**: Local command execution and system tools
- **Telegram Server**: Telegram bot functionality
- **Example Server**: Example tools and resources

## Configuration:
Servers are configured in `config/mcp_servers.yml`""",
            
            "prompts": """# Prompts Help

## Available Prompts:
- `help` - Generate help content
- `greeting` - Generate greeting messages
- `command_suggestion` - Suggest CLI commands

## Usage:
```bash
/generate help {"topic": "tools"}
/generate greeting {"name": "Alice", "style": "formal"}
/generate command_suggestion {"intent": "run a command"}
```"""
        }
        
        return PromptResult(help_content.get(topic, help_content["general"]))

class GreetingPrompt(BasePrompt):
    """Prompt that generates greeting messages."""
    
    @property
    def name(self) -> str:
        return "greeting"
    
    @property
    def description(self) -> str:
        return "Generate a personalized greeting message"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name to greet"
                },
                "time_of_day": {
                    "type": "string",
                    "description": "Time of day (morning, afternoon, evening, night)",
                    "enum": ["morning", "afternoon", "evening", "night"],
                    "default": "day"
                },
                "style": {
                    "type": "string",
                    "description": "Greeting style (formal, casual, friendly)",
                    "enum": ["formal", "casual", "friendly"],
                    "default": "friendly"
                }
            },
            "required": ["name"]
        }
    
    @property
    def arguments(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "name",
                "type": "string",
                "description": "Name to greet",
                "required": True
            },
            {
                "name": "time_of_day",
                "type": "string",
                "description": "Time of day (morning, afternoon, evening, night)",
                "enum": ["morning", "afternoon", "evening", "night"],
                "default": "day",
                "required": False
            },
            {
                "name": "style",
                "type": "string",
                "description": "Greeting style (formal, casual, friendly)",
                "enum": ["formal", "casual", "friendly"],
                "default": "friendly",
                "required": False
            }
        ]
    
    async def generate(self, arguments: Dict[str, Any]) -> PromptResult:
        name = arguments["name"]
        time_of_day = arguments.get("time_of_day", "day")
        style = arguments.get("style", "friendly")
        
        greetings = {
            "morning": {
                "formal": f"Good morning, {name}. I hope you're having a pleasant start to your day.",
                "casual": f"Hey {name}! Good morning!",
                "friendly": f"Good morning, {name}! 🌅 How are you doing today?"
            },
            "afternoon": {
                "formal": f"Good afternoon, {name}. I trust your day is proceeding well.",
                "casual": f"Hey {name}! Afternoon!",
                "friendly": f"Good afternoon, {name}! ☀️ How's your day going?"
            },
            "evening": {
                "formal": f"Good evening, {name}. I hope your day has been productive.",
                "casual": f"Hey {name}! Evening!",
                "friendly": f"Good evening, {name}! 🌆 How was your day?"
            },
            "night": {
                "formal": f"Good evening, {name}. I hope you're winding down for the day.",
                "casual": f"Hey {name}! Night!",
                "friendly": f"Good evening, {name}! 🌙 Ready to wrap up the day?"
            }
        }
        
        greeting = greetings.get(time_of_day, greetings["afternoon"])[style]
        
        return PromptResult(greeting)

class CommandSuggestionPrompt(BasePrompt):
    """Prompt that suggests CLI commands based on user intent."""
    
    @property
    def name(self) -> str:
        return "command_suggestion"
    
    @property
    def description(self) -> str:
        return "Suggest CLI commands based on user intent or description"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "What you want to accomplish"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context or constraints"
                }
            },
            "required": ["intent"]
        }
    
    @property
    def arguments(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "intent",
                "type": "string",
                "description": "What you want to accomplish",
                "required": True
            },
            {
                "name": "context",
                "type": "string",
                "description": "Additional context or constraints",
                "required": False
            }
        ]
    
    async def generate(self, arguments: Dict[str, Any]) -> PromptResult:
        intent = arguments["intent"].lower()
        context = arguments.get("context", "")
        
        suggestions = []
        
        # Server management
        if any(word in intent for word in ["server", "connect", "list", "add", "remove"]):
            suggestions.extend([
                "/list-servers - List all configured servers",
                "/add-server <id> <name> <url> <description> - Add a new server",
                "/remove-server <id> - Remove a server",
                "/call ping_server {\"server_id\": \"<server_id>\"} - Test server connectivity"
            ])
        
        # Tools
        if any(word in intent for word in ["tool", "execute", "run", "call", "function"]):
            suggestions.extend([
                "/tools - List all available tools",
                "/call <tool_name> <arguments> - Execute a specific tool",
                "/call list_servers {} - List configured servers",
                "/call get_config {\"section\": \"all\"} - Get configuration info"
            ])
        
        # Resources
        if any(word in intent for word in ["read", "file", "resource", "data", "config"]):
            suggestions.extend([
                "/resources - List all available resources",
                "/read config://config - Read CLI configuration",
                "/read system://info - Get system information",
                "/read help://help - Get help documentation"
            ])
        
        # System commands
        if any(word in intent for word in ["command", "system", "shell", "terminal"]):
            suggestions.extend([
                "/call run_command {\"command\": \"<your_command>\"} - Run system command",
                "/call run_command {\"command\": \"ls -la\", \"timeout\": 30} - List files with timeout"
            ])
        
        # Help
        if any(word in intent for word in ["help", "guide", "assist", "support"]):
            suggestions.extend([
                "/help - Show general help",
                "/generate help {\"topic\": \"tools\"} - Get tools help",
                "/generate help {\"topic\": \"resources\"} - Get resources help",
                "/generate help {\"topic\": \"servers\"} - Get servers help"
            ])
        
        if not suggestions:
            suggestions = [
                "/help - Show general help",
                "/tools - List available tools",
                "/resources - List available resources",
                "/list-servers - List configured servers"
            ]
        
        result = f"Based on your intent: '{intent}'\n\nSuggested commands:\n" + "\n".join(suggestions)
        
        if context:
            result += f"\n\nContext: {context}"
        
        return PromptResult(result) 