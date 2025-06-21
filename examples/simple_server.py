#!/usr/bin/env python3
"""
Simple MCP Server Example

This example demonstrates how to create an MCP server using the Simpli5 framework.
Run this server and then test it with your CLI client.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from simpli5.servers.fastmcp_server import Simpli5MCPServer
from simpli5.servers.examples import (
    CalculatorTool, 
    EchoTool, 
    SystemInfoResource, 
    FileResource,
    GreetingPrompt
)

def main():
    # Create the server
    server = Simpli5MCPServer("Simpli5 Example Server")
    
    # Add tools
    server.add_tool(CalculatorTool())
    server.add_tool(EchoTool())
    
    # Add resources
    server.add_resource(SystemInfoResource())
    server.add_resource(FileResource("examples/simple_server.py"))
    
    # Add prompts
    server.add_prompt(GreetingPrompt())
    
    # Print server info
    info = server.get_server_info()
    print(f"Starting {info['name']}")
    print(f"Tools: {info['tools']}")
    print(f"Resources: {info['resources']}")
    print(f"Prompts: {info['prompts']}")
    print("\nServer is running...")
    
    # Run the server
    server.run(transport="streamable-http")

if __name__ == "__main__":
    main() 