"""
Main MCP SSH Server implementation.

This module provides the MCP server that exposes SSH functionality
through the Model Context Protocol interface.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence
import traceback

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .ssh_manager import SSHConnectionManager, CommandResult, FileInfo
from .exceptions import (
    SSHBaseError,
    SSHConnectionError,
    SSHAuthenticationError,
    SSHCommandError,
    SSHFileOperationError,
    SSHTunnelError,
    SSHTimeoutError,
)


class MCPSSHServer:
    """MCP SSH Server implementation."""
    
    def __init__(self):
        self.server = Server("mcp-ssh-server")
        self.ssh_manager = SSHConnectionManager()
        self.logger = logging.getLogger(__name__)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Register MCP handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            """List available SSH tools."""
            return ListToolsResult(
                tools=[
                    # Connection Management Tools
                    Tool(
                        name="mcp_ssh_connect",
                        description="Establish SSH connection to remote host",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "host": {
                                    "type": "string",
                                    "description": "Remote host IP address or hostname"
                                },
                                "username": {
                                    "type": "string",
                                    "description": "SSH username"
                                },
                                "password": {
                                    "type": "string",
                                    "description": "SSH password (optional if using key)"
                                },
                                "private_key": {
                                    "type": "string",
                                    "description": "SSH private key content (optional)"
                                },
                                "port": {
                                    "type": "integer",
                                    "default": 22,
                                    "description": "SSH port number"
                                },
                                "timeout": {
                                    "type": "number",
                                    "default": 30.0,
                                    "description": "Connection timeout in seconds"
                                }
                            },
                            "required": ["host", "username"]
                        }
                    ),
                    Tool(
                        name="mcp_ssh_disconnect",
                        description="Close SSH connection",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "Connection ID to close"
                                }
                            },
                            "required": ["connection_id"]
                        }
                    ),
                    Tool(
                        name="mcp_ssh_list_connections",
                        description="List all active SSH connections",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "random_string": {
                                    "type": "string",
                                    "description": "Dummy parameter for no-parameter tools"
                                }
                            },
                            "required": ["random_string"]
                        }
                    ),
                    Tool(
                        name="mcp_ssh_test_connection",
                        description="Test if SSH connection is still alive",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "Connection ID to test"
                                }
                            },
                            "required": ["connection_id"]
                        }
                    ),
                    
                    # Command Execution Tools
                    Tool(
                        name="mcp_ssh_execute",
                        description="Execute single command on remote host",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "SSH connection ID"
                                },
                                "command": {
                                    "type": "string",
                                    "description": "Command to execute"
                                },
                                "timeout": {
                                    "type": "number",
                                    "default": 30.0,
                                    "description": "Command timeout in seconds"
                                },
                                "show_output": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Whether to return command output"
                                },
                                "return_exit_code": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Include exit code in response"
                                }
                            },
                            "required": ["connection_id", "command"]
                        }
                    ),
                    Tool(
                        name="mcp_ssh_execute_interactive",
                        description="Execute command with interactive prompts (like expect)",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "SSH connection ID"
                                },
                                "command": {
                                    "type": "string",
                                    "description": "Command to execute"
                                },
                                "expect_prompts": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of expected prompt patterns"
                                },
                                "responses": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of responses to prompts"
                                },
                                "timeout": {
                                    "type": "number",
                                    "default": 30.0,
                                    "description": "Command timeout in seconds"
                                }
                            },
                            "required": ["connection_id", "command", "expect_prompts", "responses"]
                        }
                    ),
                    Tool(
                        name="mcp_ssh_execute_multi",
                        description="Execute multiple commands in sequence",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "SSH connection ID"
                                },
                                "commands": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of commands to execute"
                                },
                                "stop_on_error": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Stop execution if command fails"
                                }
                            },
                            "required": ["connection_id", "commands"]
                        }
                    ),
                    
                    # File Operation Tools
                    Tool(
                        name="mcp_ssh_upload",
                        description="Upload file or directory to remote host",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "SSH connection ID"
                                },
                                "local_path": {
                                    "type": "string",
                                    "description": "Local file/directory path"
                                },
                                "remote_path": {
                                    "type": "string",
                                    "description": "Remote destination path"
                                },
                                "recursive": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Upload directories recursively"
                                },
                                "preserve_permissions": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Preserve file permissions"
                                }
                            },
                            "required": ["connection_id", "local_path", "remote_path"]
                        }
                    ),
                    Tool(
                        name="mcp_ssh_download",
                        description="Download file or directory from remote host",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "SSH connection ID"
                                },
                                "remote_path": {
                                    "type": "string",
                                    "description": "Remote file/directory path"
                                },
                                "local_path": {
                                    "type": "string",
                                    "description": "Local destination path"
                                },
                                "recursive": {
                                    "type": "boolean",
                                    "default": False,
                                    "description": "Download directories recursively"
                                }
                            },
                            "required": ["connection_id", "remote_path", "local_path"]
                        }
                    ),
                    Tool(
                        name="mcp_ssh_list_directory",
                        description="List files and directories on remote host",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "SSH connection ID"
                                },
                                "remote_path": {
                                    "type": "string",
                                    "default": ".",
                                    "description": "Remote directory path"
                                },
                                "detailed": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Show detailed file information"
                                }
                            },
                            "required": ["connection_id"]
                        }
                    ),
                    
                    # Utility Tools
                    Tool(
                        name="mcp_ssh_check_file_exists",
                        description="Check if file or directory exists on remote host",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "SSH connection ID"
                                },
                                "remote_path": {
                                    "type": "string",
                                    "description": "Remote file/directory path"
                                }
                            },
                            "required": ["connection_id", "remote_path"]
                        }
                    ),
                    Tool(
                        name="mcp_ssh_get_system_info",
                        description="Get system information from remote host",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "SSH connection ID"
                                }
                            },
                            "required": ["connection_id"]
                        }
                    ),
                    Tool(
                        name="mcp_ssh_get_command_history",
                        description="Get history of executed commands for connection",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "connection_id": {
                                    "type": "string",
                                    "description": "SSH connection ID"
                                },
                                "limit": {
                                    "type": "integer",
                                    "default": 50,
                                    "description": "Number of recent commands to return"
                                }
                            },
                            "required": ["connection_id"]
                        }
                    ),
                ]
            )
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls."""
            try:
                if name == "mcp_ssh_connect":
                    return await self._handle_connect(arguments)
                elif name == "mcp_ssh_disconnect":
                    return await self._handle_disconnect(arguments)
                elif name == "mcp_ssh_list_connections":
                    return await self._handle_list_connections(arguments)
                elif name == "mcp_ssh_test_connection":
                    return await self._handle_test_connection(arguments)
                elif name == "mcp_ssh_execute":
                    return await self._handle_execute(arguments)
                elif name == "mcp_ssh_execute_interactive":
                    return await self._handle_execute_interactive(arguments)
                elif name == "mcp_ssh_execute_multi":
                    return await self._handle_execute_multi(arguments)
                elif name == "mcp_ssh_upload":
                    return await self._handle_upload(arguments)
                elif name == "mcp_ssh_download":
                    return await self._handle_download(arguments)
                elif name == "mcp_ssh_list_directory":
                    return await self._handle_list_directory(arguments)
                elif name == "mcp_ssh_check_file_exists":
                    return await self._handle_check_file_exists(arguments)
                elif name == "mcp_ssh_get_system_info":
                    return await self._handle_get_system_info(arguments)
                elif name == "mcp_ssh_get_command_history":
                    return await self._handle_get_command_history(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                        isError=True
                    )
            except Exception as e:
                error_msg = f"Error executing {name}: {str(e)}"
                self.logger.error(f"{error_msg}\n{traceback.format_exc()}")
                return CallToolResult(
                    content=[TextContent(type="text", text=error_msg)],
                    isError=True
                )
    
    async def _handle_connect(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle SSH connection."""
        try:
            connection_id = self.ssh_manager.create_connection(
                host=arguments["host"],
                username=arguments["username"],
                password=arguments.get("password"),
                private_key=arguments.get("private_key"),
                port=arguments.get("port", 22),
                timeout=arguments.get("timeout", 30.0)
            )
            
            result = {
                "connection_id": connection_id,
                "host": arguments["host"],
                "username": arguments["username"],
                "port": arguments.get("port", 22),
                "status": "connected"
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"SSH connection established successfully!\n\nConnection ID: {connection_id}\nHost: {arguments['host']}:{arguments.get('port', 22)}\nUsername: {arguments['username']}\n\nUse this connection_id for subsequent SSH operations."
                )]
            )
        except SSHBaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"SSH connection failed: {str(e)}")],
                isError=True
            )
    
    async def _handle_disconnect(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle SSH disconnection."""
        connection_id = arguments["connection_id"]
        success = self.ssh_manager.disconnect(connection_id)
        
        if success:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"SSH connection {connection_id} disconnected successfully."
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"Connection {connection_id} not found or already disconnected."
                )],
                isError=True
            )
    
    async def _handle_list_connections(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle listing SSH connections."""
        connections = self.ssh_manager.list_connections()
        
        if not connections:
            return CallToolResult(
                content=[TextContent(type="text", text="No active SSH connections.")]
            )
        
        result = "Active SSH Connections:\n\n"
        for conn in connections:
            result += f"Connection ID: {conn['id']}\n"
            result += f"  Host: {conn['host']}:{conn['port']}\n"
            result += f"  Username: {conn['username']}\n"
            result += f"  Status: {'Connected' if conn['is_connected'] else 'Disconnected'}\n"
            result += f"  Commands executed: {conn['command_count']}\n"
            result += f"  Active tunnels: {conn['tunnel_count']}\n"
            result += f"  Created: {conn['created_at']}\n"
            result += f"  Last used: {conn['last_used']}\n\n"
        
        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )
    
    async def _handle_test_connection(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle testing SSH connection."""
        connection_id = arguments["connection_id"]
        is_alive = self.ssh_manager.test_connection(connection_id)
        
        status = "alive" if is_alive else "dead"
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=f"Connection {connection_id} is {status}."
            )]
        )
    
    async def _handle_execute(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle command execution."""
        try:
            result = self.ssh_manager.execute_command(
                connection_id=arguments["connection_id"],
                command=arguments["command"],
                timeout=arguments.get("timeout", 30.0),
                return_exit_code=arguments.get("return_exit_code", False)
            )
            
            response = f"Command: {result.command}\n"
            response += f"Exit Code: {result.exit_code}\n"
            response += f"Execution Time: {result.execution_time:.2f}s\n"
            response += f"Success: {result.success}\n\n"
            
            if arguments.get("show_output", True):
                if result.stdout:
                    response += f"STDOUT:\n{result.stdout}\n"
                if result.stderr:
                    response += f"STDERR:\n{result.stderr}\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response)]
            )
        except SSHBaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Command execution failed: {str(e)}")],
                isError=True
            )
    
    async def _handle_execute_interactive(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle interactive command execution."""
        try:
            result = self.ssh_manager.execute_interactive_command(
                connection_id=arguments["connection_id"],
                command=arguments["command"],
                expect_prompts=arguments["expect_prompts"],
                responses=arguments["responses"],
                timeout=arguments.get("timeout", 30.0)
            )
            
            response = f"Interactive Command: {result.command}\n"
            response += f"Execution Time: {result.execution_time:.2f}s\n\n"
            response += f"Output:\n{result.stdout}\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response)]
            )
        except SSHBaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Interactive command failed: {str(e)}")],
                isError=True
            )
    
    async def _handle_execute_multi(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle multiple command execution."""
        try:
            connection_id = arguments["connection_id"]
            commands = arguments["commands"]
            stop_on_error = arguments.get("stop_on_error", True)
            
            results = []
            response = f"Executing {len(commands)} commands:\n\n"
            
            for i, command in enumerate(commands, 1):
                try:
                    result = self.ssh_manager.execute_command(
                        connection_id=connection_id,
                        command=command,
                        timeout=30.0
                    )
                    
                    response += f"Command {i}: {command}\n"
                    response += f"Exit Code: {result.exit_code}\n"
                    response += f"Success: {result.success}\n"
                    
                    if result.stdout:
                        response += f"STDOUT:\n{result.stdout}\n"
                    if result.stderr:
                        response += f"STDERR:\n{result.stderr}\n"
                    
                    response += "-" * 50 + "\n"
                    results.append(result)
                    
                    if not result.success and stop_on_error:
                        response += f"Stopping execution due to error in command {i}\n"
                        break
                        
                except SSHBaseError as e:
                    response += f"Command {i} failed: {str(e)}\n"
                    if stop_on_error:
                        response += f"Stopping execution due to error in command {i}\n"
                        break
            
            return CallToolResult(
                content=[TextContent(type="text", text=response)]
            )
        except SSHBaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Multi-command execution failed: {str(e)}")],
                isError=True
            )
    
    async def _handle_upload(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle file upload."""
        try:
            success = self.ssh_manager.upload_file(
                connection_id=arguments["connection_id"],
                local_path=arguments["local_path"],
                remote_path=arguments["remote_path"],
                recursive=arguments.get("recursive", False),
                preserve_permissions=arguments.get("preserve_permissions", True)
            )
            
            if success:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"File uploaded successfully: {arguments['local_path']} -> {arguments['remote_path']}"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text="File upload failed")],
                    isError=True
                )
        except SSHBaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"File upload failed: {str(e)}")],
                isError=True
            )
    
    async def _handle_download(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle file download."""
        try:
            success = self.ssh_manager.download_file(
                connection_id=arguments["connection_id"],
                remote_path=arguments["remote_path"],
                local_path=arguments["local_path"],
                recursive=arguments.get("recursive", False)
            )
            
            if success:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"File downloaded successfully: {arguments['remote_path']} -> {arguments['local_path']}"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(type="text", text="File download failed")],
                    isError=True
                )
        except SSHBaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"File download failed: {str(e)}")],
                isError=True
            )
    
    async def _handle_list_directory(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle directory listing."""
        try:
            files = self.ssh_manager.list_directory(
                connection_id=arguments["connection_id"],
                remote_path=arguments.get("remote_path", "."),
                detailed=arguments.get("detailed", True)
            )
            
            if not files:
                return CallToolResult(
                    content=[TextContent(type="text", text="Directory is empty.")]
                )
            
            response = f"Directory listing for {arguments.get('remote_path', '.')}:\n\n"
            
            if arguments.get("detailed", True):
                response += f"{'Name':<30} {'Size':<10} {'Permissions':<10} {'Type':<10} {'Modified':<20}\n"
                response += "-" * 80 + "\n"
                
                for file in files:
                    file_type = "DIR" if file.is_directory else "FILE"
                    response += f"{file.name:<30} {file.size:<10} {file.permissions:<10} {file_type:<10} {file.modified_time:<20}\n"
            else:
                for file in files:
                    response += f"{file.name}\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response)]
            )
        except SSHBaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Directory listing failed: {str(e)}")],
                isError=True
            )
    
    async def _handle_check_file_exists(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle file existence check."""
        try:
            exists = self.ssh_manager.file_exists(
                connection_id=arguments["connection_id"],
                remote_path=arguments["remote_path"]
            )
            
            status = "exists" if exists else "does not exist"
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"File {arguments['remote_path']} {status}."
                )]
            )
        except SSHBaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"File existence check failed: {str(e)}")],
                isError=True
            )
    
    async def _handle_get_system_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle system information retrieval."""
        try:
            system_info = self.ssh_manager.get_system_info(arguments["connection_id"])
            
            response = "System Information:\n\n"
            for key, value in system_info.items():
                response += f"{key.capitalize()}: {value}\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response)]
            )
        except SSHBaseError as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"System info retrieval failed: {str(e)}")],
                isError=True
            )
    
    async def _handle_get_command_history(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Handle command history retrieval."""
        try:
            connection = self.ssh_manager.get_connection(arguments["connection_id"])
            if not connection:
                return CallToolResult(
                    content=[TextContent(type="text", text="Connection not found.")],
                    isError=True
                )
            
            limit = arguments.get("limit", 50)
            history = connection.command_history[-limit:]
            
            if not history:
                return CallToolResult(
                    content=[TextContent(type="text", text="No command history available.")]
                )
            
            response = f"Command History (last {len(history)} commands):\n\n"
            for i, command in enumerate(history, 1):
                response += f"{i:3d}. {command}\n"
            
            return CallToolResult(
                content=[TextContent(type="text", text=response)]
            )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Command history retrieval failed: {str(e)}")],
                isError=True
            )
    
    async def run(self):
        """Run the MCP server."""
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="mcp-ssh-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=None,
                            experimental_capabilities=None
                        )
                    )
                )
        except KeyboardInterrupt:
            self.logger.info("Server interrupted by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
        finally:
            # Clean up all connections
            self.ssh_manager.cleanup_all_connections()
            self.logger.info("Server shutdown complete")


def main():
    """Main entry point for the MCP SSH server."""
    server = MCPSSHServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main() 