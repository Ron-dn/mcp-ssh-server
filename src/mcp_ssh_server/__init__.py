"""
MCP SSH Server - A powerful, generic SSH MCP server for secure remote system access.

This package provides a comprehensive SSH server implementation for the Model Context Protocol,
enabling secure remote system access, command execution, file operations, and more.
"""

__version__ = "1.0.0"
__author__ = "MCP SSH Server Contributors"
__email__ = "contributors@mcp-ssh-server.com"
__license__ = "MIT"

from .server import MCPSSHServer
from .ssh_manager import SSHConnectionManager
from .exceptions import (
    SSHConnectionError,
    SSHAuthenticationError,
    SSHCommandError,
    SSHFileOperationError,
    SSHTunnelError,
)

__all__ = [
    "MCPSSHServer",
    "SSHConnectionManager",
    "SSHConnectionError",
    "SSHAuthenticationError", 
    "SSHCommandError",
    "SSHFileOperationError",
    "SSHTunnelError",
] 