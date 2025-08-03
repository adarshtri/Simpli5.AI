#!/usr/bin/env python3
"""
Example script for running the Telegram MCP server.

This script demonstrates how to start the Telegram MCP server
and test the memory categorizer tool.

Usage:
    python examples/telegram_mcp_server_example.py
"""

import asyncio
from simpli5.servers.telegram import TelegramMCPServer

async def main():
    """Run the Telegram MCP server."""
    
    print("Starting Telegram MCP Server...")
    print("Server will be available at: http://localhost:8002")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Create and start the server
        server = TelegramMCPServer(host="localhost", port=8002)
        
        # Start the server
        await server.start()
        
        # Keep the server running
        try:
            while server.is_running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        
    except KeyboardInterrupt:
        print("\nShutting down Telegram MCP server...")
    except Exception as e:
        print(f"Error running server: {e}")
    finally:
        if server:
            await server.stop()

if __name__ == "__main__":
    asyncio.run(main()) 