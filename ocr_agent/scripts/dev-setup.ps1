# Quick Setup Script for Development

Write-Host "🚀 OCR Agent - Development Setup" -ForegroundColor Cyan
Write-Host ""

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Node.js installed: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js not found. Please install Node.js 20.x" -ForegroundColor Red
    exit 1
}

# Check Docker
Write-Host "Checking Docker..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Docker not found. Please install Docker Desktop" -ForegroundColor Red
    exit 1
}

# Create .env if not exists
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    
    # Generate random secrets
    $jwtSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    $refreshSecret = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
    
    # Update .env file
    (Get-Content .env) | ForEach-Object {
        $_ -replace 'JWT_SECRET=your_jwt_secret.*', "JWT_SECRET=$jwtSecret" `
           -replace 'JWT_REFRESH_SECRET=your_refresh_secret.*', "JWT_REFRESH_SECRET=$refreshSecret" `
           -replace 'DB_PASSWORD=your_secure_password.*', "DB_PASSWORD=postgres123"
    } | Set-Content .env
    
    Write-Host "✓ .env file created with random secrets" -ForegroundColor Green
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
npm install
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Start Docker services
Write-Host ""
Write-Host "Starting Docker services (PostgreSQL, Redis)..." -ForegroundColor Yellow
docker compose up -d postgres redis
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker services started" -ForegroundColor Green
    Write-Host "  Waiting for database to initialize..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
} else {
    Write-Host "✗ Failed to start Docker services" -ForegroundColor Red
    exit 1
}

# Check database connection
Write-Host ""
Write-Host "Verifying database connection..." -ForegroundColor Yellow
docker compose exec -T postgres psql -U postgres -d ocr_agent -c "SELECT version();" > $null 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database connected successfully" -ForegroundColor Green
} else {
    Write-Host "⚠ Database connection failed, but continuing..." -ForegroundColor Yellow
}

# Done
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review .env file and update if needed"
Write-Host "  2. Run 'npm run dev' to start development servers"
Write-Host "  3. Open http://localhost:3000 in your browser"
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  npm run dev          - Start both frontend and backend"
Write-Host "  npm run dev:backend  - Start backend only"
Write-Host "  npm run dev:frontend - Start frontend only"
Write-Host "  npm run docker:logs  - View Docker logs"
Write-Host ""

$start = Read-Host "Start development servers now? (Y/N)"
if ($start -eq 'Y' -or $start -eq 'y') {
    Write-Host ""
    Write-Host "Starting development servers..." -ForegroundColor Cyan
    npm run dev
}
