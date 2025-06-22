import json
from typing import Dict, Any, List
from ..servers.base import BasePrompt, PromptResult

class HelpPrompt(BasePrompt):
    """Prompt that provides help and guidance."""
    
    @property
    def name(self) -> str:
        return "help"
    
    @property
    def description(self) -> str:
        return "Get help and guidance for CLI operations"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to get help for (tools, resources, prompts, servers, general)",
                    "enum": ["tools", "resources", "prompts", "servers", "general"],
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
                "description": "Topic to get help for (tools, resources, prompts, servers, general)",
                "enum": ["tools", "resources", "prompts", "servers", "general"],
                "default": "general",
                "required": False
            }
        ]
    
    async def generate(self, arguments: Dict[str, Any]) -> PromptResult:
        topic = arguments.get("topic", "general")
        
        help_content = {
            "general": """# Simpli5.AI CLI - General Help

Welcome to Simpli5.AI CLI! This is an extensible chat interface that connects to multiple MCP (Model Context Protocol) servers.

## Quick Start
1. Use `/tools` to see available tools
2. Use `/resources` to see available resources
3. Use `/prompts` to see available prompts
4. Use `/call <tool_name> <args>` to execute tools
5. Use `/read <resource_uri>` to read resources
6. Use `/generate <prompt_name> <args>` to use prompts

## Key Features
- **Multi-server support**: Connect to multiple MCP servers simultaneously
- **Interactive chat**: Natural conversation interface with commands
- **Tool execution**: Call tools from any connected server
- **Resource access**: Read files, configurations, and other resources
- **Prompt templates**: Use predefined prompts for common tasks

## Getting Help
- `/help` - Show this help message
- `/list-servers` - See configured servers
- Use specific help topics: `/generate help {\"topic\": \"tools\"}`""",
            
            "tools": """# Tools Help

## What are Tools?
Tools are functions that can be executed to perform specific tasks. They can come from:
- The CLI itself (host tools)
- Connected MCP servers

## Using Tools
```
/call <tool_name> <arguments>
```

## Examples
```
/call calculator_add {\"a\": 5, \"b\": 3}
/call list_servers {}
/call run_command {\"command\": \"ls -la\"}
```

## Host Tools (Built-in)
- `list_servers` - List configured MCP servers
- `run_command` - Execute system commands
- `get_config` - Get CLI configuration
- `ping_server` - Test server connectivity

## Server Tools
Tools from MCP servers are prefixed with the server name:
```
/call math:add {\"a\": 5, \"b\": 3}
/call file:read {\"path\": \"/path/to/file.txt\"}
```""",
            
            "resources": """# Resources Help

## What are Resources?
Resources are data sources that can be read, such as:
- Files on the filesystem
- Configuration data
- System information
- Network resources

## Using Resources
```
/read <resource_uri>
```

## Examples
```
/read file:///path/to/file.txt
/read config://servers
/read system://info
```

## Host Resources (Built-in)
- `config://config` - CLI configuration
- `config://servers` - Server information
- `system://info` - System information
- `help://help` - Help documentation

## Server Resources
Resources from MCP servers use their own URI schemes:
```
/read file:///path/to/file.txt
/read http://example.com/data.json
```""",
            
            "prompts": """# Prompts Help

## What are Prompts?
Prompts are templates that help you interact with the system more effectively. They provide:
- Structured input formats
- Common task templates
- Guidance for complex operations

## Using Prompts
```
/generate <prompt_name> <arguments>
```

## Examples
```
/generate help {\"topic\": \"tools\"}
/generate greeting {\"name\": \"Alice\"}
```

## Host Prompts (Built-in)
- `help` - Get help on various topics
- `greeting` - Generate a greeting message
- `command_suggestion` - Get command suggestions

## Server Prompts
Prompts from MCP servers are prefixed with the server name:
```
/generate ai:summarize {\"text\": \"Long text to summarize\"}
```""",
            
            "servers": """# Servers Help

## What are MCP Servers?
MCP (Model Context Protocol) servers provide tools, resources, and prompts that extend the CLI's capabilities.

## Managing Servers
```
/list-servers - List all configured servers
/add-server <id> <name> <url> <description> - Add a new server
/remove-server <id> - Remove a server
/enable-server <id> - Enable a server
/disable-server <id> - Disable a server
```

## Server Configuration
Servers are configured in `~/.simpli5/config.yml`:
```yaml
servers:
  math:
    name: "Math Server"
    url: "http://localhost:8000"
    description: "Mathematical operations"
    enabled: true
```

## Using Server Capabilities
Once connected, server capabilities are available with server prefixes:
- Tools: `/call server:tool_name <args>`
- Resources: `/read server://resource_uri`
- Prompts: `/generate server:prompt_name <args>`

## Testing Connectivity
Use the ping tool to test server connectivity:
```
/call ping_server {\"server_id\": \"math\"}
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
        
        result = f"Based on your intent: '{intent}'\n\nSuggested commands:\n" + "\n".join(f"- {s}" for s in suggestions)
        
        return PromptResult(result) 