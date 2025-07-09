"""
Custom exceptions for the MCP SSH Server.

This module defines all custom exceptions used throughout the SSH server
for proper error handling and user feedback.
"""

from typing import Optional, Any


class SSHBaseError(Exception):
    """Base exception class for all SSH-related errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class SSHConnectionError(SSHBaseError):
    """Raised when SSH connection fails or is lost."""
    
    def __init__(self, message: str, host: Optional[str] = None, port: Optional[int] = None, details: Optional[dict] = None) -> None:
        super().__init__(message, details)
        self.host = host
        self.port = port


class SSHAuthenticationError(SSHBaseError):
    """Raised when SSH authentication fails."""
    
    def __init__(self, message: str, username: Optional[str] = None, auth_method: Optional[str] = None, details: Optional[dict] = None) -> None:
        super().__init__(message, details)
        self.username = username
        self.auth_method = auth_method


class SSHCommandError(SSHBaseError):
    """Raised when SSH command execution fails."""
    
    def __init__(self, message: str, command: Optional[str] = None, exit_code: Optional[int] = None, stderr: Optional[str] = None, details: Optional[dict] = None) -> None:
        super().__init__(message, details)
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr


class SSHFileOperationError(SSHBaseError):
    """Raised when SSH file operations fail."""
    
    def __init__(self, message: str, local_path: Optional[str] = None, remote_path: Optional[str] = None, operation: Optional[str] = None, details: Optional[dict] = None) -> None:
        super().__init__(message, details)
        self.local_path = local_path
        self.remote_path = remote_path
        self.operation = operation


class SSHTunnelError(SSHBaseError):
    """Raised when SSH tunnel operations fail."""
    
    def __init__(self, message: str, local_port: Optional[int] = None, remote_host: Optional[str] = None, remote_port: Optional[int] = None, details: Optional[dict] = None) -> None:
        super().__init__(message, details)
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port


class SSHTimeoutError(SSHBaseError):
    """Raised when SSH operations timeout."""
    
    def __init__(self, message: str, timeout: Optional[float] = None, operation: Optional[str] = None, details: Optional[dict] = None) -> None:
        super().__init__(message, details)
        self.timeout = timeout
        self.operation = operation


class SSHConfigurationError(SSHBaseError):
    """Raised when SSH configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, config_value: Optional[Any] = None, details: Optional[dict] = None) -> None:
        super().__init__(message, details)
        self.config_key = config_key
        self.config_value = config_value


class SSHPermissionError(SSHBaseError):
    """Raised when SSH operations fail due to permission issues."""
    
    def __init__(self, message: str, path: Optional[str] = None, required_permission: Optional[str] = None, details: Optional[dict] = None) -> None:
        super().__init__(message, details)
        self.path = path
        self.required_permission = required_permission 