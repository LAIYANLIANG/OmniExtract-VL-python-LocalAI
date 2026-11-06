# OCR Agent Platform - Windows快速部署脚本
# PowerShell 5.1+ required

# 设置错误时停止
$ErrorActionPreference = "Stop"

# 控制台输出编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "OCR Agent Platform - Windows快速部署" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ 需要管理员权限" -ForegroundColor Red
    Write-Host "请右键点击PowerShell，选择'以管理员身份运行'" -ForegroundColor Yellow
    pause
    exit 1
}

# 2. 检查Windows版本
$osVersion = [System.Environment]::OSVersion.Version
Write-Host ">>> 检查Windows版本..." -ForegroundColor Green
Write-Host "当前版本: Windows $($osVersion.Major).$($osVersion.Minor) Build $($osVersion.Build)" -ForegroundColor White

if ($osVersion.Build -lt 19041) {
    Write-Host "❌ Windows版本过低" -ForegroundColor Red
    Write-Host "需要: Windows 10 version 2004 (build 19041) 或更高" -ForegroundColor Yellow
    Write-Host "当前: Build $($osVersion.Build)" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "✅ Windows版本满足要求" -ForegroundColor Green
Write-Host ""

# 3. 检查Docker Desktop
Write-Host ">>> 检查Docker Desktop..." -ForegroundColor Green
$dockerPath = Get-Command docker -ErrorAction SilentlyContinue

if (-not $dockerPath) {
    Write-Host "❌ 未找到Docker Desktop" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装Docker Desktop for Windows:" -ForegroundColor Yellow
    Write-Host "1. 下载：https://www.docker.com/products/docker-desktop" -ForegroundColor Cyan
    Write-Host "2. 双击安装" -ForegroundColor Cyan
    Write-Host "3. 重启电脑" -ForegroundColor Cyan
    Write-Host "4. 启动Docker Desktop（等待图标变绿）" -ForegroundColor Cyan
    Write-Host "5. 重新运行此脚本" -ForegroundColor Cyan
    Write-Host ""
    
    $openBrowser = Read-Host "是否打开下载页面？(Y/N)"
    if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
        Start-Process "https://www.docker.com/products/docker-desktop"
    }
    
    pause
    exit 1
}

$dockerVersion = docker --version
Write-Host "✅ Docker已安装: $dockerVersion" -ForegroundColor Green

# 检查Docker是否运行
try {
    docker ps | Out-Null
    Write-Host "✅ Docker服务运行正常" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker服务未运行" -ForegroundColor Red
    Write-Host "请启动Docker Desktop，等待图标变绿后重试" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host ""

# 4. 检查Docker Compose
Write-Host ">>> 检查Docker Compose..." -ForegroundColor Green
try {
    $composeVersion = docker compose version
    Write-Host "✅ Docker Compose已安装: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose未找到" -ForegroundColor Red
    Write-Host "请更新Docker Desktop到最新版本" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host ""

# 5. 检查项目文件
Write-Host ">>> 检查项目文件..." -ForegroundColor Green
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ 未找到 docker-compose.yml" -ForegroundColor Red
    Write-Host "请确保在项目根目录运行此脚本" -ForegroundColor Yellow
    Write-Host "当前目录: $PWD" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "✅ 项目文件完整" -ForegroundColor Green
Write-Host ""

# 6. 创建必要的目录
Write-Host ">>> 创建数据目录..." -ForegroundColor Green
$directories = @(
    "data\uploads\excel",
    "data\uploads\pdf",
    "data\uploads\word",
    "data\uploads\ppt",
    "data\processed\extracted",
    "data\processed\reports",
    "data\processed\logs",
    "data\temp",
    "logs\app",
    "logs\audit",
    "logs\error"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "✅ 目录创建完成" -ForegroundColor Green
Write-Host ""

# 7. 配置环境变量
Write-Host ">>> 配置环境变量..." -ForegroundColor Green
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "✅ 已创建 .env 文件" -ForegroundColor Green
        
        # 生成随机密钥（Windows PowerShell方式）
        function Generate-RandomKey {
            $bytes = New-Object Byte[] 32
            $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
            $rng.GetBytes($bytes)
            return [BitConverter]::ToString($bytes).Replace("-", "").ToLower()
        }
        
        $jwtSecret = Generate-RandomKey
        $encryptKey = Generate-RandomKey
        $dbPassword = Generate-RandomKey
        
        # 更新配置文件
        $envContent = Get-Content ".env" -Raw
        $envContent = $envContent -replace "your_jwt_secret_key_change_this", $jwtSecret
        $envContent = $envContent -replace "your_encryption_key", $encryptKey
        $envContent = $envContent -replace "your_secure_password", $dbPassword
        Set-Content ".env" $envContent
        
        Write-Host "✅ 安全密钥已自动生成" -ForegroundColor Green
    } else {
        Write-Host "⚠️  未找到 .env.example 文件" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ .env 文件已存在" -ForegroundColor Green
}
Write-Host ""

# 8. 检查端口占用
Write-Host ">>> 检查端口占用..." -ForegroundColor Green
function Test-Port {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $connection -ne $null
}

$portsToCheck = @(3000, 3001, 5432, 6379, 5000)
$portsInUse = @()

foreach ($port in $portsToCheck) {
    if (Test-Port -Port $port) {
        $portsInUse += $port
    }
}

if ($portsInUse.Count -gt 0) {
    Write-Host "⚠️  以下端口已被占用: $($portsInUse -join ', ')" -ForegroundColor Yellow
    Write-Host "可能需要修改 docker-compose.yml 中的端口配置" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "是否继续部署？(Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        Write-Host "部署已取消" -ForegroundColor Yellow
        pause
        exit 0
    }
} else {
    Write-Host "✅ 所有端口可用" -ForegroundColor Green
}
Write-Host ""

# 9. 构建Docker镜像
Write-Host ">>> 构建Docker镜像..." -ForegroundColor Green
Write-Host "这可能需要5-10分钟，请耐心等待..." -ForegroundColor Yellow
try {
    docker compose build
    Write-Host "✅ 镜像构建完成" -ForegroundColor Green
} catch {
    Write-Host "❌ 镜像构建失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# 10. 启动服务
Write-Host ">>> 启动服务..." -ForegroundColor Green
try {
    docker compose up -d
    Write-Host "✅ 服务启动成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 服务启动失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    pause
    exit 1
}
Write-Host ""

# 11. 等待服务就绪
Write-Host ">>> 等待服务就绪（最多60秒）..." -ForegroundColor Green
$maxWait = 60
$waited = 0
$ready = $false

while ($waited -lt $maxWait) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        # 继续等待
    }
    
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 1
    $waited++
}

Write-Host ""
if ($ready) {
    Write-Host "✅ 服务已就绪！" -ForegroundColor Green
} else {
    Write-Host "⚠️  服务启动超时，请检查日志" -ForegroundColor Yellow
    Write-Host "运行命令查看日志: docker compose logs -f" -ForegroundColor Cyan
}
Write-Host ""

# 12. 显示服务状态
Write-Host ">>> 服务状态:" -ForegroundColor Green
docker compose ps
Write-Host ""

# 13. 完成提示
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📱 访问地址:" -ForegroundColor Yellow
Write-Host "  - Web界面: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  - API文档: http://localhost:3001/api-docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 常用命令:" -ForegroundColor Yellow
Write-Host "  查看日志:    docker compose logs -f" -ForegroundColor Cyan
Write-Host "  停止服务:    docker compose down" -ForegroundColor Cyan
Write-Host "  重启服务:    docker compose restart" -ForegroundColor Cyan
Write-Host "  查看状态:    docker compose ps" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 完整文档: docs/02-ENVIRONMENT_SETUP.md" -ForegroundColor Yellow
Write-Host ""

# 询问是否打开浏览器
$openBrowser = Read-Host "是否打开Web界面？(Y/N)"
if ($openBrowser -eq "Y" -or $openBrowser -eq "y") {
    Start-Process "http://localhost:3000"
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
pause
