// Core MCP Types
export interface MCPServerConfig {
  name: string;
  version: string;
  port: number;
  host: string;
  maxConnections: number;
  requestTimeout: number;
  enableMetrics: boolean;
  enableTracing: boolean;
}

// SSH Types
export interface SSHTarget {
  id: string;
  host: string;
  port: number;
  username: string;
  keyId: string;
  description?: string;
  tags?: string[];
  allowedCommands?: string[];
}

export interface SSHConnection {
  id: string;
  target: SSHTarget;
  isConnected: boolean;
  lastUsed: Date;
  createdAt: Date;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  execute(command: string, args: string[]): Promise<CommandResult>;
  isHealthy(): Promise<boolean>;
}

export interface CommandConfig {
  command: string[];
  allowedArgs: string[];
  maxExecutionTime: number;
  requiredPermissions: string[];
  description: string;
  outputSanitizer?: (output: string) => string;
}

export interface CommandResult {
  success: boolean;
  stdout: string;
  stderr: string;
  exitCode: number;
  executionTime: number;
  timestamp: Date;
  sanitized?: boolean;
}

// Security Types
export interface UserContext {
  userId: string;
  scopes: string[];
  permissions: string[];
  tokenExpiry: number;
  sessionId?: string;
  metadata?: Record<string, any>;
}

export interface AuthConfig {
  issuerUrl: string;
  clientId: string;
  clientSecret: string;
  introspectionEndpoint: string;
  requiredScopes: string[];
  tokenCacheTtl: number;
}

export interface SecurityError extends Error {
  code: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  context?: Record<string, any>;
}

// Pool Types
export interface PoolConfig {
  minConnections: number;
  maxConnections: number;
  acquireTimeout: number;
  idleTimeout: number;
  healthCheckInterval: number;
  maxRetries: number;
}

export interface ConnectionPool<T> {
  acquire(): Promise<T>;
  release(resource: T): Promise<void>;
  destroy(resource: T): Promise<void>;
  drain(): Promise<void>;
  clear(): Promise<void>;
  size: number;
  available: number;
  borrowed: number;
}

// Cache Types
export interface CacheEntry<T = any> {
  value: T;
  timestamp: number;
  ttl: number;
  hits: number;
}

export interface CacheManager {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, ttl?: number): Promise<void>;
  delete(key: string): Promise<boolean>;
  clear(): Promise<void>;
  stats(): Promise<CacheStats>;
}

export interface CacheStats {
  hits: number;
  misses: number;
  hitRate: number;
  size: number;
  memoryUsage: number;
}

// Monitoring Types
export interface MetricsCollector {
  incrementCounter(name: string, labels?: Record<string, string>): void;
  recordHistogram(name: string, value: number, labels?: Record<string, string>): void;
  setGauge(name: string, value: number, labels?: Record<string, string>): void;
  startTimer(name: string, labels?: Record<string, string>): () => void;
}

export interface HealthCheck {
  name: string;
  check(): Promise<HealthStatus>;
  timeout: number;
  interval: number;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  message?: string;
  details?: Record<string, any>;
  timestamp: Date;
}

// MCP Tool Types
export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, any>;
    required?: string[];
  };
  outputSchema?: {
    type: 'object';
    properties: Record<string, any>;
  };
  handler: (args: any, context: UserContext) => Promise<any>;
  permissions: string[];
  rateLimit?: {
    requests: number;
    window: number;
  };
}

export interface MCPResource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
  handler: (context: UserContext) => Promise<string | Buffer>;
  permissions: string[];
}

// Configuration Types
export interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl: boolean;
  maxConnections: number;
  connectionTimeout: number;
}

export interface RedisConfig {
  host: string;
  port: number;
  password?: string;
  db: number;
  keyPrefix: string;
  maxRetriesPerRequest: number;
  retryDelayOnFailover: number;
  enableOfflineQueue: boolean;
  cluster?: {
    nodes: Array<{ host: string; port: number }>;
    options?: any;
  };
}

export interface VaultConfig {
  endpoint: string;
  token: string;
  namespace?: string;
  apiVersion: string;
  timeout: number;
  retries: number;
}

// Error Types
export class MCPError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public context?: Record<string, any>
  ) {
    super(message);
    this.name = 'MCPError';
  }
}

export class AuthenticationError extends MCPError {
  constructor(message: string, context?: Record<string, any>) {
    super(message, 'AUTHENTICATION_ERROR', 401, context);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends MCPError {
  constructor(message: string, context?: Record<string, any>) {
    super(message, 'AUTHORIZATION_ERROR', 403, context);
    this.name = 'AuthorizationError';
  }
}

export class ValidationError extends MCPError {
  constructor(message: string, context?: Record<string, any>) {
    super(message, 'VALIDATION_ERROR', 400, context);
    this.name = 'ValidationError';
  }
}

export class SSHError extends MCPError {
  constructor(message: string, context?: Record<string, any>) {
    super(message, 'SSH_ERROR', 500, context);
    this.name = 'SSHError';
  }
}

export class SecurityError extends MCPError {
  constructor(
    message: string,
    public severity: 'low' | 'medium' | 'high' | 'critical' = 'medium',
    context?: Record<string, any>
  ) {
    super(message, 'SECURITY_ERROR', 403, context);
    this.name = 'SecurityError';
  }
} 