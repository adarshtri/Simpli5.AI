# Python Project

This is a Python project template with a basic structure and common development tools.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Development

- Run tests: `pytest`
- Format code: `black .`
- Lint code: `flake8`

## Project Structure

```
.
├── README.md
├── requirements.txt
├── src/
│   └── main.py
└── tests/
    └── __init__.py
```

# Simpli5.AI

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Simpli5.AI** is an extensible AI CLI tool that supports multiple MCP (Model Context Protocol) servers, providing a unified interface for tools, resources, and prompts. Built with modern Python and designed for developers transitioning from software engineering to AI engineering.

## ✨ Features

- **Multi-Server MCP Support**: Connect to multiple MCP servers simultaneously
- **Interactive Chat Interface**: Command-line chat with AI capabilities
- **Host Tools & Resources**: Built-in CLI operations exposed as MCP tools
- **Extensible Architecture**: Easy to add new tools, resources, and prompts
- **Clean Logging**: Configurable verbosity levels for professional use
- **Graceful Shutdown**: Proper cleanup and signal handling

## 🚀 Quick Start

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/simpli5-ai.git
   cd simpli5-ai
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install in development mode**:
   ```bash
   pip install -e .
   ```

### Basic Usage

1. **Start the interactive chat**:
   ```bash
   simpli5 chat
   ```

2. **Connect to specific servers**:
   ```bash
   simpli5 chat --servers local,example
   ```

3. **Control logging verbosity**:
   ```bash
   simpli5 chat --log-level WARNING  # Less verbose (default)
   simpli5 chat --log-level INFO     # More verbose for debugging
   ```

## 📖 Usage Guide

### Chat Interface Commands

Once in the chat interface, you can use these commands:

- `/help` - Show available commands
- `/tools` - List all available tools
- `/call <server:tool> <args>` - Call a tool (e.g., `/call local:calculator {"operation": "add", "a": 5, "b": 3}`)
- `/read <server://resource>` - Read a resource
- `/generate <server:prompt> <args>` - Generate content from a prompt
- `/exit` - Exit the chat interface

### Server Configuration

Configure MCP servers in `config/mcp_servers.yml`:

```yaml
servers:
  local:
    name: "Local Development Server"
    url: "http://localhost:8000/mcp"
    description: "Local test server with calculator and file tools"
    enabled: true
  
  example:
    name: "Example Weather Server"
    url: "https://mcp.pipedream.net/159d4d25-8d02-444d-972f-9671d4b6e55d/openweather_api"
    description: "Weather data and forecasts"
    enabled: true
```

### Built-in Host Tools

Simpli5.AI exposes CLI operations as MCP tools:

- `list_servers` - List all configured MCP servers
- `run_command` - Execute shell commands
- `get_config` - Get current configuration
- `ping_server` - Test server connectivity

### Built-in Host Resources

- `config://config` - Current configuration
- `config://servers` - Detailed server information
- `system://info` - System information
- `help://<topic>` - Help documentation

## 🛠️ Development

### Project Structure

```
Simpli5.AI/
├── config/
│   └── mcp_servers.yml          # Server configurations
├── examples/
│   └── simple_server.py         # Example MCP server
├── src/
│   └── simpli5/
│       ├── __init__.py
│       ├── cli.py               # CLI entry point
│       ├── chat.py              # Interactive chat interface
│       ├── config.py            # Configuration management
│       ├── host/                # Built-in tools, resources, prompts
│       ├── providers/           # MCP client and multi-server support
│       └── servers/             # FastMCP server framework
├── tests/
├── pyproject.toml
└── README.md
```

### Adding Custom Tools

Create a new tool by extending `BaseTool`:

```python
from simpli5.servers.base import BaseTool, ToolResult

class MyCustomTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"
    
    @property
    def description(self) -> str:
        return "My custom tool description"
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {"type": "string"}
            },
            "required": ["input"]
        }
    
    async def execute(self, arguments: Dict[str, Any]) -> ToolResult:
        input_data = arguments["input"]
        result = f"Processed: {input_data}"
        return ToolResult(result)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=simpli5

# Run specific test file
pytest tests/test_chat.py
```

### Code Quality

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

## 🔧 Configuration

### Environment Variables

- `MCP_SERVER_PORT` - Port for CLI MCP server (default: 8001)
- `MCP_SERVER_HOST` - Host for CLI MCP server (default: localhost)

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General information (default for debugging)
- `WARNING` - Warning messages (default for production)
- `ERROR` - Error messages only
- `CRITICAL` - Critical errors only

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation for API changes
- Use type hints for all function parameters and return values

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/fastmcp/fastmcp) for MCP server functionality
- Uses [Click](https://click.palletsprojects.com/) for CLI interface
- Inspired by the need for extensible AI development tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/simpli5-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/simpli5-ai/discussions)
- **Documentation**: [Wiki](https://github.com/your-username/simpli5-ai/wiki)

---

**Made with ❤️ for the AI engineering community** 