#!/bin/bash

# Quick Setup Script for Development (Unix/Linux/macOS)

echo "🚀 OCR Agent - Development Setup"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check Node.js
echo -e "${YELLOW}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js installed: $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js not found. Please install Node.js 20.x${NC}"
    exit 1
fi

# Check Docker
echo -e "${YELLOW}Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker installed: $DOCKER_VERSION${NC}"
else
    echo -e "${RED}✗ Docker not found. Please install Docker${NC}"
    exit 1
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    
    # Generate random secrets
    JWT_SECRET=$(openssl rand -base64 32)
    REFRESH_SECRET=$(openssl rand -base64 32)
    
    # Update .env file
    sed -i.bak "s|JWT_SECRET=your_jwt_secret.*|JWT_SECRET=$JWT_SECRET|" .env
    sed -i.bak "s|JWT_REFRESH_SECRET=your_refresh_secret.*|JWT_REFRESH_SECRET=$REFRESH_SECRET|" .env
    sed -i.bak "s|DB_PASSWORD=your_secure_password.*|DB_PASSWORD=postgres123|" .env
    rm .env.bak
    
    echo -e "${GREEN}✓ .env file created with random secrets${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Install dependencies
echo ""
echo -e "${YELLOW}Installing dependencies...${NC}"
if npm install; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi

# Start Docker services
echo ""
echo -e "${YELLOW}Starting Docker services (PostgreSQL, Redis)...${NC}"
if docker compose up -d postgres redis; then
    echo -e "${GREEN}✓ Docker services started${NC}"
    echo -e "  Waiting for database to initialize..."
    sleep 10
else
    echo -e "${RED}✗ Failed to start Docker services${NC}"
    exit 1
fi

# Check database connection
echo ""
echo -e "${YELLOW}Verifying database connection...${NC}"
if docker compose exec -T postgres psql -U postgres -d ocr_agent -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connected successfully${NC}"
else
    echo -e "${YELLOW}⚠ Database connection failed, but continuing...${NC}"
fi

# Done
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}✓ Setup complete!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review .env file and update if needed"
echo "  2. Run 'npm run dev' to start development servers"
echo "  3. Open http://localhost:3000 in your browser"
echo ""
echo -e "${YELLOW}Useful commands:${NC}"
echo "  npm run dev          - Start both frontend and backend"
echo "  npm run dev:backend  - Start backend only"
echo "  npm run dev:frontend - Start frontend only"
echo "  npm run docker:logs  - View Docker logs"
echo ""

read -p "Start development servers now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${CYAN}Starting development servers...${NC}"
    npm run dev
fi
