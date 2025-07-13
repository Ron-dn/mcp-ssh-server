import dotenv from 'dotenv';
import { 
  MCPServerConfig, 
  AuthConfig, 
  DatabaseConfig, 
  RedisConfig, 
  VaultConfig,
  PoolConfig 
} from '@/types';

// Load environment variables
dotenv.config();

const getEnvVar = (name: string, defaultValue?: string): string => {
  const value = process.env[name];
  if (!value && !defaultValue) {
    throw new Error(`Environment variable ${name} is required`);
  }
  return value || defaultValue!;
};

const getEnvNumber = (name: string, defaultValue: number): number => {
  const value = process.env[name];
  return value ? parseInt(value, 10) : defaultValue;
};

const getEnvBoolean = (name: string, defaultValue: boolean): boolean => {
  const value = process.env[name];
  return value ? value.toLowerCase() === 'true' : defaultValue;
};

export const serverConfig: MCPServerConfig = {
  name: getEnvVar('MCP_SERVER_NAME', 'ssh-mcp-server-v2'),
  version: getEnvVar('MCP_SERVER_VERSION', '2.0.0'),
  port: getEnvNumber('PORT', 3000),
  host: getEnvVar('HOST', '0.0.0.0'),
  maxConnections: getEnvNumber('MAX_CONNECTIONS', 1000),
  requestTimeout: getEnvNumber('REQUEST_TIMEOUT', 30000),
  enableMetrics: getEnvBoolean('ENABLE_METRICS', true),
  enableTracing: getEnvBoolean('ENABLE_TRACING', true),
};

export const authConfig: AuthConfig = {
  issuerUrl: getEnvVar('OAUTH_ISSUER_URL'),
  clientId: getEnvVar('OAUTH_CLIENT_ID'),
  clientSecret: getEnvVar('OAUTH_CLIENT_SECRET'),
  introspectionEndpoint: getEnvVar('OAUTH_INTROSPECTION_ENDPOINT'),
  requiredScopes: getEnvVar('OAUTH_REQUIRED_SCOPES', 'ssh:execute,ssh:read').split(','),
  tokenCacheTtl: getEnvNumber('TOKEN_CACHE_TTL', 300), // 5 minutes
};

export const databaseConfig: DatabaseConfig = {
  host: getEnvVar('DB_HOST', 'localhost'),
  port: getEnvNumber('DB_PORT', 5432),
  database: getEnvVar('DB_NAME', 'ssh_mcp'),
  username: getEnvVar('DB_USER', 'postgres'),
  password: getEnvVar('DB_PASSWORD'),
  ssl: getEnvBoolean('DB_SSL', false),
  maxConnections: getEnvNumber('DB_MAX_CONNECTIONS', 20),
  connectionTimeout: getEnvNumber('DB_CONNECTION_TIMEOUT', 5000),
};

export const redisConfig: RedisConfig = {
  host: getEnvVar('REDIS_HOST', 'localhost'),
  port: getEnvNumber('REDIS_PORT', 6379),
  password: process.env.REDIS_PASSWORD,
  db: getEnvNumber('REDIS_DB', 0),
  keyPrefix: getEnvVar('REDIS_KEY_PREFIX', 'ssh-mcp:'),
  maxRetriesPerRequest: getEnvNumber('REDIS_MAX_RETRIES', 3),
  retryDelayOnFailover: getEnvNumber('REDIS_RETRY_DELAY', 100),
  enableOfflineQueue: getEnvBoolean('REDIS_OFFLINE_QUEUE', false),
};

export const vaultConfig: VaultConfig = {
  endpoint: getEnvVar('VAULT_ENDPOINT'),
  token: getEnvVar('VAULT_TOKEN'),
  namespace: process.env.VAULT_NAMESPACE,
  apiVersion: getEnvVar('VAULT_API_VERSION', 'v1'),
  timeout: getEnvNumber('VAULT_TIMEOUT', 5000),
  retries: getEnvNumber('VAULT_RETRIES', 3),
};

export const poolConfig: PoolConfig = {
  minConnections: getEnvNumber('POOL_MIN_CONNECTIONS', 2),
  maxConnections: getEnvNumber('POOL_MAX_CONNECTIONS', 10),
  acquireTimeout: getEnvNumber('POOL_ACQUIRE_TIMEOUT', 30000),
  idleTimeout: getEnvNumber('POOL_IDLE_TIMEOUT', 300000), // 5 minutes
  healthCheckInterval: getEnvNumber('POOL_HEALTH_CHECK_INTERVAL', 60000), // 1 minute
  maxRetries: getEnvNumber('POOL_MAX_RETRIES', 3),
};

// Security Configuration
export const securityConfig = {
  bcryptRounds: getEnvNumber('BCRYPT_ROUNDS', 12),
  jwtSecret: getEnvVar('JWT_SECRET'),
  jwtExpiresIn: getEnvVar('JWT_EXPIRES_IN', '1h'),
  rateLimitWindow: getEnvNumber('RATE_LIMIT_WINDOW', 900000), // 15 minutes
  rateLimitMax: getEnvNumber('RATE_LIMIT_MAX', 100),
  maxCommandExecutionTime: getEnvNumber('MAX_COMMAND_EXECUTION_TIME', 60000), // 1 minute
  allowedSSHKeyTypes: getEnvVar('ALLOWED_SSH_KEY_TYPES', 'rsa,ed25519,ecdsa').split(','),
};

// Monitoring Configuration
export const monitoringConfig = {
  metricsPath: getEnvVar('METRICS_PATH', '/metrics'),
  healthPath: getEnvVar('HEALTH_PATH', '/health'),
  readinessPath: getEnvVar('READINESS_PATH', '/ready'),
  jaegerEndpoint: process.env.JAEGER_ENDPOINT,
  logLevel: getEnvVar('LOG_LEVEL', 'info'),
  logFormat: getEnvVar('LOG_FORMAT', 'json'),
};

// SSH Command Whitelist Configuration
export const commandConfig = {
  allowedCommands: new Map([
    ['system_status', {
      command: ['systemctl', 'status'],
      allowedArgs: ['--no-pager', '--lines=50', '--type=service'],
      maxExecutionTime: 30000,
      requiredPermissions: ['system:read'],
      description: 'Check system service status',
    }],
    ['disk_usage', {
      command: ['df', '-h'],
      allowedArgs: [],
      maxExecutionTime: 10000,
      requiredPermissions: ['system:read'],
      description: 'Check disk usage',
    }],
    ['memory_info', {
      command: ['free', '-h'],
      allowedArgs: [],
      maxExecutionTime: 10000,
      requiredPermissions: ['system:read'],
      description: 'Check memory usage',
    }],
    ['process_list', {
      command: ['ps', 'aux'],
      allowedArgs: ['--sort=-pcpu', '--sort=-pmem'],
      maxExecutionTime: 15000,
      requiredPermissions: ['system:read'],
      description: 'List running processes',
    }],
    ['network_status', {
      command: ['ss', '-tuln'],
      allowedArgs: [],
      maxExecutionTime: 10000,
      requiredPermissions: ['network:read'],
      description: 'Check network connections',
    }],
    ['log_tail', {
      command: ['tail'],
      allowedArgs: ['-n', '100', '-f'],
      maxExecutionTime: 60000,
      requiredPermissions: ['logs:read'],
      description: 'Tail log files',
      outputSanitizer: (output: string) => {
        // Remove potential sensitive information
        return output
          .replace(/password[=:]\s*\S+/gi, 'password=***')
          .replace(/token[=:]\s*\S+/gi, 'token=***')
          .replace(/key[=:]\s*\S+/gi, 'key=***');
      },
    }],
    ['file_list', {
      command: ['ls', '-la'],
      allowedArgs: ['-h', '--color=never'],
      maxExecutionTime: 10000,
      requiredPermissions: ['filesystem:read'],
      description: 'List directory contents',
    }],
    ['docker_status', {
      command: ['docker', 'ps'],
      allowedArgs: ['-a', '--format', 'table'],
      maxExecutionTime: 15000,
      requiredPermissions: ['docker:read'],
      description: 'Check Docker container status',
    }],
    ['git_status', {
      command: ['git', 'status'],
      allowedArgs: ['--porcelain', '--branch'],
      maxExecutionTime: 10000,
      requiredPermissions: ['git:read'],
      description: 'Check Git repository status',
    }],
    ['uptime', {
      command: ['uptime'],
      allowedArgs: [],
      maxExecutionTime: 5000,
      requiredPermissions: ['system:read'],
      description: 'Check system uptime',
    }],
  ]),
};

// Validation
export const validateConfig = (): void => {
  const requiredEnvVars = [
    'OAUTH_ISSUER_URL',
    'OAUTH_CLIENT_ID',
    'OAUTH_CLIENT_SECRET',
    'OAUTH_INTROSPECTION_ENDPOINT',
    'DB_PASSWORD',
    'VAULT_ENDPOINT',
    'VAULT_TOKEN',
    'JWT_SECRET',
  ];

  const missing = requiredEnvVars.filter(name => !process.env[name]);
  
  if (missing.length > 0) {
    throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
  }

  // Validate numeric values
  if (serverConfig.port < 1 || serverConfig.port > 65535) {
    throw new Error('PORT must be between 1 and 65535');
  }

  if (poolConfig.minConnections > poolConfig.maxConnections) {
    throw new Error('POOL_MIN_CONNECTIONS cannot be greater than POOL_MAX_CONNECTIONS');
  }

  if (securityConfig.bcryptRounds < 10 || securityConfig.bcryptRounds > 15) {
    throw new Error('BCRYPT_ROUNDS must be between 10 and 15');
  }
};

export default {
  server: serverConfig,
  auth: authConfig,
  database: databaseConfig,
  redis: redisConfig,
  vault: vaultConfig,
  pool: poolConfig,
  security: securityConfig,
  monitoring: monitoringConfig,
  commands: commandConfig,
  validate: validateConfig,
}; 