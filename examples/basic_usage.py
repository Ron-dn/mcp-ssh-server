#!/usr/bin/env python3
"""
Basic usage example for MCP SSH Server.

This example demonstrates how to use the MCP SSH server for common tasks
like connecting to a server, executing commands, and managing files.
"""

import asyncio
import json
from mcp.client.stdio import stdio_client
from mcp.types import CallToolRequest


async def basic_ssh_example():
    """Basic SSH operations example."""
    
    # Connect to MCP SSH server
    async with stdio_client() as (read, write):
        # Initialize the client
        result = await read()
        print("Connected to MCP SSH Server")
        
        # Example 1: Connect to SSH server
        print("\n=== Example 1: SSH Connection ===")
        connect_request = CallToolRequest(
            method="tools/call",
            params={
                "name": "mcp_ssh_connect",
                "arguments": {
                    "host": "192.168.1.100",
                    "username": "admin",
                    "password": "your_password"
                }
            }
        )
        
        # Note: In real usage, this would be handled by the MCP client
        print("Connect request:", json.dumps(connect_request.dict(), indent=2))
        
        # Example connection response
        connection_id = "ssh_abc123_192.168.1.100_admin"
        print(f"Connection established: {connection_id}")
        
        # Example 2: Execute simple command
        print("\n=== Example 2: Execute Command ===")
        execute_request = {
            "name": "mcp_ssh_execute",
            "arguments": {
                "connection_id": connection_id,
                "command": "ls -la /home",
                "show_output": True
            }
        }
        print("Execute request:", json.dumps(execute_request, indent=2))
        
        # Example 3: Upload file
        print("\n=== Example 3: Upload File ===")
        upload_request = {
            "name": "mcp_ssh_upload",
            "arguments": {
                "connection_id": connection_id,
                "local_path": "./config.txt",
                "remote_path": "/tmp/config.txt"
            }
        }
        print("Upload request:", json.dumps(upload_request, indent=2))
        
        # Example 4: List directory
        print("\n=== Example 4: List Directory ===")
        list_request = {
            "name": "mcp_ssh_list_directory",
            "arguments": {
                "connection_id": connection_id,
                "remote_path": "/tmp",
                "detailed": True
            }
        }
        print("List request:", json.dumps(list_request, indent=2))
        
        # Example 5: Get system info
        print("\n=== Example 5: System Information ===")
        sysinfo_request = {
            "name": "mcp_ssh_get_system_info",
            "arguments": {
                "connection_id": connection_id
            }
        }
        print("System info request:", json.dumps(sysinfo_request, indent=2))
        
        # Example 6: Disconnect
        print("\n=== Example 6: Disconnect ===")
        disconnect_request = {
            "name": "mcp_ssh_disconnect",
            "arguments": {
                "connection_id": connection_id
            }
        }
        print("Disconnect request:", json.dumps(disconnect_request, indent=2))


def direct_usage_example():
    """Direct usage example without MCP client."""
    print("=== Direct Usage Example ===")
    print("""
# This is how you would use the MCP SSH server directly:

from mcp_ssh_server import MCPSSHServer

# Create server instance
server = MCPSSHServer()

# Connect to SSH host
connection_id = server.ssh_manager.create_connection(
    host="192.168.1.100",
    username="admin",
    password="your_password"
)

# Execute command
result = server.ssh_manager.execute_command(
    connection_id=connection_id,
    command="ls -la"
)
print("Command output:", result.stdout)

# Upload file
server.ssh_manager.upload_file(
    connection_id=connection_id,
    local_path="./file.txt",
    remote_path="/tmp/file.txt"
)

# Download file
server.ssh_manager.download_file(
    connection_id=connection_id,
    remote_path="/tmp/file.txt",
    local_path="./downloaded_file.txt"
)

# Disconnect
server.ssh_manager.disconnect(connection_id)
""")


if __name__ == "__main__":
    print("MCP SSH Server - Basic Usage Examples")
    print("=" * 50)
    
    # Show direct usage
    direct_usage_example()
    
    # Show MCP client usage
    print("\n" + "=" * 50)
    asyncio.run(basic_ssh_example()) 