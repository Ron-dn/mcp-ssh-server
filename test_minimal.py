#!/usr/bin/env python3

import asyncio
import json
from mcp.server import Server, InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, ListToolsResult, ServerCapabilities, ToolsCapability

# Create minimal server
server = Server("test-server")

@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(
        tools=[
            Tool(
                name="test_tool",
                description="A test tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Test input"
                        }
                    },
                    "required": ["input"]
                }
            )
        ]
    )

async def main():
    """Run the test server."""
    try:
        init_options = InitializationOptions(
            server_name="test-server",
            server_version="1.0.0",
            capabilities=ServerCapabilities(
                tools=ToolsCapability(listChanged=False)
            )
        )
        
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, init_options)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 