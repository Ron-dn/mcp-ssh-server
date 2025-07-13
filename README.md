# SSH MCP Server v2.0

A working SSH Model Context Protocol (MCP) server that provides real SSH automation capabilities for AI applications.

## 🚀 Features

- **4 Real SSH Tools**: Connect, execute, list, and disconnect
- **Dual Authentication**: Password and private key support
- **Persistent Connections**: Maintains SSH connection state
- **Real SSH Implementation**: Actually connects to SSH devices (not simulated)
- **TypeScript**: Full type safety and modern implementation
- **Tested**: Verified working with real SSH devices

## 📋 Prerequisites

- Node.js 18+
- npm or yarn
- SSH access to target devices

## 🛠 Quick Start

1. **Clone and Install**
   ```bash
   git clone https://github.com/Ron-dn/mcp-ssh-server.git
   cd mcp-ssh-server
   git checkout mcp-server-v2
   npm install
   ```

2. **Build**
   ```bash
   npm run build
   ```

3. **Configure Cursor IDE**
   Add to your `~/.cursor/mcp.json`:
   ```json
   {
     "mcpServers": {
       "ssh-real": {
         "command": "node",
         "args": ["/path/to/your/project/dist/real-ssh-server.js"],
         "env": {
           "NODE_ENV": "production"
         }
       }
     }
   }
   ```

4. **Restart Cursor** to load the new MCP server

## 🔑 Available SSH Tools

### 1. `ssh_connect` 🔌
Connect to an SSH target with authentication.

**Parameters:**
- `host` (required): SSH host IP or hostname
- `username` (required): SSH username  
- `port` (optional): SSH port (default: 22)
- `password` (optional): SSH password
- `privateKey` (optional): SSH private key content

**Example:**
```json
{
  "host": "192.168.1.100",
  "username": "admin",
  "password": "your-password"
}
```

### 2. `ssh_execute` ⚡
Execute commands on connected SSH targets.

**Parameters:**
- `targetId` (required): SSH target ID from connection
- `command` (required): Command to execute

**Returns:** stdout, stderr, exit code, execution time

**Example:**
```json
{
  "targetId": "target_123456789",
  "command": "ls -la"
}
```

### 3. `ssh_list_targets` 📋
List all SSH targets and their connection status.

**Parameters:** None

**Returns:** All configured SSH targets with connection details

### 4. `ssh_disconnect` 🔌❌
Disconnect from an SSH target.

**Parameters:**
- `targetId` (required): SSH target ID to disconnect

**Example:**
```json
{
  "targetId": "target_123456789"
}
```

## 🎯 Usage Example

1. **Connect to SSH device:**
   ```
   Use ssh_connect with your device credentials
   ```

2. **Execute commands:**
   ```
   Use ssh_execute with the returned targetId
   ```

3. **List connections:**
   ```
   Use ssh_list_targets to see all active connections
   ```

4. **Clean disconnect:**
   ```
   Use ssh_disconnect when done
   ```

## ✅ Tested Devices

This server has been successfully tested with:
- Linux servers
- Network devices with SSH interfaces
- Custom SSH implementations

## 🔧 Development

### Build from Source
```bash
npm install
npm run build
```

### File Structure
```
src/
├── real-ssh-server.ts    # Main SSH MCP server (4 tools)
├── simple-server.ts      # Demo server (10 simulated tools)
└── server.ts            # Full production architecture
```

### Available Servers
- **`real-ssh-server.ts`**: ✅ **Current working implementation** (4 tools)
- **`simple-server.ts`**: Demo with simulated responses (10 tools)
- **`server.ts`**: Future production architecture (enterprise features)

## 🚨 Important Notes

- **Real SSH**: This server actually connects to SSH devices (unlike other MCP SSH servers that only store credentials)
- **Security**: Remove sensitive data from code before committing
- **Connections**: Server maintains persistent SSH connections for performance
- **Error Handling**: Proper SSH error reporting and connection management

## 🆚 Comparison with Other SSH MCP Servers

| Feature | This Server | Others |
|---------|-------------|---------|
| Real SSH Connection | ✅ Yes | ❌ No (credential storage only) |
| Command Execution | ✅ Yes | ❌ Simulated |
| Authentication Options | ✅ Password + Key | 🔶 Key only |
| Connection Management | ✅ Persistent | ❌ One-time |
| Tested with Real Devices | ✅ Yes | ❌ No |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Troubleshooting

### SSH Tools Not Appearing in Cursor
1. Ensure the server path in `mcp.json` is correct
2. Restart Cursor completely (not just reload)
3. Check that `dist/real-ssh-server.js` exists
4. Verify Node.js can run the server: `node dist/real-ssh-server.js`

### Connection Issues
1. Verify SSH credentials are correct
2. Check network connectivity to target host
3. Ensure SSH service is running on target
4. Check firewall settings

### Command Execution Problems
1. Some devices have proprietary command sets
2. Try basic commands first (`ls`, `pwd`, `whoami`)
3. Check device documentation for supported commands

---

**Built for real SSH automation - the only MCP SSH server that actually works with SSH devices!** 🎯 