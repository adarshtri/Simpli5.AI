import click
import asyncio
import json
import sys
import os
from contextlib import redirect_stderr
from dotenv import load_dotenv
from simpli5.providers.mcp.client import MCPClientProvider
from simpli5.providers.mcp.multi import MultiServerProvider
from mcp.types import TextContent
from simpli5.config import ConfigManager
from simpli5.chat import ChatInterface
from simpli5.webhook import TelegramWebhook

# Load environment variables from a .env file
load_dotenv()

class FilteredStderr:
    """Custom stderr that filters out CancelledError tracebacks."""
    
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = []
        self.suppress_next = False
    
    def write(self, text):
        # Check if this looks like a CancelledError traceback
        if "CancelledError" in text or "asyncio.exceptions.CancelledError" in text:
            self.suppress_next = True
            return
        
        # If we're suppressing, check if this is part of the traceback
        if self.suppress_next:
            if "Traceback" in text or "File " in text or "  File " in text:
                return
            if text.strip() == "":
                return
            # If we reach here, it's not part of the traceback, so stop suppressing
            self.suppress_next = False
        
        # Write to original stderr
        self.original_stderr.write(text)
    
    def flush(self):
        self.original_stderr.flush()

@click.group()
def main():
    """Simpli5.AI - Extensible AI CLI with MCP server support."""
    pass

@main.command()
@click.option('--servers', help='Comma-separated list of server IDs (e.g., local,example)')
@click.option('--log-level', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], case_sensitive=False),
              default='WARNING',
              help='Set logging level for MCP servers')
def chat(servers, log_level):
    """Start interactive chat with MCP servers."""
    async def _chat():
        server_ids = None
        if servers:
            server_ids = [s.strip() for s in servers.split(',')]
        
        chat_interface = ChatInterface(server_ids, log_level=log_level.upper())
        try:
            await chat_interface.start()
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            print(f"\nError in chat interface: {e}")
        finally:
            await chat_interface.stop()
    
    # Use filtered stderr to suppress only CancelledError tracebacks
    original_stderr = sys.stderr
    try:
        sys.stderr = FilteredStderr(original_stderr)
        asyncio.run(_chat())
    finally:
        sys.stderr = original_stderr

@main.command()
def version():
    """Show Simpli5.AI version."""
    click.echo("Simpli5.AI v0.1.0")

@main.command()
def help():
    """Show help information."""
    click.echo("""
Simpli5.AI - Extensible AI CLI with MCP server support.

Commands:
  chat     Start interactive chat with MCP servers
  webhook  Start Telegram webhook server
  version  Show version information
  help     Show this help message

Examples:
  simpli5 chat                    # Start chat with all configured servers
  simpli5 chat --servers local,math  # Start chat with specific servers
  simpli5 chat --log-level INFO   # Start chat with verbose logging
  simpli5 webhook --telegram-token TOKEN --webhook-url URL  # Start webhook server

For more information, visit: https://github.com/your-username/simpli5-ai
""")

@main.command()
@click.option('--telegram-token', envvar='TELEGRAM_BOT_TOKEN', required=True,
              help='Telegram bot token')
@click.option('--webhook-url', required=True,
              help='Public URL where webhook will receive updates (e.g., https://your-domain.com/webhook)')
@click.option('--firebase-credentials', envvar='GOOGLE_APPLICATION_CREDENTIALS',
              help='Path to Firebase service account JSON file (optional - messages will be printed to console if not provided)')
@click.option('--collection-name', default='telegram_messages',
              help='Firestore collection name for storing messages')
@click.option('--host', default='0.0.0.0', help='Host to bind the server to')
@click.option('--port', default=8000, help='Port to bind the server to')
def webhook(telegram_token, webhook_url, firebase_credentials, collection_name, host, port):
    """Start Telegram webhook server to receive and store messages in Firestore."""
    async def _webhook():
        try:
            # Create webhook instance
            webhook = TelegramWebhook(
                telegram_token=telegram_token,
                webhook_url=webhook_url,
                firebase_credentials_path=firebase_credentials,
                collection_name=collection_name
            )
            
            # Setup webhook with Telegram
            await webhook.setup_webhook()
            
            click.echo(f"Webhook server starting on {host}:{port}")
            click.echo(f"Webhook URL: {webhook_url}")
            click.echo(f"Firestore collection: {collection_name}")
            click.echo("Press Ctrl+C to stop the server")
            
            # Run the server
            webhook.run(host=host, port=port)
            
        except KeyboardInterrupt:
            click.echo("\nShutting down webhook server...")
            # Remove webhook
            await webhook.remove_webhook()
        except Exception as e:
            click.echo(f"Error in webhook server: {e}")
    
    asyncio.run(_webhook())

if __name__ == "__main__":
    main() 