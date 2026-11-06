import { Application, Router } from 'express';
import { authRouter } from './routes/auth';
import { userRouter } from './routes/user';
import { fileRouter } from './routes/file';
import { taskRouter } from './routes/task';
import { logger } from './utils/logger';

const API_PREFIX = '/api/v1';

export function setupRoutes(app: Application): void {
  const router = Router();

  // Health check
  router.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  // API routes
  router.use('/auth', authRouter);
  router.use('/users', userRouter);
  router.use('/files', fileRouter);
  router.use('/tasks', taskRouter);

  // Mount router
  app.use(API_PREFIX, router);

  // 404 handler
  app.use('*', (req, res) => {
    logger.warn(`404 - Route not found: ${req.method} ${req.originalUrl}`);
    res.status(404).json({
      error: 'Route not found',
      path: req.originalUrl,
    });
  });

  logger.info('Routes configured successfully');
}
