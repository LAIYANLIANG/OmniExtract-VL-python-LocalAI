import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';
import path from 'path';

const {
  LOG_LEVEL = 'info',
  LOG_FORMAT = 'json',
  LOG_FILE_PATH = './logs/app.log',
  LOG_MAX_SIZE = '10m',
  LOG_MAX_FILES = '7',
  NODE_ENV = 'development',
} = process.env;

// Define log format
const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.splat(),
  LOG_FORMAT === 'json'
    ? winston.format.json()
    : winston.format.printf(({ timestamp, level, message, ...meta }) => {
        return `${timestamp} [${level.toUpperCase()}]: ${message} ${
          Object.keys(meta).length ? JSON.stringify(meta, null, 2) : ''
        }`;
      })
);

// Configure transports
const transports: winston.transport[] = [
  // Console transport
  new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    ),
  }),
];

// Add file transport in production
if (NODE_ENV !== 'test') {
  transports.push(
    new DailyRotateFile({
      filename: LOG_FILE_PATH.replace('.log', '-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      maxSize: LOG_MAX_SIZE,
      maxFiles: LOG_MAX_FILES,
      format: logFormat,
      level: LOG_LEVEL,
    })
  );

  // Separate error log
  transports.push(
    new DailyRotateFile({
      filename: LOG_FILE_PATH.replace('.log', '-error-%DATE%.log'),
      datePattern: 'YYYY-MM-DD',
      maxSize: LOG_MAX_SIZE,
      maxFiles: LOG_MAX_FILES,
      level: 'error',
      format: logFormat,
    })
  );
}

// Create logger instance
export const logger = winston.createLogger({
  level: LOG_LEVEL,
  format: logFormat,
  transports,
  exitOnError: false,
});

// Stream for Morgan HTTP logging
export const stream = {
  write: (message: string) => {
    logger.info(message.trim());
  },
};
