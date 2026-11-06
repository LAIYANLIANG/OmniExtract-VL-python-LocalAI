# Windows用户快速部署指南

**适用于**: Windows 10/11  
**难度**: ⭐ 简单（5分钟）  
**前置要求**: 无需任何技术背景

---

## 🎯 快速开始（三步）

### Step 1: 安装Docker Desktop
1. 下载 Docker Desktop
   - 访问：https://www.docker.com/products/docker-desktop
   - 点击"Download for Windows"
   - 下载完成后双击安装

2. 安装Docker Desktop
   - 双击下载的安装程序
   - 按默认选项安装（勾选"Use WSL 2"）
   - 等待安装完成（约5-10分钟）
   - **重启电脑**（必须！）

3. 启动Docker Desktop
   - 重启后，双击桌面的Docker图标
   - 等待Docker图标变绿（约2-5分钟）
   - 看到绿色图标，说明准备好了

### Step 2: 复制项目文件
- 将收到的项目文件夹（ocr_agent）复制到桌面或C盘
- 例如：`C:\ocr_agent`

### Step 3: 运行部署脚本
1. 右键点击项目文件夹中的 `scripts\quick-deploy-windows.ps1`
2. 选择"使用PowerShell运行"
3. 如果提示需要管理员权限，点击"是"
4. 等待脚本运行完成（约5-10分钟）
5. 看到"部署完成"提示后，按Y打开浏览器

**完成！** 🎉

---

## 📝 详细图文教程

### 1. 安装Docker Desktop

#### 1.1 检查系统要求
打开"设置" -> "系统" -> "关于"，确认：
- Windows 10 version 2004 或更高
- 或 Windows 11

#### 1.2 下载Docker Desktop
![下载页面](../docs/images/docker-download.png)
- 访问：https://www.docker.com/products/docker-desktop
- 点击蓝色的"Download for Windows"按钮
- 等待下载完成（约500MB，需要5-10分钟）

#### 1.3 安装Docker Desktop
![安装界面](../docs/images/docker-install.png)
- 双击下载的 `Docker Desktop Installer.exe`
- 勾选"Use WSL 2 instead of Hyper-V"（推荐）
- 点击"OK"开始安装
- 等待安装完成
- 点击"Close and restart"重启电脑

#### 1.4 首次启动
![Docker启动](../docs/images/docker-start.png)
- 电脑重启后，双击桌面的"Docker Desktop"图标
- 接受服务条款（如果有提示）
- 等待Docker启动（任务栏图标从灰色变为绿色）
- 看到欢迎界面，说明安装成功

**验证安装**：
1. 按下 `Win + R`
2. 输入 `powershell` 并回车
3. 在弹出的窗口输入：`docker --version`
4. 如果显示版本号，说明安装成功

---

### 2. 部署项目

#### 2.1 复制项目文件
- 从U盘、网盘或邮件附件获取项目文件
- 解压（如果是压缩包）
- 将整个 `ocr_agent` 文件夹复制到合适的位置
  - 推荐位置：`C:\ocr_agent` 或 `桌面\ocr_agent`
  - 避免放在有中文名称的文件夹中

#### 2.2 运行部署脚本

**方式A：双击运行（推荐）**
1. 打开项目文件夹中的 `scripts` 文件夹
2. 找到 `quick-deploy-windows.ps1` 文件
3. 右键点击该文件
4. 选择"使用PowerShell运行"
5. 如果提示"执行策略更改"，输入 `Y` 并回车
6. 等待脚本自动运行

**方式B：手动命令行**
1. 按下 `Win + X`
2. 选择"Windows PowerShell (管理员)"
3. 输入以下命令：
   ```powershell
   cd C:\ocr_agent
   .\scripts\quick-deploy-windows.ps1
   ```
4. 等待脚本运行

#### 2.3 脚本运行过程
脚本会自动：
- ✅ 检查系统版本
- ✅ 检查Docker是否安装和运行
- ✅ 创建必要的文件夹
- ✅ 生成安全配置
- ✅ 下载和构建Docker镜像（首次需要5-10分钟）
- ✅ 启动所有服务
- ✅ 验证服务状态

#### 2.4 部署完成
![部署成功](../docs/images/deploy-success.png)
看到以下信息说明部署成功：
```
=========================================
部署完成！
=========================================

📱 访问地址:
  - Web界面: http://localhost:3000
  - API文档: http://localhost:3001/api-docs

是否打开Web界面？(Y/N)
```

输入 `Y` 并回车，浏览器会自动打开系统界面。

---

## 🌐 使用系统

### 访问方式
- **Web界面**: 打开浏览器，访问 `http://localhost:3000`
- **支持的浏览器**: Chrome、Edge、Firefox（推荐Chrome）

### 首次登录
1. 打开 http://localhost:3000
2. 使用默认账号登录：
   - 用户名：`admin`
   - 密码：查看 `logs/初始密码.txt`（首次运行后生成）

### 基本操作
1. **上传文件**
   - 点击"上传文件"按钮
   - 选择Excel或PDF文件
   - 等待上传完成

2. **查看处理结果**
   - 点击"任务列表"
   - 查看处理进度
   - 下载处理结果

---

## 🛠️ 日常使用

### 启动系统
如果关闭了Docker Desktop，下次使用时：
1. 双击桌面的"Docker Desktop"图标
2. 等待图标变绿
3. 打开浏览器访问 http://localhost:3000

系统会自动恢复运行，**无需重新部署**。

### 停止系统
1. 打开Docker Desktop
2. 点击"Containers"
3. 点击停止按钮

或者使用命令：
```powershell
cd C:\ocr_agent
docker compose down
```

### 重启系统
```powershell
cd C:\ocr_agent
docker compose restart
```

### 查看运行状态
```powershell
cd C:\ocr_agent
docker compose ps
```

### 查看日志（如果出现问题）
```powershell
cd C:\ocr_agent
docker compose logs -f
```

---

## ❓ 常见问题

### Q1: Docker Desktop安装失败
**错误**: "WSL 2 installation is incomplete"

**解决**:
1. 下载WSL2更新包：https://aka.ms/wsl2kernel
2. 双击安装
3. 重启电脑
4. 重新运行Docker Desktop

### Q2: 脚本运行时提示权限错误
**错误**: "无法加载文件，因为在此系统上禁止运行脚本"

**解决**:
1. 以管理员身份打开PowerShell
2. 运行命令：`Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. 输入 `Y` 确认
4. 重新运行部署脚本

### Q3: 端口被占用
**错误**: "port 3000 is already in use"

**解决**:
1. 打开 `docker-compose.yml`
2. 找到 `ports` 配置
3. 将 `3000:3000` 改为 `8080:3000`
4. 保存文件
5. 重新运行部署脚本
6. 访问地址改为 http://localhost:8080

### Q4: 打开网页显示"无法访问此网站"
**可能原因**: 服务还在启动中

**解决**:
1. 等待2-3分钟
2. 刷新网页
3. 检查Docker Desktop图标是否为绿色
4. 运行 `docker compose ps` 检查服务状态

### Q5: 系统运行缓慢
**优化建议**:
1. 打开Docker Desktop设置
2. 进入"Resources"
3. 增加分配的内存（推荐4GB+）
4. 增加CPU核心数（推荐4核+）
5. 点击"Apply & Restart"

### Q6: 如何完全卸载
**步骤**:
1. 停止所有容器：`docker compose down`
2. 卸载Docker Desktop（通过Windows"添加或删除程序"）
3. 删除项目文件夹
4. 清理Docker数据（可选）：
   ```powershell
   Remove-Item -Recurse -Force "$env:APPDATA\Docker"
   Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Docker"
   ```

---

## 📞 获取帮助

### 技术支持
- 📧 邮箱：support@example.com
- 📱 电话：123-456-7890
- 📖 完整文档：`docs/02-ENVIRONMENT_SETUP.md`

### 在线资源
- Docker Desktop文档：https://docs.docker.com/desktop/windows/
- 项目文档：查看项目中的 `docs` 文件夹
- 视频教程：（如果有提供）

---

## ✅ 检查清单

部署前：
- [ ] Windows 10 version 2004+ 或 Windows 11
- [ ] 至少8GB内存
- [ ] 至少20GB可用磁盘空间
- [ ] 管理员权限

部署完成：
- [ ] Docker Desktop图标为绿色
- [ ] 浏览器能打开 http://localhost:3000
- [ ] 能看到登录界面
- [ ] 能成功登录系统

---

**最后更新**: 2026年3月29日  
**版本**: v1.0
