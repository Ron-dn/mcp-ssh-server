#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';

// Simple types for the demo
interface SSHTarget {
  id: string;
  host: string;
  port: number;
  username: string;
  keyId: string;
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

interface UserContext {
  userId: string;
  scopes: string[];
  permissions: string[];
}

class SimpleSSHMCPServer {
  private server: Server;
  private targets = new Map<string, SSHTarget>();

  constructor() {
    this.server = new Server(
      {
        name: 'ssh-mcp-server-v2',
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

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        // Simple user context for demo
        const userContext: UserContext = {
          userId: 'demo-user',
          scopes: ['ssh:read', 'ssh:execute'],
          permissions: ['system:read', 'filesystem:read']
        };

        switch (name) {
          case 'ssh_connect':
            return await this.handleSSHConnect(args);
          case 'ssh_execute':
            return await this.handleSSHExecute(args);
          case 'ssh_list_targets':
            return await this.handleSSHListTargets();
          case 'ssh_system_status':
            return await this.handleSSHSystemStatus(args);
          case 'ssh_disk_usage':
            return await this.handleSSHDiskUsage(args);
          case 'ssh_memory_info':
            return await this.handleSSHMemoryInfo(args);
          case 'ssh_process_list':
            return await this.handleSSHProcessList(args);
          case 'ssh_network_status':
            return await this.handleSSHNetworkStatus(args);
          case 'ssh_uptime':
            return await this.handleSSHUptime(args);
          case 'ssh_file_list':
            return await this.handleSSHFileList(args);
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
    const { host, port = 22, username, keyId } = args;
    
    const target: SSHTarget = {
      id: `target_${Date.now()}`,
      host,
      port,
      username,
      keyId,
      description: `SSH target for ${host}`
    };

    this.targets.set(target.id, target);

    return {
      content: [
        {
          type: 'text',
          text: `SSH target created successfully.\n\nTarget ID: ${target.id}\nHost: ${host}:${port}\nUsername: ${username}\n\nNote: This is a demo implementation. In production, this would establish a real SSH connection using the provided credentials.`
        }
      ]
    };
  }

  private async handleSSHExecute(args: any) {
    const { targetId, command, args: commandArgs = [] } = args;
    
    const target = this.targets.get(targetId);
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }

    // Simulate command execution
    const result: CommandResult = {
      success: true,
      stdout: `Demo output for: ${command} ${commandArgs.join(' ')}\n\nThis is simulated output. In production, this would execute the actual command on ${target.host}.`,
      stderr: '',
      exitCode: 0,
      executionTime: 150,
      timestamp: new Date()
    };
    
    return {
      content: [
        {
          type: 'text',
          text: `Command executed on ${target.host}:\n\nCommand: ${command} ${commandArgs.join(' ')}\nExit Code: ${result.exitCode}\nExecution Time: ${result.executionTime}ms\n\nOutput:\n${result.stdout}\n\nErrors:\n${result.stderr || 'None'}`
        }
      ]
    };
  }

  private async handleSSHListTargets() {
    const targets = Array.from(this.targets.values());
    
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

  private async handleSSHSystemStatus(args: any) {
    const { targetId } = args;
    const target = this.targets.get(targetId);
    
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `System Status for ${target.host}:\n\nDemo system status output:\n- CPU Usage: 25%\n- Memory Usage: 60%\n- Load Average: 1.2, 1.1, 1.0\n- Active Processes: 142\n\nNote: This is simulated data. In production, this would show real system metrics from ${target.host}.`
        }
      ]
    };
  }

  private async handleSSHDiskUsage(args: any) {
    const { targetId } = args;
    const target = this.targets.get(targetId);
    
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `Disk Usage for ${target.host}:\n\nFilesystem     Size  Used Avail Use% Mounted on\n/dev/sda1       20G   12G  7.5G  62% /\n/dev/sda2      100G   45G   50G  48% /home\ntmpfs          2.0G     0  2.0G   0% /tmp\n\nNote: This is simulated data. In production, this would show real disk usage from ${target.host}.`
        }
      ]
    };
  }

  private async handleSSHMemoryInfo(args: any) {
    const { targetId } = args;
    const target = this.targets.get(targetId);
    
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `Memory Information for ${target.host}:\n\n              total        used        free      shared  buff/cache   available\nMem:           8.0G        2.4G        3.2G        256M        2.4G        5.2G\nSwap:          2.0G          0B        2.0G\n\nNote: This is simulated data. In production, this would show real memory usage from ${target.host}.`
        }
      ]
    };
  }

  private async handleSSHProcessList(args: any) {
    const { targetId } = args;
    const target = this.targets.get(targetId);
    
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `Process List for ${target.host}:\n\nUSER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot         1  0.0  0.1  16896  1024 ?        Ss   Dec01   0:01 /sbin/init\nroot         2  0.0  0.0      0     0 ?        S    Dec01   0:00 [kthreadd]\nroot         3  0.0  0.0      0     0 ?        I<   Dec01   0:00 [rcu_gp]\nuser      1234  1.5  2.3  45678  2048 pts/0    S+   10:30   0:15 python app.py\nuser      5678  0.8  1.2  23456  1024 pts/1    S    10:25   0:05 node server.js\n\nNote: This is simulated data. In production, this would show real process information from ${target.host}.`
        }
      ]
    };
  }

  private async handleSSHNetworkStatus(args: any) {
    const { targetId } = args;
    const target = this.targets.get(targetId);
    
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `Network Status for ${target.host}:\n\nActive Internet connections (only servers)\nProto Recv-Q Send-Q Local Address           Foreign Address         State\ntcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN\ntcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN\ntcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN\ntcp        0      0 0.0.0.0:443             0.0.0.0:*               LISTEN\ntcp6       0      0 :::22                   :::*                    LISTEN\n\nNote: This is simulated data. In production, this would show real network connections from ${target.host}.`
        }
      ]
    };
  }

  private async handleSSHUptime(args: any) {
    const { targetId } = args;
    const target = this.targets.get(targetId);
    
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `Uptime for ${target.host}:\n\n 10:45:23 up 15 days,  3:22,  2 users,  load average: 0.85, 1.12, 1.05\n\nNote: This is simulated data. In production, this would show real uptime information from ${target.host}.`
        }
      ]
    };
  }

  private async handleSSHFileList(args: any) {
    const { targetId, path = '.' } = args;
    const target = this.targets.get(targetId);
    
    if (!target) {
      throw new McpError(ErrorCode.InvalidParams, 'Target not found');
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `File List for ${path} on ${target.host}:\n\ntotal 24\ndrwxr-xr-x  3 user user 4096 Dec  1 10:30 .\ndrwxr-xr-x 15 user user 4096 Nov 30 14:20 ..\n-rw-r--r--  1 user user  220 Nov 30 14:20 .bash_logout\n-rw-r--r--  1 user user 3771 Nov 30 14:20 .bashrc\ndrwx------  2 user user 4096 Dec  1 10:30 .ssh\n-rw-r--r--  1 user user  807 Nov 30 14:20 .profile\n-rw-rw-r--  1 user user 1024 Dec  1 10:30 app.py\n-rw-rw-r--  1 user user 2048 Dec  1 10:25 config.json\n\nNote: This is simulated data. In production, this would show real file listings from ${target.host}.`
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
      
      console.log('SSH MCP Server v2.0 started successfully');
      
    } catch (error) {
      console.error('Failed to start server:', error);
      process.exit(1);
    }
  }

  async shutdown(): Promise<void> {
    try {
      console.log('Shutting down SSH MCP Server...');
      await this.server.close();
      console.log('SSH MCP Server shutdown complete');
    } catch (error) {
      console.error('Error during shutdown:', error);
    }
  }
}

// Start the server
if (require.main === module) {
  const server = new SimpleSSHMCPServer();
  server.run().catch((error) => {
    console.error('Failed to start SSH MCP Server:', error);
    process.exit(1);
  });
}

export default SimpleSSHMCPServer; 