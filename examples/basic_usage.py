#!/usr/bin/env python3
"""
Basic Usage Examples for MCP SSH Server

This module demonstrates the fundamental operations available through the MCP SSH server.
All examples use generic hostnames and credentials for demonstration purposes.
"""

import json


def main():
    """
    Basic examples of MCP SSH server usage.
    These examples show the core functionality for SSH operations.
    """
    
    print("🔧 MCP SSH Server - Basic Usage Examples\n")
    print("=" * 50)
    
    # Example 1: Basic connection
    print("1. Basic SSH Connection:")
    connection_request = {
        "tool": "mcp_ssh_connect",
        "arguments": {
            "host": "server.example.com",
            "username": "user",
            "password": "your_password_here",
            "port": 22,
            "timeout": 30
        }
    }
    print(json.dumps(connection_request, indent=2))
    
    # Simulated response
    connection_id = "ssh_abc123_server.example.com_user"
    print(f"✓ Connected with ID: {connection_id}\n")
    
    # Example 2: Execute single command
    print("2. Execute Single Command:")
    single_command = {
        "tool": "mcp_ssh_execute",
        "arguments": {
            "connection_id": connection_id,
            "command": "ls -la /home/user",
            "timeout": 10
        }
    }
    print(json.dumps(single_command, indent=2))
    print("✓ Command executed\n")
    
    # Example 3: Execute multiple commands
    print("3. Execute Multiple Commands:")
    multi_commands = {
        "tool": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": connection_id,
            "commands": [
                "whoami",
                "pwd",
                "date",
                "uptime"
            ],
            "timeout": 15
        }
    }
    print(json.dumps(multi_commands, indent=2))
    print("✓ Multiple commands executed\n")
    
    # Example 4: Interactive command execution
    print("4. Interactive Command Execution:")
    interactive_command = {
        "tool": "mcp_ssh_execute_interactive",
        "arguments": {
            "connection_id": connection_id,
            "command": "sudo systemctl status nginx",
            "expect_patterns": ["password", "Active:", "inactive"],
            "timeout": 20
        }
    }
    print(json.dumps(interactive_command, indent=2))
    print("✓ Interactive command executed\n")
    
    # Example 5: File upload
    print("5. Upload File:")
    upload_file = {
        "tool": "mcp_ssh_upload",
        "arguments": {
            "connection_id": connection_id,
            "local_path": "/local/path/config.txt",
            "remote_path": "/remote/path/config.txt",
            "recursive": False
        }
    }
    print(json.dumps(upload_file, indent=2))
    print("✓ File uploaded\n")
    
    # Example 6: Directory upload (recursive)
    print("6. Upload Directory (Recursive):")
    upload_directory = {
        "tool": "mcp_ssh_upload",
        "arguments": {
            "connection_id": connection_id,
            "local_path": "/local/project",
            "remote_path": "/remote/project",
            "recursive": True
        }
    }
    print(json.dumps(upload_directory, indent=2))
    print("✓ Directory uploaded\n")
    
    # Example 7: File download
    print("7. Download File:")
    download_file = {
        "tool": "mcp_ssh_download",
        "arguments": {
            "connection_id": connection_id,
            "remote_path": "/var/log/application.log",
            "local_path": "/local/logs/application.log",
            "recursive": False
        }
    }
    print(json.dumps(download_file, indent=2))
    print("✓ File downloaded\n")
    
    # Example 8: List remote directory
    print("8. List Remote Directory:")
    list_directory = {
        "tool": "mcp_ssh_list_directory",
        "arguments": {
            "connection_id": connection_id,
            "path": "/home/user",
            "detailed": True
        }
    }
    print(json.dumps(list_directory, indent=2))
    print("✓ Directory listed\n")
    
    # Example 9: Check if file exists
    print("9. Check File Existence:")
    check_file = {
        "tool": "mcp_ssh_check_file_exists",
        "arguments": {
            "connection_id": connection_id,
            "path": "/etc/nginx/nginx.conf"
        }
    }
    print(json.dumps(check_file, indent=2))
    print("✓ File existence checked\n")
    
    # Example 10: Get system information
    print("10. Get System Information:")
    system_info = {
        "tool": "mcp_ssh_get_system_info",
        "arguments": {
            "connection_id": connection_id
        }
    }
    print(json.dumps(system_info, indent=2))
    print("✓ System information retrieved\n")
    
    # Example 11: Get command history
    print("11. Get Command History:")
    command_history = {
        "tool": "mcp_ssh_get_command_history",
        "arguments": {
            "connection_id": connection_id,
            "limit": 10
        }
    }
    print(json.dumps(command_history, indent=2))
    print("✓ Command history retrieved\n")
    
    # Example 12: Test connection health
    print("12. Test Connection Health:")
    test_connection = {
        "tool": "mcp_ssh_test_connection",
        "arguments": {
            "connection_id": connection_id
        }
    }
    print(json.dumps(test_connection, indent=2))
    print("✓ Connection tested\n")
    
    # Example 13: List all connections
    print("13. List All Active Connections:")
    list_connections = {
        "tool": "mcp_ssh_list_connections",
        "arguments": {}
    }
    print(json.dumps(list_connections, indent=2))
    print("✓ Active connections listed\n")
    
    # Example 14: Disconnect
    print("14. Disconnect from Server:")
    disconnect = {
        "tool": "mcp_ssh_disconnect",
        "arguments": {
            "connection_id": connection_id
        }
    }
    print(json.dumps(disconnect, indent=2))
    print("✓ Disconnected\n")
    
    print("=" * 50)
    print("🎯 Basic Usage Examples Complete!")
    print("\nThese examples demonstrate:")
    print("• SSH connection management")
    print("• Command execution (single, multiple, interactive)")
    print("• File and directory operations")
    print("• System information gathering")
    print("• Connection health monitoring")


if __name__ == "__main__":
    main() 