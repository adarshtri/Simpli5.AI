import click
import asyncio
import json
from simpli5.providers.mcp_client import MCPClientProvider
from mcp.types import TextContent

@click.group()
def main():
    """Simpli5 CLI entry point."""
    pass

@main.command()
@click.option('--server', required=True, help='MCP server URL (e.g., http://localhost:8000/mcp)')
def list_tools(server):
    """List available tools from the MCP server."""
    async def _list():
        provider = MCPClientProvider(server)
        tools = await provider.list_tools()
        if not tools:
            click.echo("No tools found on the server.")
            return
        for i, tool in enumerate(tools):
            click.echo(f"----------- Tool {i+1} -----------")
            click.echo(f"- {tool.name}: {tool.description}")
            click.echo("================================================")
            click.echo(f"- Input Schema: {tool.inputSchema}")
            click.echo(f"--------------------------------\n")
    asyncio.run(_list())

@main.command()
@click.option('--server', required=True, help='MCP server URL (e.g., http://localhost:8000/mcp)')
@click.option('--tool', required=True, help='Name of the tool to call')
@click.option('--args', required=True, help='Tool arguments as JSON string (e.g., \'{"key": "value"}\')')
def call_tool(server, tool, args):
    """Call a tool on the MCP server with the given arguments."""
    async def _call():
        try:
            arguments = json.loads(args)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON in --args parameter")
            return
        
        provider = MCPClientProvider(server)
        result = await provider.call_tool(tool, arguments)
        for content in result.content:
            if content.type == 'text':
                click.echo(json.loads(content.text))
            else:
                click.echo(content)
    asyncio.run(_call())

@main.command()
@click.option('--server', required=True, help='MCP server URL (e.g., http://localhost:8000/mcp)')
def list_resources(server):
    """List available resources from the MCP server."""
    async def _list():
        provider = MCPClientProvider(server)
        resources = await provider.list_resources()
        if not resources:
            click.echo("No resources found on the server.")
            return
        for i, resource in enumerate(resources):
            click.echo(f"----------- Resource {i+1} -----------")
            click.echo(f"- URI: {resource.uri}")
            click.echo(f"- Name: {resource.name}")
            if resource.description:
                click.echo(f"- Description: {resource.description}")
            click.echo(f"--------------------------------\n")
    asyncio.run(_list())

@main.command()
@click.option('--server', required=True, help='MCP server URL (e.g., http://localhost:8000/mcp)')
@click.option('--uri', required=True, help='URI of the resource to read')
def read_resource(server, uri):
    """Read content from a specific resource on the MCP server."""
    async def _read():
        provider = MCPClientProvider(server)
        content, mime_type = await provider.read_resource(uri)
        click.echo(f"MIME Type: {mime_type}")
        click.echo("Content:")
        click.echo(content)
    asyncio.run(_read())

if __name__ == "__main__":
    main() 