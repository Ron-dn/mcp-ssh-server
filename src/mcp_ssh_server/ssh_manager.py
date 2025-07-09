"""
SSH Connection Manager for MCP SSH Server.

This module provides the core SSH connection management functionality,
including connection pooling, session handling, and all SSH operations.
"""

import asyncio
import logging
import socket
import threading
import time
import uuid
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import io
import stat

import paramiko
from paramiko import SSHClient, AutoAddPolicy, RSAKey, DSSKey, ECDSAKey, Ed25519Key
from paramiko.sftp_client import SFTPClient

from .exceptions import (
    SSHConnectionError,
    SSHAuthenticationError,
    SSHCommandError,
    SSHFileOperationError,
    SSHTunnelError,
    SSHTimeoutError,
)


@dataclass
class SSHConnection:
    """Represents an SSH connection with metadata."""
    id: str
    host: str
    port: int
    username: str
    client: SSHClient
    sftp: Optional[SFTPClient] = None
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    is_connected: bool = True
    command_history: List[str] = field(default_factory=list)
    tunnels: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    success: bool


@dataclass
class FileInfo:
    """Information about a remote file."""
    name: str
    path: str
    size: int
    is_directory: bool
    permissions: str
    modified_time: float
    owner: str
    group: str


class SSHConnectionManager:
    """Manages SSH connections with pooling and session handling."""
    
    def __init__(self, max_connections: int = 50, connection_timeout: float = 30.0):
        self.max_connections = max_connections
        self.connection_timeout = connection_timeout
        self.connections: Dict[str, SSHConnection] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Configure paramiko logging
        paramiko.util.log_to_file('/tmp/paramiko.log', level=logging.WARNING)
        
    def create_connection(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        port: int = 22,
        timeout: float = 30.0,
    ) -> str:
        """Create a new SSH connection."""
        with self.lock:
            if len(self.connections) >= self.max_connections:
                # Clean up old connections
                self._cleanup_old_connections()
                
                if len(self.connections) >= self.max_connections:
                    raise SSHConnectionError(
                        "Maximum number of connections reached",
                        details={"max_connections": self.max_connections}
                    )
            
            connection_id = f"ssh_{uuid.uuid4().hex[:8]}_{host}_{username}"
            
            try:
                # Create SSH client
                client = SSHClient()
                client.set_missing_host_key_policy(AutoAddPolicy())
                
                # Connect with timeout
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    pkey=self._parse_private_key(private_key) if private_key else None,
                    timeout=timeout,
                    banner_timeout=timeout,
                    auth_timeout=timeout,
                    look_for_keys=False,
                    allow_agent=False,
                )
                
                # Create SFTP client
                sftp = client.open_sftp()
                
                # Store connection
                connection = SSHConnection(
                    id=connection_id,
                    host=host,
                    port=port,
                    username=username,
                    client=client,
                    sftp=sftp,
                )
                
                self.connections[connection_id] = connection
                
                self.logger.info(f"SSH connection established: {connection_id}")
                return connection_id
                
            except paramiko.AuthenticationException as e:
                raise SSHAuthenticationError(
                    f"Authentication failed for {username}@{host}",
                    username=username,
                    auth_method="password" if password else "key",
                    details={"error": str(e)}
                )
            except paramiko.SSHException as e:
                raise SSHConnectionError(
                    f"SSH connection failed to {host}:{port}",
                    host=host,
                    port=port,
                    details={"error": str(e)}
                )
            except socket.error as e:
                raise SSHConnectionError(
                    f"Network error connecting to {host}:{port}",
                    host=host,
                    port=port,
                    details={"error": str(e)}
                )
            except Exception as e:
                raise SSHConnectionError(
                    f"Unexpected error connecting to {host}:{port}",
                    host=host,
                    port=port,
                    details={"error": str(e)}
                )
    
    def disconnect(self, connection_id: str) -> bool:
        """Disconnect an SSH connection."""
        with self.lock:
            if connection_id not in self.connections:
                return False
            
            connection = self.connections[connection_id]
            
            try:
                # Close tunnels
                for tunnel_id, tunnel in connection.tunnels.items():
                    try:
                        tunnel.close()
                    except Exception as e:
                        self.logger.warning(f"Error closing tunnel {tunnel_id}: {e}")
                
                # Close SFTP
                if connection.sftp:
                    connection.sftp.close()
                
                # Close SSH client
                connection.client.close()
                
                # Remove from connections
                del self.connections[connection_id]
                
                self.logger.info(f"SSH connection closed: {connection_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error closing connection {connection_id}: {e}")
                # Still remove from connections
                del self.connections[connection_id]
                return False
    
    def get_connection(self, connection_id: str) -> Optional[SSHConnection]:
        """Get an SSH connection by ID."""
        with self.lock:
            connection = self.connections.get(connection_id)
            if connection:
                connection.last_used = time.time()
            return connection
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """List all active connections."""
        with self.lock:
            connections = []
            for conn in self.connections.values():
                connections.append({
                    "id": conn.id,
                    "host": conn.host,
                    "port": conn.port,
                    "username": conn.username,
                    "created_at": conn.created_at,
                    "last_used": conn.last_used,
                    "is_connected": conn.is_connected,
                    "command_count": len(conn.command_history),
                    "tunnel_count": len(conn.tunnels),
                })
            return connections
    
    def test_connection(self, connection_id: str) -> bool:
        """Test if an SSH connection is still alive."""
        connection = self.get_connection(connection_id)
        if not connection:
            return False
        
        try:
            # Send a simple command to test connection
            transport = connection.client.get_transport()
            if transport and transport.is_active():
                # Try to execute a simple command
                stdin, stdout, stderr = connection.client.exec_command("echo test", timeout=5)
                result = stdout.read().decode().strip()
                return result == "test"
            return False
        except Exception:
            connection.is_connected = False
            return False
    
    def execute_command(
        self,
        connection_id: str,
        command: str,
        timeout: float = 30.0,
        return_exit_code: bool = False,
    ) -> CommandResult:
        """Execute a command on the remote host."""
        connection = self.get_connection(connection_id)
        if not connection:
            raise SSHConnectionError(f"Connection {connection_id} not found")
        
        if not self.test_connection(connection_id):
            raise SSHConnectionError(f"Connection {connection_id} is not active")
        
        start_time = time.time()
        
        try:
            # Execute command
            stdin, stdout, stderr = connection.client.exec_command(command, timeout=timeout)
            
            # Read output
            stdout_data = stdout.read().decode('utf-8', errors='replace')
            stderr_data = stderr.read().decode('utf-8', errors='replace')
            exit_code = stdout.channel.recv_exit_status()
            
            execution_time = time.time() - start_time
            
            # Add to command history
            connection.command_history.append(command)
            if len(connection.command_history) > 100:  # Keep last 100 commands
                connection.command_history = connection.command_history[-100:]
            
            result = CommandResult(
                command=command,
                stdout=stdout_data,
                stderr=stderr_data,
                exit_code=exit_code,
                execution_time=execution_time,
                success=exit_code == 0,
            )
            
            self.logger.debug(f"Command executed on {connection_id}: {command}")
            return result
            
        except paramiko.SSHException as e:
            raise SSHCommandError(
                f"SSH error executing command: {command}",
                command=command,
                details={"error": str(e)}
            )
        except socket.timeout:
            raise SSHTimeoutError(
                f"Command timed out after {timeout} seconds: {command}",
                timeout=timeout,
                operation="command_execution"
            )
        except Exception as e:
            raise SSHCommandError(
                f"Error executing command: {command}",
                command=command,
                details={"error": str(e)}
            )
    
    def execute_interactive_command(
        self,
        connection_id: str,
        command: str,
        expect_prompts: List[str],
        responses: List[str],
        timeout: float = 30.0,
    ) -> CommandResult:
        """Execute an interactive command with expect-like functionality."""
        connection = self.get_connection(connection_id)
        if not connection:
            raise SSHConnectionError(f"Connection {connection_id} not found")
        
        if not self.test_connection(connection_id):
            raise SSHConnectionError(f"Connection {connection_id} is not active")
        
        if len(expect_prompts) != len(responses):
            raise SSHCommandError(
                "Number of expect prompts must match number of responses",
                command=command
            )
        
        start_time = time.time()
        
        try:
            # Create channel for interactive session
            channel = connection.client.invoke_shell()
            channel.settimeout(timeout)
            
            # Send initial command
            channel.send(command + '\n')
            
            output = ""
            for i, prompt in enumerate(expect_prompts):
                # Wait for prompt
                while True:
                    if channel.recv_ready():
                        data = channel.recv(1024).decode('utf-8', errors='replace')
                        output += data
                        if prompt in output:
                            break
                    time.sleep(0.1)
                    if time.time() - start_time > timeout:
                        raise SSHTimeoutError(
                            f"Interactive command timed out waiting for prompt: {prompt}",
                            timeout=timeout,
                            operation="interactive_command"
                        )
                
                # Send response
                channel.send(responses[i] + '\n')
                time.sleep(0.1)  # Small delay to ensure response is sent
            
            # Wait for final output
            time.sleep(0.5)
            while channel.recv_ready():
                output += channel.recv(1024).decode('utf-8', errors='replace')
            
            channel.close()
            
            execution_time = time.time() - start_time
            
            # Add to command history
            connection.command_history.append(f"INTERACTIVE: {command}")
            
            result = CommandResult(
                command=command,
                stdout=output,
                stderr="",
                exit_code=0,  # Interactive commands don't have exit codes
                execution_time=execution_time,
                success=True,
            )
            
            self.logger.debug(f"Interactive command executed on {connection_id}: {command}")
            return result
            
        except Exception as e:
            raise SSHCommandError(
                f"Error executing interactive command: {command}",
                command=command,
                details={"error": str(e)}
            )
    
    def upload_file(
        self,
        connection_id: str,
        local_path: str,
        remote_path: str,
        recursive: bool = False,
        preserve_permissions: bool = True,
    ) -> bool:
        """Upload a file or directory to the remote host."""
        connection = self.get_connection(connection_id)
        if not connection or not connection.sftp:
            raise SSHConnectionError(f"Connection {connection_id} not found or SFTP not available")
        
        local_path_obj = Path(local_path)
        
        if not local_path_obj.exists():
            raise SSHFileOperationError(
                f"Local path does not exist: {local_path}",
                local_path=local_path,
                operation="upload"
            )
        
        try:
            if local_path_obj.is_file():
                # Upload single file
                connection.sftp.put(local_path, remote_path)
                
                if preserve_permissions:
                    # Preserve file permissions
                    local_stat = local_path_obj.stat()
                    connection.sftp.chmod(remote_path, local_stat.st_mode)
                
                self.logger.debug(f"File uploaded: {local_path} -> {remote_path}")
                return True
            
            elif local_path_obj.is_dir() and recursive:
                # Upload directory recursively
                self._upload_directory_recursive(
                    connection.sftp, local_path_obj, remote_path, preserve_permissions
                )
                self.logger.debug(f"Directory uploaded: {local_path} -> {remote_path}")
                return True
            
            else:
                raise SSHFileOperationError(
                    f"Path is a directory but recursive=False: {local_path}",
                    local_path=local_path,
                    operation="upload"
                )
                
        except paramiko.SFTPError as e:
            raise SSHFileOperationError(
                f"SFTP error uploading {local_path} to {remote_path}",
                local_path=local_path,
                remote_path=remote_path,
                operation="upload",
                details={"error": str(e)}
            )
        except Exception as e:
            raise SSHFileOperationError(
                f"Error uploading {local_path} to {remote_path}",
                local_path=local_path,
                remote_path=remote_path,
                operation="upload",
                details={"error": str(e)}
            )
    
    def download_file(
        self,
        connection_id: str,
        remote_path: str,
        local_path: str,
        recursive: bool = False,
    ) -> bool:
        """Download a file or directory from the remote host."""
        connection = self.get_connection(connection_id)
        if not connection or not connection.sftp:
            raise SSHConnectionError(f"Connection {connection_id} not found or SFTP not available")
        
        try:
            # Check if remote path exists
            remote_stat = connection.sftp.stat(remote_path)
            
            if stat.S_ISREG(remote_stat.st_mode):
                # Download single file
                connection.sftp.get(remote_path, local_path)
                self.logger.debug(f"File downloaded: {remote_path} -> {local_path}")
                return True
            
            elif stat.S_ISDIR(remote_stat.st_mode) and recursive:
                # Download directory recursively
                self._download_directory_recursive(
                    connection.sftp, remote_path, local_path
                )
                self.logger.debug(f"Directory downloaded: {remote_path} -> {local_path}")
                return True
            
            else:
                raise SSHFileOperationError(
                    f"Path is a directory but recursive=False: {remote_path}",
                    remote_path=remote_path,
                    operation="download"
                )
                
        except FileNotFoundError:
            raise SSHFileOperationError(
                f"Remote path does not exist: {remote_path}",
                remote_path=remote_path,
                operation="download"
            )
        except paramiko.SFTPError as e:
            raise SSHFileOperationError(
                f"SFTP error downloading {remote_path} to {local_path}",
                local_path=local_path,
                remote_path=remote_path,
                operation="download",
                details={"error": str(e)}
            )
        except Exception as e:
            raise SSHFileOperationError(
                f"Error downloading {remote_path} to {local_path}",
                local_path=local_path,
                remote_path=remote_path,
                operation="download",
                details={"error": str(e)}
            )
    
    def list_directory(
        self,
        connection_id: str,
        remote_path: str = ".",
        detailed: bool = True,
    ) -> List[FileInfo]:
        """List files in a remote directory."""
        connection = self.get_connection(connection_id)
        if not connection or not connection.sftp:
            raise SSHConnectionError(f"Connection {connection_id} not found or SFTP not available")
        
        try:
            files = []
            
            if detailed:
                # Get detailed file information
                for attr in connection.sftp.listdir_attr(remote_path):
                    file_info = FileInfo(
                        name=attr.filename,
                        path=f"{remote_path}/{attr.filename}".replace("//", "/"),
                        size=attr.st_size or 0,
                        is_directory=stat.S_ISDIR(attr.st_mode) if attr.st_mode else False,
                        permissions=oct(attr.st_mode)[-3:] if attr.st_mode else "000",
                        modified_time=attr.st_mtime or 0,
                        owner=str(attr.st_uid) if attr.st_uid else "unknown",
                        group=str(attr.st_gid) if attr.st_gid else "unknown",
                    )
                    files.append(file_info)
            else:
                # Get simple file list
                for filename in connection.sftp.listdir(remote_path):
                    file_info = FileInfo(
                        name=filename,
                        path=f"{remote_path}/{filename}".replace("//", "/"),
                        size=0,
                        is_directory=False,
                        permissions="000",
                        modified_time=0,
                        owner="unknown",
                        group="unknown",
                    )
                    files.append(file_info)
            
            return files
            
        except paramiko.SFTPError as e:
            raise SSHFileOperationError(
                f"SFTP error listing directory: {remote_path}",
                remote_path=remote_path,
                operation="list_directory",
                details={"error": str(e)}
            )
        except Exception as e:
            raise SSHFileOperationError(
                f"Error listing directory: {remote_path}",
                remote_path=remote_path,
                operation="list_directory",
                details={"error": str(e)}
            )
    
    def file_exists(self, connection_id: str, remote_path: str) -> bool:
        """Check if a file exists on the remote host."""
        connection = self.get_connection(connection_id)
        if not connection or not connection.sftp:
            raise SSHConnectionError(f"Connection {connection_id} not found or SFTP not available")
        
        try:
            connection.sftp.stat(remote_path)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def get_system_info(self, connection_id: str) -> Dict[str, Any]:
        """Get system information from the remote host."""
        commands = {
            "hostname": "hostname",
            "kernel": "uname -r",
            "os": "uname -o",
            "architecture": "uname -m",
            "uptime": "uptime",
            "memory": "free -h",
            "disk": "df -h",
            "cpu": "lscpu | head -20",
        }
        
        system_info = {}
        
        for key, command in commands.items():
            try:
                result = self.execute_command(connection_id, command, timeout=10.0)
                system_info[key] = result.stdout.strip() if result.success else "N/A"
            except Exception:
                system_info[key] = "N/A"
        
        return system_info
    
    def cleanup_all_connections(self) -> None:
        """Clean up all SSH connections."""
        with self.lock:
            connection_ids = list(self.connections.keys())
            for connection_id in connection_ids:
                try:
                    self.disconnect(connection_id)
                except Exception as e:
                    self.logger.error(f"Error cleaning up connection {connection_id}: {e}")
    
    def _cleanup_old_connections(self) -> None:
        """Clean up old or inactive connections."""
        current_time = time.time()
        connections_to_remove = []
        
        for connection_id, connection in self.connections.items():
            # Remove connections older than 1 hour or inactive for 30 minutes
            if (current_time - connection.created_at > 3600 or 
                current_time - connection.last_used > 1800 or
                not connection.is_connected):
                connections_to_remove.append(connection_id)
        
        for connection_id in connections_to_remove:
            try:
                self.disconnect(connection_id)
            except Exception as e:
                self.logger.error(f"Error cleaning up old connection {connection_id}: {e}")
    
    def _parse_private_key(self, private_key_str: str) -> paramiko.PKey:
        """Parse a private key string into a paramiko key object."""
        key_types = [RSAKey, DSSKey, ECDSAKey, Ed25519Key]
        
        for key_type in key_types:
            try:
                key_file = io.StringIO(private_key_str)
                return key_type.from_private_key(key_file)
            except Exception:
                continue
        
        raise SSHAuthenticationError(
            "Invalid private key format",
            auth_method="key",
            details={"supported_types": ["RSA", "DSS", "ECDSA", "Ed25519"]}
        )
    
    def _upload_directory_recursive(
        self,
        sftp: SFTPClient,
        local_dir: Path,
        remote_dir: str,
        preserve_permissions: bool,
    ) -> None:
        """Recursively upload a directory."""
        # Create remote directory
        try:
            sftp.mkdir(remote_dir)
        except Exception:
            pass  # Directory might already exist
        
        for item in local_dir.iterdir():
            local_path = item
            remote_path = f"{remote_dir}/{item.name}"
            
            if item.is_file():
                sftp.put(str(local_path), remote_path)
                if preserve_permissions:
                    local_stat = local_path.stat()
                    sftp.chmod(remote_path, local_stat.st_mode)
            elif item.is_dir():
                self._upload_directory_recursive(sftp, local_path, remote_path, preserve_permissions)
    
    def _download_directory_recursive(
        self,
        sftp: SFTPClient,
        remote_dir: str,
        local_dir: str,
    ) -> None:
        """Recursively download a directory."""
        local_path = Path(local_dir)
        local_path.mkdir(parents=True, exist_ok=True)
        
        for attr in sftp.listdir_attr(remote_dir):
            remote_path = f"{remote_dir}/{attr.filename}"
            local_file_path = local_path / attr.filename
            
            if stat.S_ISREG(attr.st_mode):
                sftp.get(remote_path, str(local_file_path))
            elif stat.S_ISDIR(attr.st_mode):
                self._download_directory_recursive(sftp, remote_path, str(local_file_path)) 