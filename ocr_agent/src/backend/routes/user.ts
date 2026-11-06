import { Router } from 'express';

export const userRouter = Router();

// TODO: Implement user routes
userRouter.get('/', (req, res) => {
  res.json({ message: 'List users endpoint - TODO' });
});

userRouter.get('/:id', (req, res) => {
  res.json({ message: 'Get user endpoint - TODO', id: req.params.id });
});

userRouter.post('/', (req, res) => {
  res.json({ message: 'Create user endpoint - TODO' });
});

userRouter.put('/:id', (req, res) => {
  res.json({ message: 'Update user endpoint - TODO', id: req.params.id });
});

userRouter.delete('/:id', (req, res) => {
  res.json({ message: 'Delete user endpoint - TODO', id: req.params.id });
});
