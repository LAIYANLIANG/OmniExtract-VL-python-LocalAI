import { Router } from 'express';

export const taskRouter = Router();

// TODO: Implement task routes
taskRouter.get('/', (req, res) => {
  res.json({ message: 'List tasks endpoint - TODO' });
});

taskRouter.get('/:id', (req, res) => {
  res.json({ message: 'Get task endpoint - TODO', id: req.params.id });
});

taskRouter.post('/', (req, res) => {
  res.json({ message: 'Create task endpoint - TODO' });
});

taskRouter.post('/:id/cancel', (req, res) => {
  res.json({ message: 'Cancel task endpoint - TODO', id: req.params.id });
});

taskRouter.get('/:id/result', (req, res) => {
  res.json({ message: 'Get task result endpoint - TODO', id: req.params.id });
});
