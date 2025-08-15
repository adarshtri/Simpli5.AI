import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

class MCPClientProvider:
    def __init__(self, server_url: str):
        self.server_url = server_url

    async def list_tools(self):
        async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                return tools_response.tools

    async def call_tool(self, tool_name: str, arguments: dict):
        async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return result

    async def list_resources(self):
        async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                resources_response = await session.list_resources()
                return resources_response.resources

    async def read_resource(self, uri: str):
        async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                content, mime_type = await session.read_resource(uri)
                return content, mime_type

    async def list_prompts(self):
        async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                prompts_response = await session.list_prompts()
                return prompts_response.prompts

    async def generate_prompt(self, prompt_name: str, arguments: dict):
        async with streamablehttp_client(self.server_url) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.get_prompt(prompt_name, arguments=arguments)
                return result