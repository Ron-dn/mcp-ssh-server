# SSH MCP Server v2 - Deployment Guide

## 🚀 Quick Start (Demo Version)

The simplified SSH MCP Server v2 is ready to deploy and test immediately.

### Prerequisites
- Node.js 18+ installed
- Access to modify MCP client configuration

### 1. Build the Server
```bash
# In the Test_UI directory
npx tsc src/simple-server.ts --outDir dist --target ES2022 --module commonjs --moduleResolution node --esModuleInterop --skipLibCheck
```

### 2. Verify Build
```bash
ls -la dist/simple-server.js
# Should show the compiled server file
```

### 3. Configure MCP Client

Add to your MCP client configuration (e.g., `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "ssh-v2": {
      "command": "node",
      "args": ["/Users/ronmiretsky/MyProjects/Test_UI/dist/simple-server.js"],
      "env": {
        "NODE_ENV": "development"
      }
    }
  }
}
```

**Important**: Replace `/Users/ronmiretsky/MyProjects/Test_UI/` with your actual project path.

### 4. Restart MCP Client
- Completely quit and restart Cursor (Cmd+Q, then reopen)
- The SSH tools should now be available

## 🔧 Available Tools

### Core SSH Tools (10 total):

1. **ssh_connect** - Connect to SSH targets
2. **ssh_execute** - Execute commands
3. **ssh_list_targets** - List configured targets
4. **ssh_system_status** - Get system status
5. **ssh_disk_usage** - Check disk usage
6. **ssh_memory_info** - Memory information
7. **ssh_process_list** - Running processes
8. **ssh_network_status** - Network connections
9. **ssh_uptime** - System uptime
10. **ssh_file_list** - List files/directories

## 📝 Usage Examples

### Connect to a Server
```json
{
  "tool": "ssh_connect",
  "arguments": {
    "host": "example.com",
    "port": 22,
    "username": "admin",
    "keyId": "my-key"
  }
}
```

### Execute Commands
```json
{
  "tool": "ssh_execute",
  "arguments": {
    "targetId": "target_1234567890",
    "command": "ls",
    "args": ["-la", "/home"]
  }
}
```

### Check System Status
```json
{
  "tool": "ssh_system_status",
  "arguments": {
    "targetId": "target_1234567890"
  }
}
```

## ⚠️ Current Limitations (Demo Version)

This is a **demonstration version** with simulated outputs:

- **No Real SSH Connections**: Commands return simulated data
- **No Authentication**: Uses demo user context
- **No Security Validation**: Basic input validation only
- **No Persistence**: Targets are stored in memory only

## 🏗 Production Deployment

For production use, you'll need to implement:

### 1. Real SSH Integration
- Replace simulated execution with actual SSH connections
- Implement connection pooling
- Add proper error handling

### 2. Security Framework
- OAuth 2.1 authentication
- Command whitelisting
- Input/output sanitization
- Rate limiting

### 3. Infrastructure Components
- Redis for caching
- PostgreSQL for metadata
- HashiCorp Vault for SSH keys
- Monitoring and logging

### 4. Configuration Management
```bash
cp env.example .env
# Configure all required environment variables
```

### 5. Full Build Process
```bash
npm install
npm run build
npm start
```

## 🔍 Troubleshooting

### Server Won't Start
1. Check Node.js version: `node --version` (need 18+)
2. Verify compilation: `ls -la dist/simple-server.js`
3. Test import: `node -e "import('./dist/simple-server.js')"`

### Tools Not Available in MCP Client
1. Verify MCP configuration path is correct
2. Restart MCP client completely (Cmd+Q and reopen)
3. Check client logs for connection errors

### Permission Errors
1. Ensure executable permissions: `chmod +x dist/simple-server.js`
2. Check file ownership and paths

## 📊 Architecture Overview

```
MCP Client (Cursor)
    ↓
SSH MCP Server v2
    ↓
Simulated SSH Targets
```

### Production Architecture
```
MCP Client
    ↓
SSH MCP Server v2
    ↓
[Security Layer] → [Connection Pool] → [Real SSH Targets]
    ↓                    ↓
[Cache Layer]      [Monitoring]
    ↓                    ↓
[Redis]            [Metrics/Logs]
```

## 🎯 Next Steps

1. **Test the Demo**: Use the simplified version to understand the tool capabilities
2. **Plan Production**: Review the full architecture in the main README
3. **Implement Security**: Add OAuth 2.1 and proper validation
4. **Add Real SSH**: Replace simulation with actual SSH connections
5. **Deploy Infrastructure**: Set up Redis, PostgreSQL, Vault
6. **Monitor & Scale**: Add observability and scaling capabilities

## 📞 Support

- Check logs in the MCP client for connection issues
- Verify all file paths are absolute and correct
- Ensure Node.js and npm versions meet requirements
- Test server compilation before configuring MCP client

---

**Ready to revolutionize your SSH automation with AI! 🚀** 