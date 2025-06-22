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
  version  Show version information
  help     Show this help message

Examples:
  simpli5 chat                    # Start chat with all configured servers
  simpli5 chat --servers local,math  # Start chat with specific servers
  simpli5 chat --log-level INFO   # Start chat with verbose logging

For more information, visit: https://github.com/your-username/simpli5-ai
""")

if __name__ == "__main__":
    main() 