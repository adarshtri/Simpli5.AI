from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from .base import BaseTool, BaseResource, BasePrompt

class Simpli5MCPServer:
    """Simpli5 MCP Server using FastMCP."""
    
    def __init__(self, name: str = "Simpli5 Server"):
        self.name = name
        self.mcp = FastMCP(name)
        self.tools: List[BaseTool] = []
        self.resources: List[BaseResource] = []
        self.prompts: List[BasePrompt] = []
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to the server."""
        self.tools.append(tool)
        
        # Register with FastMCP
        @self.mcp.tool()
        async def dynamic_tool(**kwargs):
            result = await tool.execute(kwargs)
            return result.content
    
        # Set the tool metadata
        dynamic_tool.__name__ = tool.name
        dynamic_tool.__doc__ = tool.description
    
    def add_resource(self, resource: BaseResource):
        """Add a resource to the server."""
        self.resources.append(resource)
        
        # Register with FastMCP
        @self.mcp.resource(resource.uri)
        async def dynamic_resource():
            result = await resource.read()
            return result.content
    
    def add_prompt(self, prompt: BasePrompt):
        """Add a prompt to the server."""
        self.prompts.append(prompt)
        
        # Register with FastMCP
        @self.mcp.prompt()
        async def dynamic_prompt(**kwargs):
            return await prompt.generate(kwargs)
    
    def run(self, transport: str = "stdio", **kwargs):
        """Run the server with specified transport."""
        self.mcp.run(transport=transport, **kwargs)
    
    def get_server_info(self) -> dict:
        """Get server information."""
        return {
            "name": self.name,
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "prompts_count": len(self.prompts),
            "tools": [tool.name for tool in self.tools],
            "resources": [resource.uri for resource in self.resources],
            "prompts": [prompt.name for prompt in self.prompts]
        } 