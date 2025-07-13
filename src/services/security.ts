import jwt from 'jsonwebtoken';
import { 
  UserContext, 
  AuthConfig, 
  SecurityError, 
  AuthenticationError, 
  AuthorizationError,
  ValidationError,
  CommandConfig 
} from '@/types';
import { authConfig, securityConfig, commandConfig } from '@/config';
import { CacheManager } from './cache';
import { logger } from '@/utils/logger';

export class SecurityService {
  private cache: CacheManager;

  constructor(cache: CacheManager) {
    this.cache = cache;
  }

  /**
   * Validate OAuth 2.1 token via introspection
   */
  async validateToken(token: string): Promise<UserContext> {
    try {
      // Check cache first
      const cacheKey = `token:${this.hashToken(token)}`;
      const cached = await this.cache.get<UserContext>(cacheKey);
      if (cached) {
        logger.debug('Token validation cache hit', { userId: cached.userId });
        return cached;
      }

      // Introspect token
      const response = await fetch(authConfig.introspectionEndpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Basic ${this.getClientCredentials()}`,
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json',
        },
        body: new URLSearchParams({ token }),
      });

      if (!response.ok) {
        throw new AuthenticationError('Token introspection failed', {
          status: response.status,
          statusText: response.statusText,
        });
      }

      const result = await response.json();

      if (!result.active) {
        throw new AuthenticationError('Token is inactive');
      }

      // Validate required scopes
      const tokenScopes = result.scope ? result.scope.split(' ') : [];
      const hasRequiredScopes = authConfig.requiredScopes.every(scope => 
        tokenScopes.includes(scope)
      );

      if (!hasRequiredScopes) {
        throw new AuthorizationError('Insufficient scopes', {
          required: authConfig.requiredScopes,
          provided: tokenScopes,
        });
      }

      const userContext: UserContext = {
        userId: result.sub,
        scopes: tokenScopes,
        permissions: await this.resolvePermissions(result.sub, tokenScopes),
        tokenExpiry: result.exp,
        metadata: {
          clientId: result.client_id,
          username: result.username,
          tokenType: result.token_type,
        },
      };

      // Cache the validation result
      const ttl = Math.min(authConfig.tokenCacheTtl, result.exp - Math.floor(Date.now() / 1000));
      await this.cache.set(cacheKey, userContext, ttl);

      logger.info('Token validated successfully', { 
        userId: userContext.userId, 
        scopes: userContext.scopes.length 
      });

      return userContext;
    } catch (error) {
      logger.error('Token validation failed', { error: error.message });
      if (error instanceof AuthenticationError || error instanceof AuthorizationError) {
        throw error;
      }
      throw new AuthenticationError(`Token validation failed: ${error.message}`);
    }
  }

  /**
   * Validate and sanitize SSH command execution
   */
  async validateCommand(
    commandName: string, 
    args: string[], 
    userContext: UserContext
  ): Promise<{ command: string[]; args: string[] }> {
    // Check if command is allowed
    const config = commandConfig.allowedCommands.get(commandName);
    if (!config) {
      throw new SecurityError(
        `Command '${commandName}' is not permitted`,
        'critical',
        { commandName, userId: userContext.userId }
      );
    }

    // Check user permissions
    await this.validatePermissions(userContext, config.requiredPermissions);

    // Sanitize and validate arguments
    const sanitizedArgs = this.sanitizeArguments(args, config.allowedArgs);

    logger.info('Command validated', {
      commandName,
      userId: userContext.userId,
      argsCount: sanitizedArgs.length,
    });

    return {
      command: config.command,
      args: sanitizedArgs,
    };
  }

  /**
   * Validate user permissions
   */
  async validatePermissions(userContext: UserContext, requiredPermissions: string[]): Promise<void> {
    const missingPermissions = requiredPermissions.filter(
      permission => !userContext.permissions.includes(permission)
    );

    if (missingPermissions.length > 0) {
      throw new AuthorizationError('Insufficient permissions', {
        userId: userContext.userId,
        required: requiredPermissions,
        missing: missingPermissions,
      });
    }
  }

  /**
   * Sanitize command arguments
   */
  private sanitizeArguments(args: string[], allowedArgs: string[]): string[] {
    const sanitized: string[] = [];

    for (const arg of args) {
      // Basic type validation
      if (typeof arg !== 'string') {
        throw new ValidationError('All arguments must be strings', { arg, type: typeof arg });
      }

      // Length validation
      if (arg.length > 1000) {
        throw new ValidationError('Argument too long', { arg: arg.substring(0, 50) + '...', length: arg.length });
      }

      // Dangerous character detection
      if (this.containsDangerousPatterns(arg)) {
        throw new SecurityError(
          'Argument contains dangerous characters',
          'high',
          { arg: arg.substring(0, 50) + '...' }
        );
      }

      // Whitelist validation
      if (!this.isArgumentAllowed(arg, allowedArgs)) {
        throw new ValidationError(`Argument '${arg}' is not permitted`, { arg, allowedArgs });
      }

      sanitized.push(arg);
    }

    return sanitized;
  }

  /**
   * Check for dangerous patterns in input
   */
  private containsDangerousPatterns(input: string): boolean {
    const dangerousPatterns = [
      /[;&|`$()><\\*?[\]{}]/,     // Shell metacharacters
      /\$\{.*\}/,                // Variable expansion
      /\.\./,                    // Path traversal
      /^-/,                      // Option injection (starts with dash)
      /[\n\r\t\f\v\0]/,         // Control characters
      /eval\(|exec\(/gi,         // Code injection
      /javascript:/gi,           // XSS attempts
      /data:.*base64/gi,         // Data URLs
      /file:\/\//gi,             // File URLs
      /(rm|del|format|fdisk)\s/gi, // Destructive commands
    ];

    return dangerousPatterns.some(pattern => pattern.test(input));
  }

  /**
   * Check if argument is in allowed list
   */
  private isArgumentAllowed(arg: string, allowedArgs: string[]): boolean {
    // If no restrictions, allow all (dangerous - should be avoided)
    if (allowedArgs.length === 0) {
      return true;
    }

    // Exact match
    if (allowedArgs.includes(arg)) {
      return true;
    }

    // Pattern matching for parameterized arguments
    for (const allowed of allowedArgs) {
      if (allowed.includes('*')) {
        const pattern = new RegExp('^' + allowed.replace(/\*/g, '[a-zA-Z0-9_-]*') + '$');
        if (pattern.test(arg)) {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * Resolve user permissions based on scopes and user ID
   */
  private async resolvePermissions(userId: string, scopes: string[]): Promise<string[]> {
    const permissions: string[] = [];

    // Map scopes to permissions
    const scopePermissionMap: Record<string, string[]> = {
      'ssh:read': ['system:read', 'filesystem:read', 'network:read', 'logs:read'],
      'ssh:execute': ['system:execute', 'filesystem:execute'],
      'ssh:admin': ['system:admin', 'filesystem:admin', 'network:admin'],
      'docker:read': ['docker:read'],
      'docker:execute': ['docker:execute'],
      'git:read': ['git:read'],
      'git:execute': ['git:execute'],
    };

    for (const scope of scopes) {
      const scopePermissions = scopePermissionMap[scope];
      if (scopePermissions) {
        permissions.push(...scopePermissions);
      }
    }

    // TODO: Add user-specific permissions from database
    // const userPermissions = await this.getUserPermissions(userId);
    // permissions.push(...userPermissions);

    return [...new Set(permissions)]; // Remove duplicates
  }

  /**
   * Hash token for cache key (security)
   */
  private hashToken(token: string): string {
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(token).digest('hex').substring(0, 32);
  }

  /**
   * Get client credentials for OAuth
   */
  private getClientCredentials(): string {
    const credentials = `${authConfig.clientId}:${authConfig.clientSecret}`;
    return Buffer.from(credentials).toString('base64');
  }

  /**
   * Sanitize command output
   */
  sanitizeOutput(output: string, config?: CommandConfig): string {
    let sanitized = output;

    // Apply command-specific sanitizer if available
    if (config?.outputSanitizer) {
      sanitized = config.outputSanitizer(sanitized);
    }

    // General sensitive information removal
    sanitized = sanitized
      .replace(/password[=:]\s*\S+/gi, 'password=***')
      .replace(/token[=:]\s*\S+/gi, 'token=***')
      .replace(/key[=:]\s*\S+/gi, 'key=***')
      .replace(/secret[=:]\s*\S+/gi, 'secret=***')
      .replace(/api[_-]?key[=:]\s*\S+/gi, 'api_key=***')
      .replace(/bearer\s+[a-zA-Z0-9\-._~+/]+=*/gi, 'bearer ***')
      .replace(/ssh-rsa\s+[A-Za-z0-9+/=]+/gi, 'ssh-rsa ***')
      .replace(/ssh-ed25519\s+[A-Za-z0-9+/=]+/gi, 'ssh-ed25519 ***');

    // Limit output size to prevent memory issues
    const maxOutputSize = 1024 * 1024; // 1MB
    if (sanitized.length > maxOutputSize) {
      sanitized = sanitized.substring(0, maxOutputSize) + '\n\n[OUTPUT TRUNCATED]';
    }

    return sanitized;
  }

  /**
   * Rate limiting check
   */
  async checkRateLimit(userId: string, action: string): Promise<void> {
    const key = `rate_limit:${userId}:${action}`;
    const current = await this.cache.get<number>(key) || 0;
    
    if (current >= securityConfig.rateLimitMax) {
      throw new SecurityError(
        'Rate limit exceeded',
        'medium',
        { userId, action, current, limit: securityConfig.rateLimitMax }
      );
    }

    await this.cache.set(key, current + 1, securityConfig.rateLimitWindow / 1000);
  }

  /**
   * Audit log security events
   */
  async auditLog(event: string, userContext: UserContext, details?: any): Promise<void> {
    logger.warn('Security audit event', {
      event,
      userId: userContext.userId,
      timestamp: new Date().toISOString(),
      details,
    });

    // TODO: Send to external audit system
    // await this.sendToAuditSystem({ event, userContext, details });
  }
} 