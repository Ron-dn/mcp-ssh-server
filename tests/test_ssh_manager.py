#!/usr/bin/env python3
"""
Unit tests for SSH Manager.

This module contains comprehensive tests for the SSH connection manager,
including connection handling, command execution, and file operations.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import tempfile
import os
from pathlib import Path

import paramiko

from mcp_ssh_server.ssh_manager import SSHConnectionManager, SSHConnection, CommandResult
from mcp_ssh_server.exceptions import (
    SSHConnectionError,
    SSHAuthenticationError,
    SSHCommandError,
    SSHFileOperationError,
    SSHTimeoutError,
)


class TestSSHConnectionManager(unittest.TestCase):
    """Test cases for SSHConnectionManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ssh_manager = SSHConnectionManager(max_connections=5)
        
    def tearDown(self):
        """Clean up after tests."""
        self.ssh_manager.cleanup_all_connections()
    
    @patch('mcp_ssh_server.ssh_manager.SSHClient')
    def test_create_connection_success(self, mock_ssh_client):
        """Test successful SSH connection creation."""
        # Mock SSH client
        mock_client = Mock()
        mock_sftp = Mock()
        mock_client.open_sftp.return_value = mock_sftp
        mock_ssh_client.return_value = mock_client
        
        # Create connection
        connection_id = self.ssh_manager.create_connection(
            host="test.example.com",
            username="testuser",
            password="testpass"
        )
        
        # Verify connection was created
        self.assertIsNotNone(connection_id)
        self.assertTrue(connection_id.startswith("ssh_"))
        self.assertIn("test.example.com", connection_id)
        self.assertIn("testuser", connection_id)
        
        # Verify connection is stored
        connection = self.ssh_manager.get_connection(connection_id)
        self.assertIsNotNone(connection)
        self.assertEqual(connection.host, "test.example.com")
        self.assertEqual(connection.username, "testuser")
        self.assertEqual(connection.port, 22)
        
        # Verify SSH client was called correctly
        mock_client.connect.assert_called_once_with(
            hostname="test.example.com",
            port=22,
            username="testuser",
            password="testpass",
            pkey=None,
            timeout=30.0,
            banner_timeout=30.0,
            auth_timeout=30.0,
            look_for_keys=False,
            allow_agent=False,
        )
    
    @patch('mcp_ssh_server.ssh_manager.SSHClient')
    def test_create_connection_auth_failure(self, mock_ssh_client):
        """Test SSH connection creation with authentication failure."""
        # Mock SSH client to raise authentication error
        mock_client = Mock()
        mock_client.connect.side_effect = paramiko.AuthenticationException("Auth failed")
        mock_ssh_client.return_value = mock_client
        
        # Test authentication failure
        with self.assertRaises(SSHAuthenticationError) as context:
            self.ssh_manager.create_connection(
                host="test.example.com",
                username="testuser",
                password="wrongpass"
            )
        
        self.assertIn("Authentication failed", str(context.exception))
        self.assertEqual(context.exception.username, "testuser")
        self.assertEqual(context.exception.auth_method, "password")
    
    @patch('mcp_ssh_server.ssh_manager.SSHClient')
    def test_create_connection_network_error(self, mock_ssh_client):
        """Test SSH connection creation with network error."""
        # Mock SSH client to raise socket error
        mock_client = Mock()
        mock_client.connect.side_effect = OSError("Network unreachable")
        mock_ssh_client.return_value = mock_client
        
        # Test network error
        with self.assertRaises(SSHConnectionError) as context:
            self.ssh_manager.create_connection(
                host="unreachable.example.com",
                username="testuser",
                password="testpass"
            )
        
        self.assertIn("Network error", str(context.exception))
        self.assertEqual(context.exception.host, "unreachable.example.com")
        self.assertEqual(context.exception.port, 22)
    
    @patch('mcp_ssh_server.ssh_manager.SSHClient')
    def test_max_connections_limit(self, mock_ssh_client):
        """Test maximum connections limit."""
        # Mock SSH client
        mock_client = Mock()
        mock_sftp = Mock()
        mock_client.open_sftp.return_value = mock_sftp
        mock_ssh_client.return_value = mock_client
        
        # Create maximum number of connections
        connection_ids = []
        for i in range(5):  # max_connections = 5
            connection_id = self.ssh_manager.create_connection(
                host=f"host{i}.example.com",
                username="testuser",
                password="testpass"
            )
            connection_ids.append(connection_id)
        
        # Try to create one more connection - should fail
        with self.assertRaises(SSHConnectionError) as context:
            self.ssh_manager.create_connection(
                host="host6.example.com",
                username="testuser",
                password="testpass"
            )
        
        self.assertIn("Maximum number of connections reached", str(context.exception))
    
    def test_disconnect_connection(self):
        """Test disconnecting SSH connection."""
        # Create a mock connection
        mock_client = Mock()
        mock_sftp = Mock()
        
        connection = SSHConnection(
            id="test_connection",
            host="test.example.com",
            port=22,
            username="testuser",
            client=mock_client,
            sftp=mock_sftp
        )
        
        self.ssh_manager.connections["test_connection"] = connection
        
        # Disconnect
        success = self.ssh_manager.disconnect("test_connection")
        
        # Verify disconnection
        self.assertTrue(success)
        self.assertNotIn("test_connection", self.ssh_manager.connections)
        mock_sftp.close.assert_called_once()
        mock_client.close.assert_called_once()
    
    def test_disconnect_nonexistent_connection(self):
        """Test disconnecting non-existent connection."""
        success = self.ssh_manager.disconnect("nonexistent_connection")
        self.assertFalse(success)
    
    def test_list_connections(self):
        """Test listing active connections."""
        # Create mock connections
        mock_client1 = Mock()
        mock_client2 = Mock()
        
        connection1 = SSHConnection(
            id="conn1",
            host="host1.example.com",
            port=22,
            username="user1",
            client=mock_client1
        )
        
        connection2 = SSHConnection(
            id="conn2",
            host="host2.example.com",
            port=2222,
            username="user2",
            client=mock_client2
        )
        
        self.ssh_manager.connections["conn1"] = connection1
        self.ssh_manager.connections["conn2"] = connection2
        
        # List connections
        connections = self.ssh_manager.list_connections()
        
        # Verify listing
        self.assertEqual(len(connections), 2)
        
        conn1_info = next(c for c in connections if c["id"] == "conn1")
        self.assertEqual(conn1_info["host"], "host1.example.com")
        self.assertEqual(conn1_info["username"], "user1")
        self.assertEqual(conn1_info["port"], 22)
        
        conn2_info = next(c for c in connections if c["id"] == "conn2")
        self.assertEqual(conn2_info["host"], "host2.example.com")
        self.assertEqual(conn2_info["username"], "user2")
        self.assertEqual(conn2_info["port"], 2222)
    
    def test_test_connection_alive(self):
        """Test testing connection that is alive."""
        # Create mock connection
        mock_client = Mock()
        mock_transport = Mock()
        mock_transport.is_active.return_value = True
        mock_client.get_transport.return_value = mock_transport
        
        # Mock exec_command to return "test"
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_stdout.read.return_value = b"test"
        mock_client.exec_command.return_value = (mock_stdin, mock_stdout, mock_stderr)
        
        connection = SSHConnection(
            id="test_connection",
            host="test.example.com",
            port=22,
            username="testuser",
            client=mock_client
        )
        
        self.ssh_manager.connections["test_connection"] = connection
        
        # Test connection
        is_alive = self.ssh_manager.test_connection("test_connection")
        
        # Verify result
        self.assertTrue(is_alive)
        mock_client.exec_command.assert_called_once_with("echo test", timeout=5)
    
    def test_test_connection_dead(self):
        """Test testing connection that is dead."""
        # Create mock connection
        mock_client = Mock()
        mock_transport = Mock()
        mock_transport.is_active.return_value = False
        mock_client.get_transport.return_value = mock_transport
        
        connection = SSHConnection(
            id="test_connection",
            host="test.example.com",
            port=22,
            username="testuser",
            client=mock_client
        )
        
        self.ssh_manager.connections["test_connection"] = connection
        
        # Test connection
        is_alive = self.ssh_manager.test_connection("test_connection")
        
        # Verify result
        self.assertFalse(is_alive)
    
    def test_execute_command_success(self):
        """Test successful command execution."""
        # Create mock connection
        mock_client = Mock()
        mock_transport = Mock()
        mock_transport.is_active.return_value = True
        mock_client.get_transport.return_value = mock_transport
        
        # Mock exec_command for test and actual command
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_channel = Mock()
        mock_channel.recv_exit_status.return_value = 0
        mock_stdout.channel = mock_channel
        mock_stdout.read.return_value = b"command output"
        mock_stderr.read.return_value = b""
        
        def mock_exec_command(cmd, timeout=None):
            if cmd == "echo test":
                test_stdout = Mock()
                test_stdout.read.return_value = b"test"
                return (Mock(), test_stdout, Mock())
            else:
                return (mock_stdin, mock_stdout, mock_stderr)
        
        mock_client.exec_command.side_effect = mock_exec_command
        
        connection = SSHConnection(
            id="test_connection",
            host="test.example.com",
            port=22,
            username="testuser",
            client=mock_client
        )
        
        self.ssh_manager.connections["test_connection"] = connection
        
        # Execute command
        result = self.ssh_manager.execute_command(
            connection_id="test_connection",
            command="ls -la"
        )
        
        # Verify result
        self.assertIsInstance(result, CommandResult)
        self.assertEqual(result.command, "ls -la")
        self.assertEqual(result.stdout, "command output")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.success)
        self.assertGreater(result.execution_time, 0)
        
        # Verify command was added to history
        self.assertIn("ls -la", connection.command_history)
    
    def test_execute_command_failure(self):
        """Test command execution failure."""
        # Create mock connection
        mock_client = Mock()
        mock_transport = Mock()
        mock_transport.is_active.return_value = True
        mock_client.get_transport.return_value = mock_transport
        
        # Mock exec_command for test and actual command
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_channel = Mock()
        mock_channel.recv_exit_status.return_value = 1
        mock_stdout.channel = mock_channel
        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"command not found"
        
        def mock_exec_command(cmd, timeout=None):
            if cmd == "echo test":
                test_stdout = Mock()
                test_stdout.read.return_value = b"test"
                return (Mock(), test_stdout, Mock())
            else:
                return (mock_stdin, mock_stdout, mock_stderr)
        
        mock_client.exec_command.side_effect = mock_exec_command
        
        connection = SSHConnection(
            id="test_connection",
            host="test.example.com",
            port=22,
            username="testuser",
            client=mock_client
        )
        
        self.ssh_manager.connections["test_connection"] = connection
        
        # Execute command
        result = self.ssh_manager.execute_command(
            connection_id="test_connection",
            command="nonexistent_command"
        )
        
        # Verify result
        self.assertEqual(result.exit_code, 1)
        self.assertFalse(result.success)
        self.assertEqual(result.stderr, "command not found")
    
    def test_execute_command_nonexistent_connection(self):
        """Test command execution on non-existent connection."""
        with self.assertRaises(SSHConnectionError) as context:
            self.ssh_manager.execute_command(
                connection_id="nonexistent_connection",
                command="ls -la"
            )
        
        self.assertIn("Connection nonexistent_connection not found", str(context.exception))
    
    def test_file_exists_true(self):
        """Test file existence check - file exists."""
        # Create mock connection
        mock_sftp = Mock()
        mock_sftp.stat.return_value = Mock()  # stat() succeeds
        
        connection = SSHConnection(
            id="test_connection",
            host="test.example.com",
            port=22,
            username="testuser",
            client=Mock(),
            sftp=mock_sftp
        )
        
        self.ssh_manager.connections["test_connection"] = connection
        
        # Check file existence
        exists = self.ssh_manager.file_exists("test_connection", "/tmp/test.txt")
        
        # Verify result
        self.assertTrue(exists)
        mock_sftp.stat.assert_called_once_with("/tmp/test.txt")
    
    def test_file_exists_false(self):
        """Test file existence check - file doesn't exist."""
        # Create mock connection
        mock_sftp = Mock()
        mock_sftp.stat.side_effect = FileNotFoundError()
        
        connection = SSHConnection(
            id="test_connection",
            host="test.example.com",
            port=22,
            username="testuser",
            client=Mock(),
            sftp=mock_sftp
        )
        
        self.ssh_manager.connections["test_connection"] = connection
        
        # Check file existence
        exists = self.ssh_manager.file_exists("test_connection", "/tmp/nonexistent.txt")
        
        # Verify result
        self.assertFalse(exists)
    
    def test_cleanup_all_connections(self):
        """Test cleaning up all connections."""
        # Create mock connections
        mock_client1 = Mock()
        mock_client2 = Mock()
        mock_sftp1 = Mock()
        mock_sftp2 = Mock()
        
        connection1 = SSHConnection(
            id="conn1",
            host="host1.example.com",
            port=22,
            username="user1",
            client=mock_client1,
            sftp=mock_sftp1
        )
        
        connection2 = SSHConnection(
            id="conn2",
            host="host2.example.com",
            port=22,
            username="user2",
            client=mock_client2,
            sftp=mock_sftp2
        )
        
        self.ssh_manager.connections["conn1"] = connection1
        self.ssh_manager.connections["conn2"] = connection2
        
        # Cleanup all connections
        self.ssh_manager.cleanup_all_connections()
        
        # Verify all connections were cleaned up
        self.assertEqual(len(self.ssh_manager.connections), 0)
        mock_sftp1.close.assert_called_once()
        mock_client1.close.assert_called_once()
        mock_sftp2.close.assert_called_once()
        mock_client2.close.assert_called_once()


class TestCommandResult(unittest.TestCase):
    """Test cases for CommandResult."""
    
    def test_command_result_creation(self):
        """Test CommandResult creation."""
        result = CommandResult(
            command="ls -la",
            stdout="total 0\ndrwxr-xr-x 2 user user 4096 Jan 1 12:00 .",
            stderr="",
            exit_code=0,
            execution_time=0.5,
            success=True
        )
        
        self.assertEqual(result.command, "ls -la")
        self.assertIn("total 0", result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.execution_time, 0.5)
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main() 