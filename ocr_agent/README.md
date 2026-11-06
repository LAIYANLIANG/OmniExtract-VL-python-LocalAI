# OCR Agent Platform

**版本**: v1.0-alpha  
**状态**: 🚧 开发中  
**启动日期**: 2026年3月29日

---

## 📖 项目简介

OCR Agent 是一个基于 OpenClaw 架构设计的企业级文档与数据处理系统。系统专注于大批量财务文档的智能解析和数据整理，支持 Excel、PDF、Word、PowerPoint 等多种格式。

### 核心特性

- 🎯 **智能文档解析** - 支持50份Excel（30MB/份）+ 50份PDF（150页/份）批量处理
- 🔍 **PDF多层解析** - OpenCV预处理 → pdfplumber → PaddleOCR → AI分类的四层架构
- 📊 **多格式支持** - Excel、PDF、Word、PowerPoint全格式覆盖
- 🔐 **企业级安全** - 完整的用户认证、权限管理、数据隔离、审计日志系统
- 🗄️ **数据库集成** - 支持连接地端数据库进行数据读取
- 🌐 **双重接口** - Web界面 + RESTful API
- 🐳 **容器化部署** - Docker Compose 一键部署
- 📈 **AI驱动** - 集成多家AI提供商，支持本地模型

---

## 🚀 快速开始

### 前置要求

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Node.js | >= 20.x LTS | JavaScript运行时 |
| Docker | >= 24.x | 容器化平台 |
| Docker Compose | >= 2.x | 容器编排工具 |
| Python | >= 3.8 | OCR服务依赖 |

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url> ocr_agent
cd ocr_agent

# 2. 安装Node.js依赖
npm install

# 3. 安装Python依赖（OCR服务）
cd ocr-service
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
cd ..

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置

# 5. 初始化数据库
npm run db:init

# 6. 启动服务（Docker方式，推荐）
docker compose up -d

# 7. 验证安装
curl http://localhost:3000/health
```

### 开发模式启动

```bash
# 启动后端服务
npm run dev

# 另开终端，启动OCR服务
cd ocr-service
source venv/bin/activate
python app.py

# 另开终端，启动前端
cd src/web
npm start
```

---

## 📁 项目结构

```
ocr_agent/
├── docs/                   # 📚 项目文档
│   ├── README.md          # 文档导航
│   ├── 01-PROJECT_PLAN.md # 项目规划
│   └── 02-ENVIRONMENT_SETUP.md # 环境搭建
├── src/                   # 💻 源代码
│   ├── core/             # 核心处理引擎
│   ├── auth/             # 权限管理
│   ├── api/              # REST API
│   ├── web/              # Web界面
│   ├── audit/            # 审计日志
│   └── config/           # 配置管理
├── ocr-service/          # 🔍 OCR处理服务
├── docker/               # 🐳 Docker配置
├── tests/                # 🧪 测试文件
├── data/                 # 📦 数据存储
└── logs/                 # 📋 日志文件
```

详细结构请查看 [环境搭建指南](./docs/02-ENVIRONMENT_SETUP.md#项目结构)

---

## 🎯 主要功能

### 1. 多格式文档处理
- **Excel**: 支持.xlsx/.xls，大文件流式处理，公式计算
- **PDF**: 四层智能解析（OpenCV → pdfplumber → PaddleOCR → AI）
- **Word**: 支持.doc/.docx，提取文本和表格
- **PowerPoint**: 支持.ppt/.pptx，识别图表和数据

### 2. 智能数据提取
- 财务报表自动识别和分类
- 表格结构理解和数据提取
- 多语言支持（中英文）
- 扫描件OCR识别

### 3. 数据库集成
- 支持PostgreSQL、MySQL、Oracle等主流数据库
- 安全的连接管理和查询执行
- 事务管理和数据同步

### 4. 用户权限管理
- JWT/API Key多种认证方式
- 角色权限管理（管理员、财务专员、审计员等）
- 部门级数据隔离
- 完整的审计日志

### 5. Web界面
- 文件批量上传和管理
- 实时任务监控
- 结果查看和导出
- 系统管理面板

### 6. API接口
- RESTful API设计
- 完整的API文档（OpenAPI规范）
- 批量处理接口
- Webhook通知

---

## 🛠️ 技术栈

### 后端
- **运行时**: Node.js 20.x LTS
- **语言**: TypeScript 5.x
- **框架**: Express 4.x
- **ORM**: Sequelize 6.x
- **缓存**: Redis 7.x

### 前端
- **框架**: React 18.x
- **语言**: TypeScript 5.x
- **UI库**: Ant Design 5.x
- **状态管理**: Zustand
- **图表**: Apache ECharts

### 文档处理
- **Excel**: xlsx, exceljs
- **PDF**: pdfplumber, PaddleOCR, OpenCV
- **Word**: mammoth, docx
- **PowerPoint**: pptxjs, node-pptx

### AI集成
- **OpenAI**: GPT-4等模型
- **Anthropic**: Claude系列模型
- **本地模型**: Ollama、LocalAI

### 基础设施
- **容器化**: Docker + Docker Compose
- **数据库**: PostgreSQL 14+
- **监控**: Prometheus + Grafana

---

## 📖 文档

完整的项目文档请访问 [docs](./docs/) 目录：

0. **[讨论记录](./docs/00-DISCUSSION_RECORD.md)** - 完整的项目讨论和决策过程
1. **[文档导航](./docs/README.md)** - 所有文档的索引和导航
2. **[项目规划](./docs/01-PROJECT_PLAN.md)** - 详细的项目规划和技术方案
3. **[环境搭建](./docs/02-ENVIRONMENT_SETUP.md)** - 开发环境配置指南
4. **审计日志系统** *(待创建)*
5. **API文档** *(待创建)*
6. **用户手册** *(待创建)*

---

## 🗺️ 开发路线图

### 第一阶段 - 基础架构 (Week 1-2) 🔄
- [x] 项目规划
- [x] 文档编写
- [ ] 开发环境搭建
- [ ] Docker容器化配置
- [ ] 基础服务框架

### 第二阶段 - 核心引擎 (Week 3-6) ⏸️
- [ ] Excel处理器
- [ ] PDF多层解析系统
- [ ] Word/PPT处理器
- [ ] 数据库连接模块
- [ ] AI模型集成

### 第三阶段 - 权限系统 (Week 7-8) ⏸️
- [ ] 用户认证
- [ ] 角色权限管理
- [ ] 数据访问控制
- [ ] 审计日志系统

### 第四阶段 - 用户界面 (Week 9-11) ⏸️
- [ ] 文件管理界面
- [ ] 任务监控界面
- [ ] 结果展示界面
- [ ] 管理后台

### 第五阶段 - API开发 (Week 12-13) ⏸️
- [ ] REST API实现
- [ ] API认证和限流
- [ ] 批量处理接口
- [ ] Webhook通知

### 第六阶段 - 测试部署 (Week 14-16) ⏸️
- [ ] 功能测试
- [ ] 性能测试
- [ ] 安全测试
- [ ] 部署上线

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 开发流程
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范
- 遵循 ESLint + Prettier 配置
- 使用 Conventional Commits 提交信息
- 所有 PR 需要通过代码审查
- 保持测试覆盖率 > 80%

---

## 📊 项目状态

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| 代码覆盖率 | 0% | 80%+ |
| 文档完整度 | 40% | 100% |
| 功能完成度 | 5% | 100% |
| 测试用例数 | 0 | 500+ |

---

## 🐛 已知问题

目前项目处于早期开发阶段，以下功能尚未完成：
- [ ] 核心处理引擎
- [ ] 权限管理系统
- [ ] Web界面
- [ ] API接口
- [ ] 测试套件

详细问题追踪请查看 [GitHub Issues](../../issues)

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](./LICENSE) 文件。

---

## 🙏 致谢

本项目参考了以下优秀的开源项目：

- [OpenClaw](https://github.com/openclaw/openclaw) - 架构设计参考
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) - OCR识别引擎
- [pdfplumber](https://github.com/jsvine/pdfplumber) - PDF解析工具

---

## 📞 联系方式

- **项目主页**: [GitHub Repository](../../)
- **问题反馈**: [GitHub Issues](../../issues)
- **邮箱**: [待定]
- **文档**: [docs/](./docs/)

---

**开发团队**: OCR Agent Platform Team  
**最后更新**: 2026年3月29日  
**项目状态**: 🚧 积极开发中
