#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { Client } from 'ssh2';

// Types for real SSH implementation
interface SSHTarget {
  id: string;
  host: string;
  port: number;
  username: string;
  password?: string;
  privateKey?: string;
  description?: string;
}

interface CommandResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exitCode: number;
  executionTime: number;
  timestamp: Date;
}

interface SSHConnection {
  id: string;
  target: SSHTarget;
  client: Client;
  isConnected: boolean;
  lastUsed: Date;
  createdAt: Date;
}

class RealSSHMCPServer {
  private server: Server;
  private targets = new Map<string, SSHTarget>();
  private connections = new Map<string, SSHConnection>();

  constructor() {
    this.server = new Server(
      {
        name: 'ssh-mcp-server-real',
        version: '2.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupTools();
    this.setupErrorHandling();
  }

  private setupTools(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'ssh_connect',
            description: 'Connect to an SSH target with password or key authentication',
            inputSchema: {
              type: 'object',
              properties: {
                host: { type: 'string', description: 'SSH host IP or hostname' },
                port: { type: 'number', description: 'SSH port', default: 22 },
                username: { type: 'string', description: 'SSH username' },
                password: { type: 'string', description: 'SSH password (optional if using key)' },
                privateKey: { type: 'string', description: 'SSH private key (optional if using password)' }
              },
              required: ['host', 'username']
            }
          },
          {
            name: 'ssh_execute',
            description: 'Execute a command on an SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' },
                command: { type: 'string', description: 'Command to execute' }
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
            name: 'ssh_disconnect',
            description: 'Disconnect from an SSH target',
            inputSchema: {
              type: 'object',
              properties: {
                targetId: { type: 'string', description: 'SSH target ID' }
              },
              required: ['targetId']
            }
          }
        ]
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'ssh_connect':
            return await this.handleSSHConnect(args);
          case 'ssh_execute':
            return await this.handleSSHExecute(args);
          case 'ssh_list_targets':
            return await this.handleSSHListTargets();
          case 'ssh_disconnect':
            return await this.handleSSHDisconnect(args);
          default:
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
        }
      } catch (error) {
        console.error('Tool execution error:', error);
        throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${(error as Error).message}`);
      }
    });
  }

  private async handleSSHConnect(args: any) {
    const { host, port = 22, username, password, privateKey } = args;
    
    if (!password && !privateKey) {
      throw new McpError(ErrorCode.InvalidParams, 'Either password or privateKey must be provided');
    }

    const target: SSHTarget = {
      id: `target_${Date.now()}`,
      host,
      port,
      username,
      password,
      privateKey,
      description: `SSH target for ${host}`
    };

    try {
      // Test the connection
      await this.connectToTarget(target);
      
      this.targets.set(target.id, target);

      return {
        content: [
          {
            type: 'text',
            text: `SSH connection successful!\n\nTarget ID: ${target.id}\nHost: ${host}:${port}\nUsername: ${username}\nStatus: Connected\n\nYou can now execute commands using ssh_execute with this target ID.`
          }
        ]
      };
    } catch (error) {
      throw new McpError(ErrorCode.InternalError, `SSH connection failed: ${(error as Error).message}`);
    }
  }

  private async connectToTarget(target: SSHTarget): Promise<SSHConnection> {
    return new Promise((resolve, reject) => {
      const client = new Client();
      const connection: SSHConnection = {
        id: `conn_${Date.now()}`,
        target,
        client,
        isConnected: false,
        lastUsed: new Date(),
        createdAt: new Date()
      };

      const timeout = setTimeout(() => {
        client.end();
        reject(new Error('Connection timeout after 30 seconds'));
      }, 30000);

      client.on('ready', () => {
        clearTimeout(timeout);
        connection.isConnected = true;
        connection.lastUsed = new Date();
        this.connections.set(target.id, connection);
        console.log(`SSH connection established to ${target.host}`);
        resolve(connection);
      });

      client.on('error', (error) => {
        clearTimeout(timeout);
        console.error(`SSH connection error to ${target.host}:`, error.message);
        reject(error);
      });

      client.on('close', () => {
        connection.isConnected = false;
        console.log(`SSH connection closed to ${target.host}`);
      });

      // Connect with provided credentials
      const connectConfig: any = {
        host: target.host,
        port: target.port,
        username: target.username,
        readyTimeout: 30000,
        keepaliveInterval: 60000,
      };

      if (target.password) {
        connectConfig.password = target.password;
      } else if (target.privateKey) {
        connectConfig.privateKey = target.privateKey;
      }

      client.connect(connectConfig);
    });
  }

  private async handleSSHExecute(args: any) {
    const { targetId, command } = args;
    
    const target = this.targets.get(targetId);
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }

    let connection = this.connections.get(targetId);
    
    // Reconnect if needed
    if (!connection || !connection.isConnected) {
      try {
        connection = await this.connectToTarget(target);
      } catch (error) {
        throw new McpError(ErrorCode.InternalError, `Failed to connect: ${(error as Error).message}`);
      }
    }

    try {
      const result = await this.executeCommand(connection, command);
      
      return {
        content: [
          {
            type: 'text',
            text: `Command executed on ${target.host}:\n\nCommand: ${command}\nExit Code: ${result.exitCode}\nExecution Time: ${result.executionTime}ms\n\n=== STDOUT ===\n${result.stdout}\n\n=== STDERR ===\n${result.stderr || 'None'}\n\n=== STATUS ===\n${result.success ? '✅ Success' : '❌ Failed'}`
          }
        ]
      };
    } catch (error) {
      throw new McpError(ErrorCode.InternalError, `Command execution failed: ${(error as Error).message}`);
    }
  }

  private async executeCommand(connection: SSHConnection, command: string): Promise<CommandResult> {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      const timeout = setTimeout(() => {
        reject(new Error('Command execution timeout after 60 seconds'));
      }, 60000);

      connection.client.exec(command, (err, stream) => {
        if (err) {
          clearTimeout(timeout);
          reject(err);
          return;
        }

        let stdout = '';
        let stderr = '';
        let exitCode = 0;

        stream.on('close', (code: number) => {
          clearTimeout(timeout);
          const executionTime = Date.now() - startTime;
          connection.lastUsed = new Date();

          const result: CommandResult = {
            success: code === 0,
            stdout,
            stderr,
            exitCode: code,
            executionTime,
            timestamp: new Date(),
          };

          console.log(`Command executed on ${connection.target.host}: ${command} (exit code: ${code})`);
          resolve(result);
        });

        stream.on('data', (data: Buffer) => {
          stdout += data.toString();
        });

        stream.stderr.on('data', (data: Buffer) => {
          stderr += data.toString();
        });

        stream.on('error', (error: Error) => {
          clearTimeout(timeout);
          reject(error);
        });
      });
    });
  }

  private async handleSSHListTargets() {
    const targets = Array.from(this.targets.values());
    const connections = Array.from(this.connections.values());
    
    const targetList = targets.map(target => {
      const conn = connections.find(c => c.target.id === target.id);
      const status = conn?.isConnected ? '🟢 Connected' : '🔴 Disconnected';
      
      return `ID: ${target.id}\nHost: ${target.host}:${target.port}\nUsername: ${target.username}\nStatus: ${status}\nDescription: ${target.description || 'N/A'}`;
    }).join('\n\n');

    return {
      content: [
        {
          type: 'text',
          text: `SSH Targets (${targets.length}):\n\n${targetList || 'No targets configured'}`
        }
      ]
    };
  }

  private async handleSSHDisconnect(args: any) {
    const { targetId } = args;
    
    const target = this.targets.get(targetId);
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }

    const connection = this.connections.get(targetId);
    if (connection && connection.isConnected) {
      connection.client.end();
      connection.isConnected = false;
    }

    this.connections.delete(targetId);
    this.targets.delete(targetId);

    return {
      content: [
        {
          type: 'text',
          text: `SSH target ${targetId} disconnected and removed.\nHost: ${target.host}:${target.port}`
        }
      ]
    };
  }

  private setupErrorHandling(): void {
    this.server.onerror = (error) => {
      console.error('MCP Server error:', error);
    };

    process.on('uncaughtException', (error) => {
      console.error('Uncaught exception:', error);
      process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
      console.error('Unhandled rejection:', reason);
      process.exit(1);
    });

    process.on('SIGINT', async () => {
      console.log('Received SIGINT, shutting down gracefully...');
      await this.shutdown();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      console.log('Received SIGTERM, shutting down gracefully...');
      await this.shutdown();
      process.exit(0);
    });
  }

  async run(): Promise<void> {
    try {
      const transport = new StdioServerTransport();
      await this.server.connect(transport);
      
      console.log('Real SSH MCP Server v2.0 started successfully');
      
    } catch (error) {
      console.error('Failed to start server:', error);
      process.exit(1);
    }
  }

  async shutdown(): Promise<void> {
    try {
      console.log('Shutting down SSH MCP Server...');
      
      // Close all SSH connections
      for (const connection of this.connections.values()) {
        if (connection.isConnected) {
          connection.client.end();
        }
      }
      
      await this.server.close();
      console.log('SSH MCP Server shutdown complete');
    } catch (error) {
      console.error('Error during shutdown:', error);
    }
  }
}

// Start the server
if (require.main === module) {
  const server = new RealSSHMCPServer();
  server.run().catch((error) => {
    console.error('Failed to start SSH MCP Server:', error);
    process.exit(1);
  });
}

export default RealSSHMCPServer; 