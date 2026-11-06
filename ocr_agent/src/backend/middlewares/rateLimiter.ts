import rateLimit from 'express-rate-limit';

const {
  RATE_LIMIT_WINDOW_MS = '900000',
  RATE_LIMIT_MAX_REQUESTS = '100',
} = process.env;

export const rateLimiter = rateLimit({
  windowMs: parseInt(RATE_LIMIT_WINDOW_MS, 10),
  max: parseInt(RATE_LIMIT_MAX_REQUESTS, 10),
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
