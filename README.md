# MCP SSH Server

A powerful, generic SSH MCP server that provides secure remote system access through the Model Context Protocol. Perfect for system administration, network device management, and automation tasks.

## 🚀 Features

- 🔐 **Secure SSH connections** with runtime credentials (no storage)
- 💻 **Command execution** (single, interactive, multi-command)
- 📁 **File operations** (upload, download, directory listing)
- 🌐 **Universal compatibility** (Linux, Unix, network devices, routers, switches)
- 🔧 **SSH tunneling** and port forwarding
- 🛡️ **Security-first design** with session-based authentication
- ⚡ **High performance** with connection pooling and async operations
- 🎯 **Easy integration** with any MCP-compatible client

## 📦 Installation

### Via pip (Recommended)
```bash
pip install mcp-ssh-server
```

### From source
```bash
git clone https://github.com/yourusername/mcp-ssh-server.git
cd mcp-ssh-server
pip install -e .
```

## ⚙️ Configuration

Add to your MCP client configuration:

### Claude Desktop
```json
{
  "mcpServers": {
    "ssh": {
      "command": "mcp-ssh-server",
      "args": []
    }
  }
}
```

### Other MCP Clients
```bash
mcp-ssh-server
```

## 🔧 Available Tools

### Connection Management
- `mcp_ssh_connect` - Establish SSH connection
- `mcp_ssh_disconnect` - Close connection
- `mcp_ssh_list_connections` - List active connections
- `mcp_ssh_test_connection` - Test connection health

### Command Execution
- `mcp_ssh_execute` - Execute single command
- `mcp_ssh_execute_interactive` - Handle interactive prompts
- `mcp_ssh_execute_multi` - Run multiple commands

### File Operations
- `mcp_ssh_upload` - Upload files/directories
- `mcp_ssh_download` - Download files/directories
- `mcp_ssh_list_directory` - List remote directory contents

### Utilities
- `mcp_ssh_check_file_exists` - Check if file exists
- `mcp_ssh_get_system_info` - Get system information
- `mcp_ssh_create_tunnel` - Create SSH tunnel
- `mcp_ssh_close_tunnel` - Close SSH tunnel

### Security
- `mcp_ssh_change_password` - Change user password
- `mcp_ssh_add_public_key` - Add SSH public key

## 💡 Usage Examples

### Basic Usage
```python
# Connect to server
conn_id = mcp_ssh_connect(
    host="server.example.com",
    username="admin",
    password="your_password"
)

# Execute command
result = mcp_ssh_execute(
    connection_id=conn_id,
    command="ls -la /home"
)

# Upload file
mcp_ssh_upload(
    connection_id=conn_id,
    local_path="./config.txt",
    remote_path="/tmp/config.txt"
)

# Disconnect
mcp_ssh_disconnect(conn_id)
```

### Network Device Automation
```python
# Connect to network switch
switch_conn = mcp_ssh_connect(
    host="switch.example.com",
    username="admin",
    password="your_password"
)

# Check interface status
interface_status = mcp_ssh_execute(
    connection_id=switch_conn,
    command="show interface GigabitEthernet0/1 status"
)

# Configure interface
mcp_ssh_execute_interactive(
    connection_id=switch_conn,
    command="configure terminal",
    expect_prompts=["(config)#"],
    responses=["interface GigabitEthernet0/1"]
)
```

### Bulk Operations
```python
# Connect to multiple servers
servers = [
    {"host": "web1.example.com", "username": "deploy", "password": "pass1"},
    {"host": "web2.example.com", "username": "deploy", "password": "pass2"},
    {"host": "web3.example.com", "username": "deploy", "password": "pass3"}
]

connections = []
for server in servers:
    conn_id = mcp_ssh_connect(**server)
    connections.append(conn_id)

# Deploy to all servers
for conn_id in connections:
    mcp_ssh_execute_multi(
        connection_id=conn_id,
        commands=[
            "cd /var/www/html",
            "git pull origin main",
            "sudo systemctl restart nginx"
        ]
    )
```

### File Management
```python
# Download logs from server
mcp_ssh_download(
    connection_id=conn_id,
    remote_path="/var/log/application.log",
    local_path="./logs/app.log"
)

# Upload configuration
mcp_ssh_upload(
    connection_id=conn_id,
    local_path="./configs/",
    remote_path="/etc/myapp/",
    recursive=True
)
```

### SSH Tunneling
```python
# Create tunnel for database access
tunnel_id = mcp_ssh_create_tunnel(
    connection_id=conn_id,
    local_port=5432,
    remote_host="db.internal.com",
    remote_port=5432
)

# Now connect to localhost:5432 to access remote database
```

## 🔐 Security Features

- **No credential storage** - All authentication data is runtime-only
- **Session-based security** - Connections exist only during MCP session
- **Host key verification** - Protects against man-in-the-middle attacks
- **Timeout management** - Prevents hanging connections
- **Secure file transfers** - Uses SFTP/SCP protocols
- **Memory-only operations** - No sensitive data written to disk

## 🚀 Performance

- **Connection pooling** - Reuse connections for better performance
- **Async operations** - Non-blocking command execution
- **Efficient file transfers** - Optimized for large files
- **Resource management** - Automatic cleanup of resources

## 🛠️ Development

### Requirements
- Python 3.8+
- paramiko
- asyncio support

### Running Tests
```bash
pytest tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/mcp-ssh-server/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/mcp-ssh-server/discussions)
- 📖 **Documentation**: [Wiki](https://github.com/yourusername/mcp-ssh-server/wiki)

## 🙏 Acknowledgments

Built with:
- [Paramiko](https://github.com/paramiko/paramiko) - SSH implementation
- [MCP](https://github.com/modelcontextprotocol/python-sdk) - Model Context Protocol
- [asyncio](https://docs.python.org/3/library/asyncio.html) - Async support

---

**Made with ❤️ for the MCP community** 