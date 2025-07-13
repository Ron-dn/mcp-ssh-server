import { Client, ConnectConfig } from 'ssh2';
import { 
  SSHTarget, 
  SSHConnection, 
  CommandResult, 
  ConnectionPool, 
  PoolConfig,
  SSHError,
  UserContext 
} from '@/types';
import { poolConfig, securityConfig } from '@/config';
import { logger } from '@/utils/logger';
import { SecurityService } from './security';
import { createPool, Pool } from 'generic-pool';
import { promisify } from 'util';
import { setTimeout } from 'timers/promises';

export class SSHConnectionImpl implements SSHConnection {
  public id: string;
  public target: SSHTarget;
  public isConnected: boolean = false;
  public lastUsed: Date = new Date();
  public createdAt: Date = new Date();
  
  private client: Client;
  private connectPromise?: Promise<void>;

  constructor(target: SSHTarget) {
    this.id = `ssh_${target.id}_${Date.now()}`;
    this.target = target;
    this.client = new Client();
  }

  async connect(): Promise<void> {
    if (this.connectPromise) {
      return this.connectPromise;
    }

    this.connectPromise = this._connect();
    return this.connectPromise;
  }

  private async _connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new SSHError('Connection timeout', { target: this.target.host }));
      }, 30000);

      this.client.on('ready', () => {
        clearTimeout(timeout);
        this.isConnected = true;
        this.lastUsed = new Date();
        logger.info('SSH connection established', { 
          targetId: this.target.id, 
          host: this.target.host 
        });
        resolve();
      });

      this.client.on('error', (error) => {
        clearTimeout(timeout);
        this.isConnected = false;
        logger.error('SSH connection error', { 
          targetId: this.target.id, 
          host: this.target.host, 
          error: error.message 
        });
        reject(new SSHError(`Connection failed: ${error.message}`, { 
          target: this.target.host,
          error: error.message 
        }));
      });

      this.client.on('close', () => {
        this.isConnected = false;
        logger.info('SSH connection closed', { 
          targetId: this.target.id, 
          host: this.target.host 
        });
      });

      const connectConfig: ConnectConfig = {
        host: this.target.host,
        port: this.target.port,
        username: this.target.username,
        // TODO: Load private key from Vault using keyId
        privateKey: this.getPrivateKey(this.target.keyId),
        readyTimeout: 30000,
        keepaliveInterval: 60000,
        keepaliveCountMax: 3,
      };

      this.client.connect(connectConfig);
    });
  }

  async disconnect(): Promise<void> {
    if (this.client) {
      this.client.end();
      this.isConnected = false;
      this.connectPromise = undefined;
    }
  }

  async execute(command: string, args: string[]): Promise<CommandResult> {
    if (!this.isConnected) {
      throw new SSHError('Not connected', { targetId: this.target.id });
    }

    const fullCommand = [command, ...args].join(' ');
    const startTime = Date.now();

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new SSHError('Command execution timeout', { 
          command: fullCommand,
          timeout: securityConfig.maxCommandExecutionTime 
        }));
      }, securityConfig.maxCommandExecutionTime);

      this.client.exec(fullCommand, (err, stream) => {
        if (err) {
          clearTimeout(timeout);
          reject(new SSHError(`Command execution failed: ${err.message}`, { 
            command: fullCommand,
            error: err.message 
          }));
          return;
        }

        let stdout = '';
        let stderr = '';
        let exitCode = 0;

        stream.on('close', (code: number) => {
          clearTimeout(timeout);
          const executionTime = Date.now() - startTime;
          this.lastUsed = new Date();

          const result: CommandResult = {
            success: code === 0,
            stdout,
            stderr,
            exitCode: code,
            executionTime,
            timestamp: new Date(),
          };

          logger.info('Command executed', {
            targetId: this.target.id,
            command: fullCommand,
            exitCode: code,
            executionTime,
          });

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
          reject(new SSHError(`Stream error: ${error.message}`, { 
            command: fullCommand,
            error: error.message 
          }));
        });
      });
    });
  }

  async isHealthy(): Promise<boolean> {
    if (!this.isConnected) {
      return false;
    }

    try {
      // Simple health check command
      const result = await this.execute('echo', ['health_check']);
      return result.success && result.stdout.includes('health_check');
    } catch (error) {
      logger.warn('SSH health check failed', { 
        targetId: this.target.id, 
        error: (error as Error).message 
      });
      return false;
    }
  }

  private getPrivateKey(keyId: string): Buffer {
    // TODO: Implement Vault integration to retrieve private keys
    // For now, return a placeholder
    throw new SSHError('Private key retrieval not implemented', { keyId });
  }
}

export class SSHConnectionPool implements ConnectionPool<SSHConnection> {
  private pool: Pool<SSHConnection>;
  private target: SSHTarget;

  constructor(target: SSHTarget, config: PoolConfig) {
    this.target = target;
    
    this.pool = createPool({
      create: async (): Promise<SSHConnection> => {
        const connection = new SSHConnectionImpl(target);
        await connection.connect();
        return connection;
      },
      destroy: async (connection: SSHConnection): Promise<void> => {
        await connection.disconnect();
      },
      validate: async (connection: SSHConnection): Promise<boolean> => {
        return await connection.isHealthy();
      },
    }, {
      min: config.minConnections,
      max: config.maxConnections,
      acquireTimeoutMillis: config.acquireTimeout,
      idleTimeoutMillis: config.idleTimeout,
      testOnBorrow: true,
      testOnReturn: true,
      evictionRunIntervalMillis: config.healthCheckInterval,
      numTestsPerEvictionRun: 3,
      softIdleTimeoutMillis: config.idleTimeout / 2,
    });

    logger.info('SSH connection pool created', { 
      targetId: target.id,
      minConnections: config.minConnections,
      maxConnections: config.maxConnections 
    });
  }

  async acquire(): Promise<SSHConnection> {
    try {
      const connection = await this.pool.acquire();
      logger.debug('SSH connection acquired', { 
        targetId: this.target.id,
        connectionId: connection.id 
      });
      return connection;
    } catch (error) {
      logger.error('Failed to acquire SSH connection', { 
        targetId: this.target.id,
        error: (error as Error).message 
      });
      throw new SSHError(`Failed to acquire connection: ${(error as Error).message}`, { 
        targetId: this.target.id 
      });
    }
  }

  async release(connection: SSHConnection): Promise<void> {
    try {
      await this.pool.release(connection);
      logger.debug('SSH connection released', { 
        targetId: this.target.id,
        connectionId: connection.id 
      });
    } catch (error) {
      logger.error('Failed to release SSH connection', { 
        targetId: this.target.id,
        connectionId: connection.id,
        error: (error as Error).message 
      });
    }
  }

  async destroy(connection: SSHConnection): Promise<void> {
    try {
      await this.pool.destroy(connection);
      logger.debug('SSH connection destroyed', { 
        targetId: this.target.id,
        connectionId: connection.id 
      });
    } catch (error) {
      logger.error('Failed to destroy SSH connection', { 
        targetId: this.target.id,
        connectionId: connection.id,
        error: (error as Error).message 
      });
    }
  }

  async drain(): Promise<void> {
    await this.pool.drain();
    logger.info('SSH connection pool drained', { targetId: this.target.id });
  }

  async clear(): Promise<void> {
    await this.pool.clear();
    logger.info('SSH connection pool cleared', { targetId: this.target.id });
  }

  get size(): number {
    return this.pool.size;
  }

  get available(): number {
    return this.pool.available;
  }

  get borrowed(): number {
    return this.pool.borrowed;
  }
}

export class SSHService {
  private pools: Map<string, SSHConnectionPool> = new Map();
  private targets: Map<string, SSHTarget> = new Map();
  private securityService: SecurityService;

  constructor(securityService: SecurityService) {
    this.securityService = securityService;
  }

  async addTarget(target: SSHTarget): Promise<void> {
    this.targets.set(target.id, target);
    
    const pool = new SSHConnectionPool(target, poolConfig);
    this.pools.set(target.id, pool);

    logger.info('SSH target added', { targetId: target.id, host: target.host });
  }

  async removeTarget(targetId: string): Promise<void> {
    const pool = this.pools.get(targetId);
    if (pool) {
      await pool.drain();
      await pool.clear();
      this.pools.delete(targetId);
    }
    
    this.targets.delete(targetId);
    logger.info('SSH target removed', { targetId });
  }

  async executeCommand(
    targetId: string,
    commandName: string,
    args: string[],
    userContext: UserContext
  ): Promise<CommandResult> {
    // Security validation
    await this.securityService.checkRateLimit(userContext.userId, 'ssh_execute');
    const { command, args: sanitizedArgs } = await this.securityService.validateCommand(
      commandName, 
      args, 
      userContext
    );

    // Get target and pool
    const target = this.targets.get(targetId);
    if (!target) {
      throw new SSHError('Target not found', { targetId });
    }

    const pool = this.pools.get(targetId);
    if (!pool) {
      throw new SSHError('Connection pool not found', { targetId });
    }

    // Execute command
    let connection: SSHConnection | null = null;
    try {
      connection = await pool.acquire();
      const result = await connection.execute(command[0], [...command.slice(1), ...sanitizedArgs]);
      
      // Sanitize output
      const commandConfig = this.securityService.getCommandConfig?.(commandName);
      result.stdout = this.securityService.sanitizeOutput(result.stdout, commandConfig);
      result.stderr = this.securityService.sanitizeOutput(result.stderr, commandConfig);
      result.sanitized = true;

      // Audit log
      await this.securityService.auditLog('command_executed', userContext, {
        targetId,
        commandName,
        exitCode: result.exitCode,
        executionTime: result.executionTime,
      });

      return result;

    } finally {
      if (connection) {
        await pool.release(connection);
      }
    }
  }

  async listTargets(userContext: UserContext): Promise<SSHTarget[]> {
    // TODO: Filter targets based on user permissions
    return Array.from(this.targets.values());
  }

  async getTargetStatus(targetId: string, userContext: UserContext): Promise<{
    target: SSHTarget;
    poolStatus: {
      size: number;
      available: number;
      borrowed: number;
    };
    isHealthy: boolean;
  }> {
    const target = this.targets.get(targetId);
    if (!target) {
      throw new SSHError('Target not found', { targetId });
    }

    const pool = this.pools.get(targetId);
    if (!pool) {
      throw new SSHError('Connection pool not found', { targetId });
    }

    // Test connectivity
    let isHealthy = false;
    try {
      const connection = await pool.acquire();
      isHealthy = await connection.isHealthy();
      await pool.release(connection);
    } catch (error) {
      logger.warn('Health check failed', { 
        targetId, 
        error: (error as Error).message 
      });
    }

    return {
      target,
      poolStatus: {
        size: pool.size,
        available: pool.available,
        borrowed: pool.borrowed,
      },
      isHealthy,
    };
  }

  async shutdown(): Promise<void> {
    logger.info('Shutting down SSH service');
    
    const shutdownPromises = Array.from(this.pools.entries()).map(async ([targetId, pool]) => {
      try {
        await pool.drain();
        await pool.clear();
        logger.info('SSH pool shutdown complete', { targetId });
      } catch (error) {
        logger.error('Error shutting down SSH pool', { 
          targetId, 
          error: (error as Error).message 
        });
      }
    });

    await Promise.all(shutdownPromises);
    this.pools.clear();
    this.targets.clear();
    
    logger.info('SSH service shutdown complete');
  }
} 