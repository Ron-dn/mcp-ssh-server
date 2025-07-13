# SSH MCP Server v2.0

A production-ready SSH Model Context Protocol (MCP) server that provides secure, scalable SSH automation capabilities for AI applications.

## 🚀 Features

### Core Capabilities
- **10 SSH Tools**: Complete SSH automation toolkit
- **Enterprise Security**: OAuth 2.1 authentication, input validation, output sanitization
- **High Performance**: Connection pooling, multi-level caching, optimized for concurrent operations
- **Production Ready**: Comprehensive monitoring, logging, error handling, and graceful shutdown

### Security Features
- OAuth 2.1 token introspection
- Command whitelist with argument validation
- Input sanitization and output filtering
- Rate limiting and audit logging
- HashiCorp Vault integration for SSH key management
- Comprehensive security event logging

### Performance Optimizations
- Connection pooling with health checks
- Multi-level caching (L1: in-memory, L2: Redis)
- Optimized for concurrent SSH operations
- Resource management and cleanup
- Metrics and observability

## 📋 Prerequisites

- Node.js 18+ and npm 9+
- TypeScript 5.2+
- Redis (for caching)
- PostgreSQL (for metadata storage)
- HashiCorp Vault (for SSH key management)
- OAuth 2.1 provider (for authentication)

## 🛠 Installation

1. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd mcp-ssh-2
   npm install
   ```

2. **Configuration**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Build**
   ```bash
   npm run build
   ```

4. **Start**
   ```bash
   npm start
   ```

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

#### Required Variables
- `OAUTH_ISSUER_URL`: OAuth 2.1 provider URL
- `OAUTH_CLIENT_ID`: OAuth client ID
- `OAUTH_CLIENT_SECRET`: OAuth client secret
- `OAUTH_INTROSPECTION_ENDPOINT`: Token introspection endpoint
- `DB_PASSWORD`: PostgreSQL password
- `VAULT_ENDPOINT`: HashiCorp Vault URL
- `VAULT_TOKEN`: Vault authentication token
- `JWT_SECRET`: JWT signing secret

#### Optional Variables
See `env.example` for complete list with defaults.

### MCP Client Configuration

Add to your MCP client configuration (e.g., `~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "ssh-v2": {
      "command": "node",
      "args": ["/path/to/mcp-ssh-2/dist/server.js"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```

## 🔑 SSH Tools

### 1. ssh_connect
Connect to an SSH target and add it to the pool.

```json
{
  "name": "ssh_connect",
  "arguments": {
    "host": "example.com",
    "port": 22,
    "username": "admin",
    "keyId": "vault-key-id"
  }
}
```

### 2. ssh_execute
Execute arbitrary commands on SSH targets.

```json
{
  "name": "ssh_execute",
  "arguments": {
    "targetId": "target_123456789",
    "command": "ls",
    "args": ["-la", "/home"]
  }
}
```

### 3. ssh_list_targets
List all configured SSH targets.

```json
{
  "name": "ssh_list_targets",
  "arguments": {}
}
```

### 4. ssh_system_status
Get system status information.

```json
{
  "name": "ssh_system_status",
  "arguments": {
    "targetId": "target_123456789"
  }
}
```

### 5. ssh_disk_usage
Check disk usage across filesystems.

```json
{
  "name": "ssh_disk_usage",
  "arguments": {
    "targetId": "target_123456789"
  }
}
```

### 6. ssh_memory_info
Get memory usage information.

```json
{
  "name": "ssh_memory_info",
  "arguments": {
    "targetId": "target_123456789"
  }
}
```

### 7. ssh_process_list
List running processes.

```json
{
  "name": "ssh_process_list",
  "arguments": {
    "targetId": "target_123456789"
  }
}
```

### 8. ssh_network_status
Check network connections and listening ports.

```json
{
  "name": "ssh_network_status",
  "arguments": {
    "targetId": "target_123456789"
  }
}
```

### 9. ssh_uptime
Get system uptime and load information.

```json
{
  "name": "ssh_uptime",
  "arguments": {
    "targetId": "target_123456789"
  }
}
```

### 10. ssh_file_list
List files and directories.

```json
{
  "name": "ssh_file_list",
  "arguments": {
    "targetId": "target_123456789",
    "path": "/var/log"
  }
}
```

## 🔒 Security Model

### Authentication Flow
1. Client provides OAuth 2.1 token
2. Server validates token via introspection
3. Token cached for performance
4. User context created with scopes/permissions

### Authorization
- Scope-based permissions (`ssh:read`, `ssh:execute`, etc.)
- Command whitelist with argument validation
- Rate limiting per user/action
- Audit logging for all operations

### Input Validation
- Command whitelist enforcement
- Argument sanitization
- Length limits and pattern matching
- Dangerous character detection

### Output Sanitization
- Credential scrubbing (passwords, tokens, keys)
- Configurable output filters
- Size limits to prevent memory issues

## 📊 Monitoring

### Health Checks
- `/health` - Basic health status
- `/ready` - Readiness probe for K8s
- `/metrics` - Prometheus metrics

### Metrics Collected
- Request/response times
- Error rates by type
- Connection pool statistics
- Cache hit/miss ratios
- Security events

### Logging
- Structured JSON logging
- Security audit trail
- Performance metrics
- Error tracking with context

## 🚀 Deployment

### Docker
```bash
npm run docker:build
npm run docker:run
```

### Kubernetes
See `k8s/` directory for deployment manifests.

### Production Considerations
- Use environment-specific configurations
- Enable TLS termination at load balancer
- Configure proper log aggregation
- Set up monitoring and alerting
- Implement backup strategies for Redis/PostgreSQL

## 🧪 Development

### Scripts
- `npm run dev` - Development with hot reload
- `npm run build` - Production build
- `npm run test` - Run tests
- `npm run test:coverage` - Test coverage
- `npm run lint` - ESLint
- `npm run format` - Prettier

### Testing
```bash
npm test
npm run test:watch
npm run test:coverage
```

## 🔧 Troubleshooting

### Common Issues

1. **Connection Failures**
   - Check SSH key permissions in Vault
   - Verify network connectivity
   - Review connection pool settings

2. **Authentication Errors**
   - Validate OAuth configuration
   - Check token introspection endpoint
   - Verify required scopes

3. **Performance Issues**
   - Monitor connection pool metrics
   - Check Redis cache performance
   - Review rate limiting settings

### Debug Mode
```bash
LOG_LEVEL=debug npm start
```

## 📚 Architecture

### Components
- **MCP Server**: Core protocol implementation
- **Security Service**: Authentication and authorization
- **SSH Service**: Connection management and command execution
- **Cache Manager**: Multi-level caching strategy
- **Connection Pool**: Optimized SSH connection reuse

### Data Flow
1. MCP client sends tool request
2. Server validates OAuth token
3. Security service authorizes command
4. SSH service executes via connection pool
5. Output sanitized and returned
6. Audit event logged

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

- Create an issue for bug reports
- Use discussions for questions
- Check troubleshooting guide first

---

**Built with security and performance in mind for production AI workloads.** 