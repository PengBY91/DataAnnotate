# 图像数据标注管理系统 (DataAnnotate)

一个完整的图像数据标注管理平台，支持多种标注类型、任务管理、质量控制、批量审核、导出管理等功能。

## 系统架构

```
用户层：为不同角色（标注员、管理员、算法工程师）提供交互界面
应用层：实现核心业务逻辑，如任务管理、标注工具、质量控制
服务层：提供基础且可复用的能力，如模型推理、文件存储服务
数据层：负责所有数据的存储与管理
```

## 功能特性

### 1. 任务管理模块
- ✅ **任务流水线**：创建任务 → 分配任务 → 标注员领取 → 标注/审核 → 完成
- ✅ **状态追踪**：实时展示任务进度，支持按图像数量统计
- ✅ **灵活分配**：支持单用户分配和多用户团队分配
- ✅ **文件夹上传**：支持批量上传整个文件夹，保留相对路径结构
- ✅ **任务预览**：管理员可查看任务详情、图像列表、标注状态

### 2. 标注工具模块
- ✅ **基础交互**：图像缩放、拖拽、快捷键支持
- ✅ **多工具支持**：边界框、多边形、关键点、分类标注
- ✅ **标签管理**：预设和管理标签
- ✅ **标注状态**：支持未标注、标注中、待审核、已通过、未通过状态
- ✅ **重新标注**：支持对未通过图像进行重新标注

### 3. 质量控制模块
- ✅ **审核机制**：标注-审核流程，支持通过/拒绝操作
- ✅ **批量审核**：支持批量通过多个标注
- ✅ **过滤功能**：按任务、标注员、状态进行过滤
- ✅ **统计展示**：按图像数量显示总图像数、已通过图像、已拒绝图像、通过率
- ✅ **标注员统计**：显示每个标注员的工作量和质量指标

### 4. 导出管理模块
- ✅ **多格式导出**：支持Pascal VOC、COCO、YOLO、JSON格式
- ✅ **异步导出**：大文件异步处理，支持进度跟踪
- ✅ **导出历史**：查看和管理历史导出记录
- ✅ **下载管理**：支持导出文件下载和清理

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy
- **认证**: JWT (python-jose)
- **密码加密**: passlib
- **文件存储**: 本地文件系统
- **异步处理**: 支持异步导出和文件处理

### 前端
- **框架**: Vue 3
- **构建工具**: Vite
- **UI库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios

## 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- SQLite (开发环境) / PostgreSQL (生产环境)

### 1. 克隆项目
```bash
git clone <repository-url>
cd DataAnnotate
```

### 2. 一键安装（推荐）
```bash
# 运行安装脚本
chmod +x install.sh
./install.sh
```

### 3. 手动安装

#### 后端设置
```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 创建管理员用户（首次运行）
python create_admin.py

# 启动后端服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动前端服务
npm run dev
```

### 4. 使用Docker（推荐）

#### 开发环境
```bash
# 一键启动（推荐）
chmod +x docker-start.sh
./docker-start.sh

# 或手动启动
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 生产环境
```bash
# 设置环境变量
export DB_PASSWORD=your_secure_password
export SECRET_KEY=your_secret_key

# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps
```

### 5. 访问系统
- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **默认管理员**: admin / admin123

## 用户角色

### 管理员 (admin)
- **用户管理**：创建、编辑、删除用户，分配角色
- **任务管理**：创建任务、分配任务、查看任务进度
- **质量控制**：审核标注、批量审核、质量统计
- **导出管理**：导出标注数据、管理导出历史
- **系统配置**：系统设置、权限管理

### 算法工程师 (engineer)
- **任务创建**：创建标注任务、设置标注要求
- **数据上传**：单文件上传、文件夹批量上传
- **数据导出**：导出标注结果、下载标注数据
- **任务监控**：查看任务进度、标注质量

### 标注员 (annotator)
- **任务领取**：查看分配的任务、开始标注
- **图像标注**：使用标注工具进行图像标注
- **进度查看**：查看个人标注进度、任务状态
- **重新标注**：对未通过的标注进行重新标注

### 审核员 (reviewer)
- **标注审核**：审核标注员提交的标注
- **质量控制**：批量审核、质量统计
- **反馈管理**：提供标注反馈、质量评估

## API文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
DataAnnotate/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── models/            # 数据模型
│   │   │   ├── user.py        # 用户模型
│   │   │   ├── task.py        # 任务模型
│   │   │   ├── image.py       # 图像模型
│   │   │   ├── annotation.py  # 标注模型
│   │   │   └── task_assignment.py # 任务分配模型
│   │   ├── routes/            # API路由
│   │   │   ├── auth.py        # 认证路由
│   │   │   ├── tasks.py       # 任务管理路由
│   │   │   ├── annotations.py # 标注路由
│   │   │   ├── files.py       # 文件管理路由
│   │   │   ├── quality_control.py # 质量控制路由
│   │   │   └── export.py      # 导出管理路由
│   │   ├── schemas/           # Pydantic模型
│   │   ├── services/          # 业务服务
│   │   └── utils/             # 工具函数
│   ├── main.py                # 应用入口
│   ├── create_admin.py        # 创建管理员脚本
│   └── requirements.txt       # Python依赖
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── components/        # Vue组件
│   │   ├── views/            # 页面视图
│   │   │   ├── Tasks.vue     # 任务管理页面
│   │   │   ├── Annotate.vue  # 标注页面
│   │   │   ├── QualityControl.vue # 质量控制页面
│   │   │   └── Export.vue    # 导出管理页面
│   │   ├── stores/           # Pinia状态管理
│   │   ├── router/           # 路由配置
│   │   └── utils/            # 工具函数
│   └── package.json           # 前端依赖
├── install.sh                 # 一键安装脚本
├── start.sh                   # 启动脚本
├── stop.sh                    # 停止脚本
└── README.md                  # 项目说明
```

## 功能演示

### 1. 任务管理流程
1. **创建任务**：管理员创建标注任务，设置标注类型、标签、要求
2. **分配任务**：将任务分配给标注员或团队
3. **开始标注**：标注员领取任务，开始标注工作
4. **质量控制**：审核员审核标注质量，通过或拒绝
5. **导出结果**：导出标注数据，支持多种格式

### 2. 标注工具使用
- **边界框标注**：拖拽创建矩形框，标注目标对象
- **多边形标注**：点击创建多边形，精确标注不规则形状
- **关键点标注**：点击标记关键点，用于姿态估计等任务
- **分类标注**：选择标签进行分类标注

### 3. 质量控制流程
- **待审核列表**：查看所有待审核的标注
- **过滤功能**：按任务、标注员、状态过滤
- **批量审核**：选择多个标注进行批量通过
- **质量统计**：查看标注质量和通过率

## 开发指南

### 后端开发
1. **创建新的API路由**：在 `app/routes/` 目录下添加路由文件
2. **定义数据模型**：在 `app/models/` 目录下添加模型文件
3. **创建Pydantic模式**：在 `app/schemas/` 目录下添加模式文件
4. **实现业务逻辑**：在 `app/services/` 目录下添加服务文件

### 前端开发
1. **创建新页面**：在 `src/views/` 目录下添加Vue组件
2. **创建可复用组件**：在 `src/components/` 目录下添加组件
3. **管理状态**：在 `src/stores/` 目录下添加Pinia store
4. **配置路由**：在 `src/router/index.js` 中添加路由

## 常见问题

### Q: 如何重置管理员密码？
A: 运行 `python backend/create_admin.py` 重新创建管理员用户。

### Q: 如何备份标注数据？
A: 标注数据存储在SQLite数据库中，可以直接备份 `backend/app.db` 文件。

### Q: 支持哪些图像格式？
A: 支持 jpg、jpeg、png、bmp、gif、tiff、webp 等常见图像格式。

### Q: 如何导出标注数据？
A: 在导出管理页面选择导出格式（Pascal VOC、COCO、YOLO、JSON），系统会异步处理并生成下载链接。

### Q: 如何批量上传图像？
A: 在任务详情页面选择"文件夹上传"，输入文件夹路径，系统会递归遍历所有图像文件。

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
- 邮箱: baoyun20@gmail.com
- 项目地址: https://github.com/PengBY91/DataAnnotate