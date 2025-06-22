from typing import List, Optional, Any, Dict, Type, Literal
from inspect import Parameter, Signature
from mcp.server.fastmcp import FastMCP
from .base import BaseTool, BaseResource, BasePrompt

# Mapping from JSON schema types to Python types
TYPE_MAP: Dict[str, Type] = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
    "object": dict,
    "array": list,
}

class FastMCPServer:
    """Simpli5 MCP Server using FastMCP."""
    
    def __init__(self, name: str = "Simpli5 Server", log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "WARNING"):
        self.name = name
        self.log_level = log_level
        self.mcp = FastMCP(name, log_level=log_level)
        self.tools: List[BaseTool] = []
        self.resources: List[BaseResource] = []
        self.prompts: List[BasePrompt] = []
    
    def add_tool(self, tool: BaseTool):
        """Add a tool to the server."""
        self.tools.append(tool)
        
        # Create a function with the correct signature for FastMCP to inspect.
        params = [
            Parameter(
                name,
                Parameter.KEYWORD_ONLY,
                annotation=TYPE_MAP.get(prop.get("type"), Any)
            )
            for name, prop in tool.input_schema.get("properties", {}).items()
        ]
        sig = Signature(params)
        
        async def tool_func(**kwargs):
            result = await tool.execute(kwargs)
            return result.content

        tool_func.__signature__ = sig
        tool_func.__name__ = tool.name
        tool_func.__doc__ = tool.description
        tool_func.__annotations__ = {p.name: p.annotation for p in sig.parameters.values()}
        
        self.mcp.tool()(tool_func)
    
    def add_resource(self, resource: BaseResource):
        """Add a resource to the server."""
        self.resources.append(resource)
        
        async def resource_func():
            result = await resource.read()
            return result.content

        resource_func.__name__ = resource.name
        resource_func.__doc__ = resource.description
        
        self.mcp.resource(resource.uri)(resource_func)
    
    def add_prompt(self, prompt: BasePrompt):
        """Add a prompt to the server."""
        self.prompts.append(prompt)
        
        params = [
            Parameter(
                arg["name"],
                Parameter.KEYWORD_ONLY,
                annotation=TYPE_MAP.get(arg.get("type", "string"), Any)
            )
            for arg in prompt.arguments
        ]
        sig = Signature(params)
        
        async def prompt_func(**kwargs):
            return await prompt.generate(kwargs)

        prompt_func.__signature__ = sig
        prompt_func.__name__ = prompt.name
        prompt_func.__doc__ = prompt.description
        prompt_func.__annotations__ = {p.name: p.annotation for p in sig.parameters.values()}

        self.mcp.prompt()(prompt_func)
    
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