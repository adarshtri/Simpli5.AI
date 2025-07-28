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

**Simpli5.AI** is an extensible, configuration-driven AI CLI that connects to both **Large Language Models (LLMs)** and **Model Context Protocol (MCP)** servers. It provides a unified, interactive chat interface for seamless interaction with multiple AI capabilities.

## ✨ Features

- **Multi-LLM Support**: Connect to multiple LLM providers (like Groq, OpenAI, etc.) through a simple config file.
- **Multi-Server MCP Support**: Interact with tools, resources, and prompts from multiple MCP servers simultaneously.
- **Interactive Chat Interface**: A single command-line interface for both conversational AI and MCP commands.
- **Telegram Webhook**: Receive and store Telegram messages in Firestore for AI analysis.
- **Secure API Key Management**: Loads API keys securely from a `.env` file.
- **Extensible Architecture**: Clean, provider-based architecture makes it easy to add new LLMs or MCP functionalities.
- **Configurable Logging**: Control log verbosity for a clean user experience or detailed debugging.

## 🚀 Quick Start

### 1. Installation

Clone the repository and set up your environment.

```bash
# Clone the project
git clone https://github.com/your-username/simpli5-ai.git
cd simpli5-ai

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the project and its dependencies
pip install -e .
```

### 2. API Key Setup

Simpli5.AI loads API keys from a `.env` file for security.

1.  **Create a `.env` file** in the project's root directory. You can copy the example file:
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file** and add your secret API keys:
    ```bash
    # .env
    GROQ_API_KEY="your-groq-api-key-here"
    # OPENAI_API_KEY="your-openai-api-key-here"
    ```

### 3. Running the Chat

Start the interactive chat interface with a single command.

```bash
simpli5 chat
```

Now you can chat with your configured LLM or use `/` commands to interact with MCP servers!

## 📖 Usage Guide

### Chat Interface

-   **Conversational AI**: Type any message to chat with the default configured LLM.
-   **MCP Commands**: Use slash commands to interact with MCP servers.
    -   `/help`: Show available commands.
    -   `/tools`: List all tools from connected MCP servers.
    -   `/call <server:tool> <args>`: Call a specific tool.
    -   `/exit`: Quit the chat interface.

### Telegram Webhook

Simpli5.AI includes a webhook server that can receive Telegram messages and store them in Firestore for AI analysis.

#### Setup

1. **Create a Telegram Bot**: Use [@BotFather](https://t.me/botfather) to create a bot and get the token.

2. **Set up Firebase**: 
   - Create a Firebase project
   - Download the service account JSON file
   - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable

3. **Configure Environment Variables**:
   ```bash
   # .env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   ```

4. **Start the Webhook Server**:
   ```bash
   # Using CLI command
   simpli5 webhook --telegram-token YOUR_TOKEN --webhook-url https://your-domain.com/webhook
   
   # Or using the example script
   python examples/telegram_webhook_example.py
   ```

#### Features

- **Message Storage**: All incoming Telegram messages are stored in Firestore
- **Health Check**: Available at `/health` endpoint
- **Webhook Management**: Automatically sets up and removes webhooks
- **Error Handling**: Robust error handling and logging

#### Testing with ngrok

For local development, you can use ngrok to create a public HTTPS URL:

```bash
# Install ngrok
npm install -g ngrok

# Start your webhook server
simpli5 webhook --telegram-token YOUR_TOKEN --webhook-url https://your-ngrok-url.ngrok.io/webhook

# In another terminal, expose your local server
ngrok http 8000
```

#### Complete Setup Guide

For detailed setup instructions, see [SETUP_WEBHOOK.md](SETUP_WEBHOOK.md).

## 🔧 Configuration

Simpli5.AI is fully configurable through YAML files in the `config/` directory.

### LLM Providers (`config/llm_providers.yml`)

Configure which LLMs you want to use. The first enabled provider becomes the default for chat.

```yaml
# config/llm_providers.yml
llm_providers:
  groq:
    provider: 'groq'
    api_key_env: 'GROQ_API_KEY'
    default_model: 'llama3-8b-8192'
    enabled: true
  
  openai:
    provider: 'openai'
    api_key_env: 'OPENAI_API_KEY'
    default_model: 'gpt-4o'
    enabled: false # Disabled by default
```

### MCP Servers (`config/mcp_servers.yml`)

Add any MCP-compatible servers to access their tools and resources.

```yaml
# config/mcp_servers.yml
servers:
  local:
    name: "Local Development Server"
    url: "http://localhost:8000/mcp"
    enabled: true
```

## 🛠️ Development

### Project Structure

The project is organized for scalability and clarity.

```
Simpli5.AI/
├── config/
│   ├── llm_providers.yml      # LLM provider configurations
│   └── mcp_servers.yml        # MCP server configurations
├── src/
│   └── simpli5/
│       ├── cli.py             # Main CLI entry point
│       ├── chat.py            # Interactive chat interface
│       ├── providers/
│       │   ├── llm/           # LLM provider implementations
│       │   └── mcp/           # MCP provider implementations
│       └── ...
├── .env.example               # Example environment variables
├── pyproject.toml
└── README.md
```

### Adding a New LLM Provider

1.  **Create the Provider Class**: Add a new file in `src/simpli5/providers/llm/` that inherits from `BaseLLMProvider`.
2.  **Update `multi.py`**: Register your new provider class in `src/simpli5/providers/llm/multi.py`.
3.  **Configure It**: Add its configuration to `config/llm_providers.yml`.
4.  **Set the API Key**: Add the required API key to your `.env` file.

## 🤝 Contributing

Contributions are welcome! Please follow the standard fork-and-pull-request workflow.

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