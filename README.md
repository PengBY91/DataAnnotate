# 图像数据标注管理系统

一个完整的图像数据标注管理平台，支持多种标注类型、任务管理、质量控制等功能。

## 系统架构

```
用户层：为不同角色（标注员、管理员、算法工程师）提供交互界面
应用层：实现核心业务逻辑，如任务管理、标注工具、质量控制
服务层：提供基础且可复用的能力，如模型推理、文件存储服务
数据层：负责所有数据的存储与管理
```

## 功能特性

### 1. 任务管理模块
- ✅ 任务流水线：创建任务 → 分配任务 → 标注员领取 → 标注/审核 → 完成
- ✅ 状态追踪：实时展示任务进度
- ✅ 灵活分配：支持按数据集或规则分配给个人或团队

### 2. 标注工具模块
- ✅ 基础交互：图像缩放、拖拽、快捷键支持
- ✅ 多工具支持：边界框、多边形、关键点、分类标注
- ✅ 标签管理：预设和管理标签
- ✅ 结果导出：支持Pascal VOC XML、JSON、COCO等格式

### 3. 质量控制模块
- ✅ 审核机制：标注-审核流程
- 🔄 智能预标注：集成初始模型进行预标注（规划中）
- 🔄 主动学习：识别不确定样本优先标注（规划中）

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy
- **认证**: JWT
- **缓存**: Redis
- **文件存储**: 本地文件系统

### 前端
- **框架**: Vue 3
- **构建工具**: Vite
- **UI库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 1. 克隆项目
```bash
git clone <repository-url>
cd DataLabels
```

### 2. 后端设置
```bash
cd backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库连接等信息

# 运行数据库迁移
alembic upgrade head

# 启动后端服务
uvicorn main:app --reload
```

### 3. 前端设置
```bash
cd frontend
npm install

# 启动前端服务
npm run dev
```

### 4. 使用Docker（推荐）
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 用户角色

### 管理员 (admin)
- 用户管理
- 任务管理
- 系统配置

### 算法工程师 (engineer)
- 创建任务
- 上传图像
- 导出标注数据

### 标注员 (annotator)
- 领取任务
- 进行标注
- 查看进度

### 审核员 (reviewer)
- 审核标注
- 质量控制
- 反馈意见

## API文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
DataLabels/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── routes/         # API路由
│   │   ├── schemas/        # Pydantic模型
│   │   ├── services/       # 业务服务
│   │   └── utils/          # 工具函数
│   ├── main.py             # 应用入口
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile         # Docker配置
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/     # Vue组件
│   │   ├── views/         # 页面视图
│   │   ├── stores/        # Pinia状态管理
│   │   ├── router/        # 路由配置
│   │   └── utils/         # 工具函数
│   ├── package.json       # 前端依赖
│   └── Dockerfile         # Docker配置
├── docker-compose.yml     # Docker编排
└── README.md             # 项目说明
```

## 开发指南

### 后端开发
1. 创建新的API路由：在 `app/routes/` 目录下添加路由文件
2. 定义数据模型：在 `app/models/` 目录下添加模型文件
3. 创建Pydantic模式：在 `app/schemas/` 目录下添加模式文件
4. 实现业务逻辑：在 `app/services/` 目录下添加服务文件

### 前端开发
1. 创建新页面：在 `src/views/` 目录下添加Vue组件
2. 创建可复用组件：在 `src/components/` 目录下添加组件
3. 管理状态：在 `src/stores/` 目录下添加Pinia store
4. 配置路由：在 `src/router/index.js` 中添加路由

## 部署指南

### 生产环境部署
1. 配置环境变量
2. 设置数据库连接
3. 配置文件存储路径
4. 设置反向代理（Nginx）
5. 配置SSL证书

### 性能优化
- 使用CDN加速静态资源
- 配置数据库连接池
- 启用Redis缓存
- 优化图像处理

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：
- 邮箱: your-email@example.com
- 项目地址: https://github.com/your-username/DataLabels