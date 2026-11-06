# OCR Agent - 开发入门指南

## 🚀 快速开始

### 1. 环境准备

确保已安装：
- Node.js 20.x 或更高
- npm 10.x 或更高
- Docker & Docker Compose（用于运行数据库）
- Git

### 2. 克隆并安装依赖

```bash
# 进入项目目录
cd ocr_agent

# 创建环境变量文件
cp .env.example .env

# 安装依赖（这会安装根目录和所有子项目的依赖）
npm install
```

### 3. 配置环境变量

编辑 `.env` 文件，设置必要的配置：

```env
# 最小配置
NODE_ENV=development
PORT=3001
FRONTEND_PORT=3000

# 数据库（使用Docker时无需修改）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ocr_agent
DB_USER=postgres
DB_PASSWORD=your_password

# JWT密钥（生产环境请使用强随机密钥）
JWT_SECRET=your_jwt_secret_change_this
JWT_REFRESH_SECRET=your_refresh_secret_change_this

# AI服务（可选，根据需要配置）
OPENAI_API_KEY=your_openai_key
```

### 4. 启动数据库（使用Docker）

```bash
# 只启动数据库和Redis
docker compose up -d postgres redis

# 等待几秒让数据库初始化
sleep 5

# 验证数据库连接
docker compose exec postgres psql -U postgres -d ocr_agent -c "SELECT version();"
```

### 5. 启动开发服务器

```bash
# 同时启动前端和后端开发服务器
npm run dev

# 或者分别启动
npm run dev:backend  # 后端：http://localhost:3001
npm run dev:frontend # 前端：http://localhost:3000
```

### 6. 访问应用

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:3001
- **健康检查**: http://localhost:3001/health

---

## 📁 项目结构

```
ocr_agent/
├── src/
│   ├── backend/              # 后端代码
│   │   ├── config/          # 配置文件（数据库、Redis等）
│   │   ├── controllers/     # 控制器
│   │   ├── services/        # 业务逻辑
│   │   ├── models/          # 数据模型
│   │   ├── middlewares/     # 中间件
│   │   ├── routes/          # 路由定义
│   │   ├── parsers/         # 文件解析器（Excel、PDF等）
│   │   ├── utils/           # 工具函数
│   │   ├── types/           # TypeScript类型
│   │   └── index.ts         # 入口文件
│   ├── frontend/            # 前端代码
│   │   ├── src/
│   │   │   ├── components/ # React组件
│   │   │   ├── pages/      # 页面组件
│   │   │   ├── hooks/      # 自定义Hooks
│   │   │   ├── services/   # API服务
│   │   │   ├── utils/      # 工具函数
│   │   │   └── styles/     # 样式文件
│   │   └── index.html      # HTML入口
│   └── shared/              # 前后端共享代码
│       ├── types/          # 共享类型定义
│       ├── constants/      # 共享常量
│       └── utils/          # 共享工具函数
├── tests/                   # 测试文件
├── scripts/                 # 脚本文件
├── docs/                    # 文档
├── config/                  # 配置文件
├── logs/                    # 日志文件
├── uploads/                 # 上传文件存储
└── data/                    # 数据持久化

```

---

## 🛠️ 开发命令

### 根目录命令

```bash
# 前端+后端同时开发
npm run dev

# 构建整个项目
npm run build

# 运行测试
npm run test

# 代码格式化
npm run format

# 类型检查
npm run typecheck

# Docker相关
npm run docker:build    # 构建镜像
npm run docker:up       # 启动所有服务
npm run docker:down     # 停止所有服务
npm run docker:logs     # 查看日志

# 数据库相关
npm run db:migrate      # 运行迁移
npm run db:seed         # 填充测试数据
npm run db:reset        # 重置数据库
```

### 后端命令

```bash
cd src/backend

# 开发模式（自动重启）
npm run dev

# 构建
npm run build

# 生产环境运行
npm start

# 测试
npm run test
npm run test:watch

# 代码检查
npm run lint
npm run typecheck
```

### 前端命令

```bash
cd src/frontend

# 开发模式
npm run dev

# 构建
npm run build

# 预览构建结果
npm run preview

# 测试
npm run test
npm run test:ui

# 代码检查
npm run lint
npm run typecheck
```

---

## 🧪 测试

```bash
# 运行所有测试
npm run test

# 后端测试
npm run test:backend

# 前端测试
npm run test:frontend

# E2E测试
npm run test:e2e
```

---

## 📦 构建和部署

### 本地构建

```bash
# 构建前端和后端
npm run build

# 生成的文件：
# - dist/backend/  <- 后端构建输出
# - src/frontend/dist/  <- 前端构建输出
```

### 使用Docker部署

```bash
# 构建镜像
npm run docker:build

# 启动所有服务
npm run docker:up

# 查看服务状态
docker compose ps

# 查看日志
npm run docker:logs
```

---

## 🐛 调试

### VSCode调试配置

项目已包含 `.vscode/launch.json`，支持：
- 后端Node.js调试
- 前端Chrome调试
- 测试调试

按 `F5` 即可启动调试。

### 查看日志

```bash
# 后端日志
tail -f logs/app.log
tail -f logs/app-error.log

# Docker日志
docker compose logs -f backend
docker compose logs -f frontend
```

---

## 📚 开发指南

### 添加新的API端点

1. 在 `src/backend/routes/` 创建路由文件
2. 在 `src/backend/controllers/` 创建控制器
3. 在 `src/backend/services/` 实现业务逻辑
4. 在 `src/backend/routes/index.ts` 注册路由

### 添加新的前端页面

1. 在 `src/frontend/src/pages/` 创建页面组件
2. 在 `src/frontend/src/App.tsx` 添加路由
3. 创建相关的组件和服务

### 添加文件解析器

1. 在 `src/backend/parsers/` 创建解析器类
2. 实现解析逻辑
3. 在控制器中调用

### 数据库变更

1. 编辑 `scripts/db/init.sql`
2. 重新创建数据库：`docker compose down -v && docker compose up -d postgres`

---

## 🔧 常见问题

### 端口被占用

```bash
# 修改 .env 文件中的端口号
PORT=3002
FRONTEND_PORT=3001
```

### 数据库连接失败

```bash
# 检查Docker是否运行
docker compose ps

# 重启数据库
docker compose restart postgres

# 查看数据库日志
docker compose logs postgres
```

### 依赖安装失败

```bash
# 清理缓存重新安装
rm -rf node_modules src/*/node_modules package-lock.json
npm install
```

---

## 📖 更多文档

- [项目规划](docs/01-PROJECT_PLAN.md)
- [环境设置](docs/02-ENVIRONMENT_SETUP.md)
- [API文档](docs/API.md) (待创建)
- [架构设计](docs/ARCHITECTURE.md) (待创建)

---

## 🤝 贡献指南

1. 创建功能分支：`git checkout -b feature/your-feature`
2. 提交改动：`git commit -m "Add: your feature"`
3. 推送分支：`git push origin feature/your-feature`
4. 创建Pull Request

---

## 📝 代码规范

- 使用 TypeScript 严格模式
- 遵循 ESLint 规则
- 使用 Prettier 格式化代码
- 编写测试覆盖核心功能
- 添加适当的注释和文档

---

**准备好了吗？运行 `npm run dev` 开始开发！** 🚀
