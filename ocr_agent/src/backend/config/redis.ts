import Redis from 'ioredis';
import { logger } from '../utils/logger';

const {
  REDIS_HOST = 'localhost',
  REDIS_PORT = '6379',
  REDIS_PASSWORD = '',
  REDIS_DB = '0',
} = process.env;

export let redisClient: Redis;

export async function connectRedis(): Promise<Redis> {
  try {
    redisClient = new Redis({
      host: REDIS_HOST,
      port: parseInt(REDIS_PORT, 10),
      password: REDIS_PASSWORD || undefined,
      db: parseInt(REDIS_DB, 10),
      retryStrategy: (times: number) => {
        const delay = Math.min(times * 50, 2000);
        return delay;
      },
      maxRetriesPerRequest: 3,
    });

    redisClient.on('connect', () => {
      logger.info('Redis client connected');
    });

    redisClient.on('error', (error) => {
      logger.error('Redis client error:', error);
    });

    redisClient.on('ready', () => {
      logger.info('Redis client ready');
    });

    // Test connection
    await redisClient.ping();

    return redisClient;
  } catch (error) {
    logger.error('Failed to connect to Redis:', error);
    throw error;
  }
}

export async function disconnectRedis(): Promise<void> {
  if (redisClient) {
    await redisClient.quit();
    logger.info('Redis connection closed.');
  }
}

export { redisClient as redis };
