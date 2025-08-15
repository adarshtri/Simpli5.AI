#!/usr/bin/env python3
"""
Calculator MCP Server - A simple STDIO-based MCP server for mathematical operations.

This server demonstrates how to build MCP servers using STDIO transport,
eliminating the need for port management and providing better process isolation.
"""

import logging
import sys
from mcp.server.fastmcp import FastMCP

# Set up logging to stderr (not stdout!) to avoid interfering with MCP protocol
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,  # Important: log to stderr, not stdout
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("calculator-server")

# Create FastMCP server
mcp = FastMCP("Calculator")

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    result = a + b
    logger.info(f"Addition: {a} + {b} = {result}")
    return result

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract second number from first."""
    result = a - b
    print(f"Subtraction: {a} - {b} = {result}")
    logger.info(f"Subtraction: {a} - {b} = {result}")
    return result

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    result = a * b
    logger.info(f"Multiplication: {a} × {b} = {result}")
    return result

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide first number by second."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    result = a / b
    logger.info(f"Division: {a} ÷ {b} = {result}")
    return result

@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    result = base ** exponent
    logger.info(f"Power: {base}^{exponent} = {result}")
    return result

def main():
    """Main entry point for Calculator MCP server."""
    logger.info("Starting Calculator MCP Server via STDIO...")
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main() 