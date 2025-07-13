#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { 
  MCPTool, 
  UserContext, 
  SSHTarget, 
  CommandResult,
  AuthenticationError,
  AuthorizationError,
  ValidationError,
  SSHError
} from './types/index.js';
import { logger } from './utils/logger.js';
import { serverConfig, validateConfig } from './config/index.js';

// Simple cache implementation for now
class SimpleCache {
  private cache = new Map<string, { value: any; expires: number }>();

  async get<T>(key: string): Promise<T | null> {
    const item = this.cache.get(key);
    if (item && item.expires > Date.now()) {
      return item.value;
    }
    this.cache.delete(key);
    return null;
  }

  async set<T>(key: string, value: T, ttlSeconds: number = 3600): Promise<void> {
    this.cache.set(key, {
      value,
      expires: Date.now() + (ttlSeconds * 1000)
    });
  }

  async delete(key: string): Promise<boolean> {
    return this.cache.delete(key);
  }

  async clear(): Promise<void> {
    this.cache.clear();
  }

  async stats() {
    return {
      hits: 0,
      misses: 0,
      hitRate: 0,
      size: this.cache.size,
      memoryUsage: 0
    };
  }
}

// Simple security service for now
class SimpleSecurityService {
  private cache: SimpleCache;

  constructor(cache: SimpleCache) {
    this.cache = cache;
  }

  async validateToken(token: string): Promise<UserContext> {
    // For demo purposes, accept any token and create a basic user context
    return {
      userId: 'demo-user',
      scopes: ['ssh:read', 'ssh:execute'],
      permissions: ['system:read', 'filesystem:read', 'network:read'],
      tokenExpiry: Math.floor(Date.now() / 1000) + 3600,
      metadata: { demo: true }
    };
  }

  async validateCommand(commandName: string, args: string[], userContext: UserContext) {
    // Basic validation - in production this would be much more comprehensive
    const allowedCommands = ['ls', 'ps', 'df', 'free', 'uptime', 'whoami', 'pwd'];
    
    if (!allowedCommands.includes(commandName)) {
      throw new ValidationError(`Command '${commandName}' is not allowed`);
    }

    return {
      command: [commandName],
      args: args.filter(arg => typeof arg === 'string' && arg.length < 100)
    };
  }

  sanitizeOutput(output: string): string {
    return output
      .replace(/password[=:]\s*\S+/gi, 'password=***')
      .replace(/token[=:]\s*\S+/gi, 'token=***')
      .replace(/key[=:]\s*\S+/gi, 'key=***');
  }

  async checkRateLimit(userId: string, action: string): Promise<void> {
    // Simple rate limiting
    const key = `rate_limit:${userId}:${action}`;
    const current = await this.cache.get<number>(key) || 0;
    
    if (current >= 100) {
      throw new AuthorizationError('Rate limit exceeded');
    }

    await this.cache.set(key, current + 1, 900); // 15 minutes
  }

  async auditLog(event: string, userContext: UserContext, details?: any): Promise<void> {
    logger.info('Security audit', { event, userId: userContext.userId, details });
  }
}

// Simple SSH service for demo
class SimpleSSHService {
  private targets = new Map<string, SSHTarget>();
  private securityService: SimpleSecurityService;

  constructor(securityService: SimpleSecurityService) {
    this.securityService = securityService;
  }

  async addTarget(target: SSHTarget): Promise<void> {
    this.targets.set(target.id, target);
    logger.info('SSH target added', { targetId: target.id });
  }

  async executeCommand(
    targetId: string,
    commandName: string,
    args: string[],
    userContext: UserContext
  ): Promise<CommandResult> {
    await this.securityService.checkRateLimit(userContext.userId, 'ssh_execute');
    await this.securityService.validateCommand(commandName, args, userContext);

    const target = this.targets.get(targetId);
    if (!target) {
      throw new SSHError('Target not found', { targetId });
    }

    // Simulate command execution
    const result: CommandResult = {
      success: true,
      stdout: `Simulated output for: ${commandName} ${args.join(' ')}`,
      stderr: '',
      exitCode: 0,
      executionTime: 100,
      timestamp: new Date(),
      sanitized: true
    };

    await this.securityService.auditLog('command_executed', userContext, {
      targetId,
      commandName,
      exitCode: result.exitCode
    });

    return result;
  }

  async listTargets(): Promise<SSHTarget[]> {
    return Array.from(this.targets.values());
  }
}

class SSHMCPServer {
  private server: Server;
  private cache: SimpleCache;
  private securityService: SimpleSecurityService;
  private sshService: SimpleSSHService;

  constructor() {
    this.server = new Server(
      {
        name: serverConfig.name,
        version: serverConfig.version,
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.cache = new SimpleCache();
    this.securityService = new SimpleSecurityService(this.cache);
    this.sshService = new SimpleSSHService(this.securityService);
    
    this.setupTools();
    this.setupErrorHandling();
  }

  private setupTools(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'ssh_connect',
            description: 'Connect to an SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                host: { type: 'string', description: 'SSH host' },
                port: { type: 'number', description: 'SSH port', default: 22 },
                username: { type: 'string', description: 'SSH username' },
                keyId: { type: 'string', description: 'SSH key identifier' }
              },
              required: ['host', 'username', 'keyId']
            }
          },
          {
            name: 'ssh_execute',
            description: 'Execute a command on an SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' },
                command: { type: 'string', description: 'Command to execute' },
                args: { 
                  type: 'array', 
                  items: { type: 'string' },
                  description: 'Command arguments' 
                }
              },
              required: ['targetId', 'command']
            }
          },
          {
            name: 'ssh_list_targets',
            description: 'List all SSH targets',
            inputSchema: {
              type: 'object',
              properties: {}
            }
          },
          {
            name: 'ssh_system_status',
            description: 'Get system status from SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' }
              },
              required: ['targetId']
            }
          },
          {
            name: 'ssh_disk_usage',
            description: 'Get disk usage from SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' }
              },
              required: ['targetId']
            }
          },
          {
            name: 'ssh_memory_info',
            description: 'Get memory information from SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' }
              },
              required: ['targetId']
            }
          },
          {
            name: 'ssh_process_list',
            description: 'List running processes on SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' }
              },
              required: ['targetId']
            }
          },
          {
            name: 'ssh_network_status',
            description: 'Get network status from SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' }
              },
              required: ['targetId']
            }
          },
          {
            name: 'ssh_uptime',
            description: 'Get system uptime from SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' }
              },
              required: ['targetId']
            }
          },
          {
            name: 'ssh_file_list',
            description: 'List files in directory on SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' },
                path: { type: 'string', description: 'Directory path', default: '.' }
              },
              required: ['targetId']
            }
          }
        ]
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        // Get user context from token (in real implementation)
        const userContext = await this.securityService.validateToken('demo-token');

        switch (name) {
          case 'ssh_connect':
            return await this.handleSSHConnect(args, userContext);
          case 'ssh_execute':
            return await this.handleSSHExecute(args, userContext);
          case 'ssh_list_targets':
            return await this.handleSSHListTargets(args, userContext);
          case 'ssh_system_status':
            return await this.handleSSHSystemStatus(args, userContext);
          case 'ssh_disk_usage':
            return await this.handleSSHDiskUsage(args, userContext);
          case 'ssh_memory_info':
            return await this.handleSSHMemoryInfo(args, userContext);
          case 'ssh_process_list':
            return await this.handleSSHProcessList(args, userContext);
          case 'ssh_network_status':
            return await this.handleSSHNetworkStatus(args, userContext);
          case 'ssh_uptime':
            return await this.handleSSHUptime(args, userContext);
          case 'ssh_file_list':
            return await this.handleSSHFileList(args, userContext);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        logger.error('Tool execution error', { tool: name, error: (error as Error).message });
        
        if (error instanceof AuthenticationError) {
          throw new McpError(ErrorCode.InvalidRequest, error.message);
        }
        if (error instanceof AuthorizationError) {
          throw new McpError(ErrorCode.InvalidRequest, error.message);
        }
        if (error instanceof ValidationError) {
          throw new McpError(ErrorCode.InvalidParams, error.message);
        }
        if (error instanceof SSHError) {
          throw new McpError(ErrorCode.InternalError, error.message);
        }
        
        throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${(error as Error).message}`);
      }
    });
  }

  private async handleSSHConnect(args: any, userContext: UserContext) {
    const { host, port = 22, username, keyId } = args;
    
    const target: SSHTarget = {
      id: `target_${Date.now()}`,
      host,
      port,
      username,
      keyId,
      description: `SSH target for ${host}`
    };

    await this.sshService.addTarget(target);

    return {
      content: [
        {
          type: 'text',
          text: `SSH target created successfully.\nTarget ID: ${target.id}\nHost: ${host}:${port}\nUsername: ${username}`
        }
      ]
    };
  }

  private async handleSSHExecute(args: any, userContext: UserContext) {
    const { targetId, command, args: commandArgs = [] } = args;
    
    const result = await this.sshService.executeCommand(targetId, command, commandArgs, userContext);
    
    return {
      content: [
        {
          type: 'text',
          text: `Command executed successfully.\n\nCommand: ${command} ${commandArgs.join(' ')}\nExit Code: ${result.exitCode}\nExecution Time: ${result.executionTime}ms\n\nOutput:\n${result.stdout}\n\nErrors:\n${result.stderr}`
        }
      ]
    };
  }

  private async handleSSHListTargets(args: any, userContext: UserContext) {
    const targets = await this.sshService.listTargets();
    
    const targetList = targets.map(target => 
      `ID: ${target.id}\nHost: ${target.host}:${target.port}\nUsername: ${target.username}\nDescription: ${target.description || 'N/A'}`
    ).join('\n\n');

    return {
      content: [
        {
          type: 'text',
          text: `SSH Targets (${targets.length}):\n\n${targetList || 'No targets configured'}`
        }
      ]
    };
  }

  private async handleSSHSystemStatus(args: any, userContext: UserContext) {
    const { targetId } = args;
    const result = await this.sshService.executeCommand(targetId, 'ps', ['aux'], userContext);
    
    return {
      content: [
        {
          type: 'text',
          text: `System Status for target ${targetId}:\n\n${result.stdout}`
        }
      ]
    };
  }

  private async handleSSHDiskUsage(args: any, userContext: UserContext) {
    const { targetId } = args;
    const result = await this.sshService.executeCommand(targetId, 'df', ['-h'], userContext);
    
    return {
      content: [
        {
          type: 'text',
          text: `Disk Usage for target ${targetId}:\n\n${result.stdout}`
        }
      ]
    };
  }

  private async handleSSHMemoryInfo(args: any, userContext: UserContext) {
    const { targetId } = args;
    const result = await this.sshService.executeCommand(targetId, 'free', ['-h'], userContext);
    
    return {
      content: [
        {
          type: 'text',
          text: `Memory Information for target ${targetId}:\n\n${result.stdout}`
        }
      ]
    };
  }

  private async handleSSHProcessList(args: any, userContext: UserContext) {
    const { targetId } = args;
    const result = await this.sshService.executeCommand(targetId, 'ps', ['aux'], userContext);
    
    return {
      content: [
        {
          type: 'text',
          text: `Process List for target ${targetId}:\n\n${result.stdout}`
        }
      ]
    };
  }

  private async handleSSHNetworkStatus(args: any, userContext: UserContext) {
    const { targetId } = args;
    const result = await this.sshService.executeCommand(targetId, 'ss', ['-tuln'], userContext);
    
    return {
      content: [
        {
          type: 'text',
          text: `Network Status for target ${targetId}:\n\n${result.stdout}`
        }
      ]
    };
  }

  private async handleSSHUptime(args: any, userContext: UserContext) {
    const { targetId } = args;
    const result = await this.sshService.executeCommand(targetId, 'uptime', [], userContext);
    
    return {
      content: [
        {
          type: 'text',
          text: `Uptime for target ${targetId}:\n\n${result.stdout}`
        }
      ]
    };
  }

  private async handleSSHFileList(args: any, userContext: UserContext) {
    const { targetId, path = '.' } = args;
    const result = await this.sshService.executeCommand(targetId, 'ls', ['-la', path], userContext);
    
    return {
      content: [
        {
          type: 'text',
          text: `File List for ${path} on target ${targetId}:\n\n${result.stdout}`
        }
      ]
    };
  }

  private setupErrorHandling(): void {
    this.server.onerror = (error) => {
      logger.error('MCP Server error', { error: error.message, stack: error.stack });
    };

    process.on('uncaughtException', (error) => {
      logger.error('Uncaught exception', { error: error.message, stack: error.stack });
      process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
      logger.error('Unhandled rejection', { reason, promise });
      process.exit(1);
    });

    process.on('SIGINT', async () => {
      logger.info('Received SIGINT, shutting down gracefully...');
      await this.shutdown();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      logger.info('Received SIGTERM, shutting down gracefully...');
      await this.shutdown();
      process.exit(0);
    });
  }

  async run(): Promise<void> {
    try {
      validateConfig();
      
      const transport = new StdioServerTransport();
      await this.server.connect(transport);
      
      logger.info('SSH MCP Server started', { 
        name: serverConfig.name, 
        version: serverConfig.version 
      });
      
    } catch (error) {
      logger.error('Failed to start server', { error: (error as Error).message });
      process.exit(1);
    }
  }

  async shutdown(): Promise<void> {
    try {
      logger.info('Shutting down SSH MCP Server...');
      await this.server.close();
      logger.info('SSH MCP Server shutdown complete');
    } catch (error) {
      logger.error('Error during shutdown', { error: (error as Error).message });
    }
  }
}

// Start the server
if (require.main === module) {
  const server = new SSHMCPServer();
  server.run().catch((error) => {
    logger.error('Failed to start SSH MCP Server', { error: error.message });
    process.exit(1);
  });
}

export default SSHMCPServer; 