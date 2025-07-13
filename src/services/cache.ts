import Redis from 'ioredis';
import { CacheManager, CacheEntry, CacheStats } from '@/types';
import { redisConfig } from '@/config';
import { logger } from '@/utils/logger';

export class MultiLevelCacheManager implements CacheManager {
  private l1Cache: Map<string, CacheEntry> = new Map(); // In-memory cache
  private l2Cache!: Redis; // Redis cache
  private l1MaxSize: number = 1000;
  private l1DefaultTtl: number = 300; // 5 minutes
  private cacheStats = {
    hits: 0,
    misses: 0,
    l1Hits: 0,
    l2Hits: 0,
  };

  constructor(l1MaxSize: number = 1000) {
    this.l1MaxSize = l1MaxSize;
    this.initializeRedis();
  }

  private initializeRedis(): void {
    try {
      if (redisConfig.cluster) {
        this.l2Cache = new Redis.Cluster(redisConfig.cluster.nodes, {
          redisOptions: {
            password: redisConfig.password,
            db: redisConfig.db,
            keyPrefix: redisConfig.keyPrefix,
            maxRetriesPerRequest: redisConfig.maxRetriesPerRequest,
            retryDelayOnFailover: redisConfig.retryDelayOnFailover,
            enableOfflineQueue: redisConfig.enableOfflineQueue,
          },
          ...redisConfig.cluster.options,
        });
      } else {
        this.l2Cache = new Redis({
          host: redisConfig.host,
          port: redisConfig.port,
          password: redisConfig.password,
          db: redisConfig.db,
          keyPrefix: redisConfig.keyPrefix,
          maxRetriesPerRequest: redisConfig.maxRetriesPerRequest,
          retryDelayOnFailover: redisConfig.retryDelayOnFailover,
          enableOfflineQueue: redisConfig.enableOfflineQueue,
        });
      }

      this.l2Cache.on('connect', () => {
        logger.info('Redis cache connected');
      });

      this.l2Cache.on('error', (error) => {
        logger.error('Redis cache error', { error: error.message });
      });

      this.l2Cache.on('close', () => {
        logger.warn('Redis cache connection closed');
      });

    } catch (error) {
      logger.error('Failed to initialize Redis cache', { error: error.message });
      throw error;
    }
  }

  async get<T>(key: string): Promise<T | null> {
    try {
      // L1: Check in-memory cache first
      const l1Entry = this.l1Cache.get(key);
      if (l1Entry && !this.isExpired(l1Entry)) {
        this.stats.hits++;
        this.stats.l1Hits++;
        l1Entry.hits++;
        logger.debug('Cache L1 hit', { key });
        return l1Entry.value as T;
      }

      // L2: Check Redis cache
      const l2Value = await this.l2Cache.get(key);
      if (l2Value) {
        this.stats.hits++;
        this.stats.l2Hits++;
        
        try {
          const parsed = JSON.parse(l2Value) as T;
          
          // Store in L1 cache for faster access
          this.setL1(key, parsed, this.l1DefaultTtl);
          
          logger.debug('Cache L2 hit', { key });
          return parsed;
        } catch (parseError) {
          logger.error('Failed to parse cached value', { key, error: parseError.message });
          await this.l2Cache.del(key); // Remove corrupted data
        }
      }

      // Cache miss
      this.stats.misses++;
      logger.debug('Cache miss', { key });
      return null;

    } catch (error) {
      logger.error('Cache get error', { key, error: error.message });
      return null;
    }
  }

  async set<T>(key: string, value: T, ttl: number = 3600): Promise<void> {
    try {
      // Set in L1 cache
      this.setL1(key, value, Math.min(ttl, this.l1DefaultTtl));

      // Set in L2 cache (Redis)
      const serialized = JSON.stringify(value);
      if (ttl > 0) {
        await this.l2Cache.setex(key, ttl, serialized);
      } else {
        await this.l2Cache.set(key, serialized);
      }

      logger.debug('Cache set', { key, ttl });

    } catch (error) {
      logger.error('Cache set error', { key, error: error.message });
      throw error;
    }
  }

  async delete(key: string): Promise<boolean> {
    try {
      // Delete from L1 cache
      const l1Deleted = this.l1Cache.delete(key);

      // Delete from L2 cache
      const l2Deleted = await this.l2Cache.del(key);

      logger.debug('Cache delete', { key, l1Deleted, l2Deleted: l2Deleted > 0 });
      return l1Deleted || l2Deleted > 0;

    } catch (error) {
      logger.error('Cache delete error', { key, error: error.message });
      return false;
    }
  }

  async clear(): Promise<void> {
    try {
      // Clear L1 cache
      this.l1Cache.clear();

      // Clear L2 cache (only keys with our prefix)
      const keys = await this.l2Cache.keys(`${redisConfig.keyPrefix}*`);
      if (keys.length > 0) {
        await this.l2Cache.del(...keys);
      }

      // Reset stats
      this.stats = { hits: 0, misses: 0, l1Hits: 0, l2Hits: 0 };

      logger.info('Cache cleared');

    } catch (error) {
      logger.error('Cache clear error', { error: error.message });
      throw error;
    }
  }

  async stats(): Promise<CacheStats> {
    const total = this.stats.hits + this.stats.misses;
    const hitRate = total > 0 ? this.stats.hits / total : 0;

    // Get Redis memory usage
    let memoryUsage = 0;
    try {
      const info = await this.l2Cache.info('memory');
      const match = info.match(/used_memory:(\d+)/);
      if (match) {
        memoryUsage = parseInt(match[1], 10);
      }
    } catch (error) {
      logger.error('Failed to get Redis memory info', { error: error.message });
    }

    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      hitRate,
      size: this.l1Cache.size,
      memoryUsage,
    };
  }

  private setL1<T>(key: string, value: T, ttl: number): void {
    // Implement LRU eviction if cache is full
    if (this.l1Cache.size >= this.l1MaxSize) {
      this.evictLRU();
    }

    const entry: CacheEntry<T> = {
      value,
      timestamp: Date.now(),
      ttl: ttl * 1000, // Convert to milliseconds
      hits: 0,
    };

    this.l1Cache.set(key, entry);
  }

  private isExpired(entry: CacheEntry): boolean {
    return Date.now() - entry.timestamp > entry.ttl;
  }

  private evictLRU(): void {
    let oldestKey = '';
    let oldestTime = Date.now();

    for (const [key, entry] of this.l1Cache.entries()) {
      if (entry.timestamp < oldestTime) {
        oldestTime = entry.timestamp;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.l1Cache.delete(oldestKey);
      logger.debug('L1 cache LRU eviction', { key: oldestKey });
    }
  }

  // Cleanup expired entries from L1 cache
  private cleanupExpired(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, entry] of this.l1Cache.entries()) {
      if (now - entry.timestamp > entry.ttl) {
        expiredKeys.push(key);
      }
    }

    expiredKeys.forEach(key => this.l1Cache.delete(key));

    if (expiredKeys.length > 0) {
      logger.debug('L1 cache cleanup', { expiredCount: expiredKeys.length });
    }
  }

  // Start periodic cleanup
  startCleanup(intervalMs: number = 60000): void {
    setInterval(() => {
      this.cleanupExpired();
    }, intervalMs);
  }

  // Get cache health status
  async getHealth(): Promise<{ status: 'healthy' | 'unhealthy'; details: any }> {
    try {
      // Test Redis connection
      await this.l2Cache.ping();
      
      const stats = await this.stats();
      
      return {
        status: 'healthy',
        details: {
          l1Size: this.l1Cache.size,
          l1MaxSize: this.l1MaxSize,
          redisConnected: true,
          stats,
        },
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: {
          error: error.message,
          l1Size: this.l1Cache.size,
          redisConnected: false,
        },
      };
    }
  }

  // Graceful shutdown
  async disconnect(): Promise<void> {
    try {
      await this.l2Cache.disconnect();
      this.l1Cache.clear();
      logger.info('Cache manager disconnected');
    } catch (error) {
      logger.error('Error during cache disconnect', { error: error.message });
    }
  }
}

// Export a singleton instance
export const cacheManager = new MultiLevelCacheManager();

// Start cleanup process
cacheManager.startCleanup(); 