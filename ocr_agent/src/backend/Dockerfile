# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY src/backend/package*.json ./src/backend/

# Install dependencies
RUN npm ci --workspace=src/backend

# Copy source code
COPY tsconfig.json ./
COPY src/shared ./src/shared
COPY src/backend ./src/backend

# Build application
RUN npm run build:backend

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install only production dependencies
COPY package*.json ./
COPY src/backend/package*.json ./src/backend/
RUN npm ci --workspace=src/backend --omit=dev

# Copy built files from builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/src/shared ./src/shared

# Create necessary directories
RUN mkdir -p logs uploads data && \
    chown -R node:node /app

# Switch to non-root user
USER node

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3001/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

# Start application
CMD ["node", "dist/backend/index.js"]
