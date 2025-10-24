# 图像数据标注管理系统 (DataAnnotate)

一个功能完整、企业级的图像数据标注管理平台，支持多种标注类型、多人协作、任务管理、质量控制、批量审核、数据导出等核心功能。适用于计算机视觉项目的数据标注、质量管理和团队协作。

## ✨ 核心特性

- 🎯 **多种标注类型**：边界框、多边形、关键点、分类、回归
- 👥 **多人协作**：支持多标注员协作，可配置每张图像需要的标注数量
- 📊 **智能任务管理**：任务状态自动更新，实时进度追踪
- ✅ **完善的质量控制**：标注审核、批量审核、质量统计
- 📤 **灵活的数据导出**：支持CSV、JSON、COCO、YOLO、Pascal VOC等格式
- 🔐 **精细的权限控制**：基于角色的访问控制，管理员、标注员、审核员分离
- 💾 **数据持久化**：导出历史、任务状态持久化存储，服务重启不丢失
- 🚀 **异步处理**：大数据量导出异步处理，支持进度查询

## 系统架构

```
用户层：为不同角色（标注员、管理员、算法工程师）提供交互界面
应用层：实现核心业务逻辑，如任务管理、标注工具、质量控制
服务层：提供基础且可复用的能力，如模型推理、文件存储服务
数据层：负责所有数据的存储与管理
```

## 📋 功能特性

### 1. 任务管理模块
- ✅ **完整的任务流水线**：创建 → 分配 → 标注 → 审核 → 完成
- ✅ **智能状态管理**：任务状态自动更新（待分配→进行中→已完成→已审核）
- ✅ **多标注员协作**：支持将任务分配给多个标注员
- ✅ **可配置标注数量**：设置每张图像需要的标注人数（如3人标注同一张图）
- ✅ **多种标注类型**：支持边界框、多边形、关键点、分类、回归
- ✅ **任务编辑功能**：支持修改任务信息、标注类型、标签列表
- ✅ **任务删除**：管理员可删除任务及所有关联数据（级联删除）
- ✅ **文件管理**：
  - 单文件上传：支持拖拽上传图像
  - 文件夹批量上传：递归遍历文件夹，保留相对路径结构
  - 支持多种图像格式：jpg、png、bmp、tiff、webp等

### 2. 标注工具模块
- ✅ **多种标注工具**：
  - 🔲 边界框（Bounding Box）：目标检测
  - 📐 多边形（Polygon）：实例分割
  - 📍 关键点（Keypoint）：姿态估计
  - 🏷️ 分类（Classification）：图像分类
  - 📊 回归（Regression）：数值预测
- ✅ **智能UI交互**：
  - Tab页切换不同标注类型
  - 只显示当前任务定义的标注类型
  - 图像缩放、拖拽、快捷键支持
- ✅ **自动导航**：完成当前图像后自动跳转下一张未标注图像
- ✅ **标注管理**：
  - 添加、编辑、删除标注
  - 标注列表显示（每个标注员的最终标注）
  - 自动去重（只保留每个标注员的最新标注）
- ✅ **状态追踪**：未标注、标注中、待审核、已通过、未通过

### 3. 质量控制模块
- ✅ **完善的审核机制**：
  - 只有管理员可以审核（权限隔离）
  - 支持通过/拒绝操作
  - 批量审核功能（选择多张图像批量通过/拒绝）
- ✅ **灵活的过滤**：
  - 按任务过滤
  - 按标注员过滤
  - 按状态过滤（待审核、已通过、已拒绝）
- ✅ **详细的统计展示**：
  - 总图像数、已通过图像、已拒绝图像
  - 通过率计算（按图像数量）
  - 每个标注员的质量指标
- ✅ **审核详情**：
  - 查看标注详情和图像预览
  - 添加审核备注
  - 历史审核记录

### 4. 导出管理模块
- ✅ **多种导出格式**：
  - 📊 **CSV**：表格格式，支持Excel，包含完整标注信息（新增✨）
  - 📄 **JSON**：通用格式，包含所有元数据
  - 🎯 **COCO**：COCO数据集格式
  - 🔍 **YOLO**：YOLO训练格式
  - 📦 **Pascal VOC**：Pascal VOC XML格式
- ✅ **异步导出**：
  - 大数据量异步处理
  - 实时进度查询
  - 支持后台处理
- ✅ **数据持久化**：
  - 导出历史保存到数据库（新增✨）
  - 服务重启后历史记录不丢失
  - 支持导出记录的查询和过滤
- ✅ **导出配置**：
  - 可选包含原始图像
  - 状态过滤（只导出已通过的标注）
  - 用户隔离（每个用户只能看到自己的导出记录）

### 5. 用户与权限管理
- ✅ **角色分离**：
  - **管理员**：只能审核，不能标注
  - **标注员**：只能标注，不能审核
  - **算法工程师**：任务创建、数据导出
- ✅ **精细权限控制**：
  - 基于角色的访问控制（RBAC）
  - API级别权限验证
  - 前端UI权限控制
- ✅ **用户管理**：
  - 创建、编辑、删除用户
  - 分配角色
  - 密码加密存储

## 🛠️ 技术栈

### 后端技术
- **Web框架**: FastAPI 0.100+ (高性能异步框架)
- **数据库**: SQLite (开发环境) / PostgreSQL (生产环境)
- **ORM**: SQLAlchemy 2.0+ (数据建模和查询)
- **认证**: JWT Token (python-jose)
- **密码加密**: bcrypt 4.0.1 + passlib (安全哈希)
- **文件处理**: Pillow, OpenCV (图像处理)
- **数据导出**: pandas, lxml (CSV, XML生成)
- **异步任务**: asyncio (后台任务处理)
- **数据验证**: Pydantic 2.0+ (类型验证)

### 前端技术
- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite 4.0+ (极速开发和构建)
- **UI组件库**: Element Plus (完整组件库)
- **状态管理**: Pinia (轻量级状态管理)
- **路由**: Vue Router 4
- **HTTP客户端**: Axios (API请求)
- **Canvas绘图**: HTML5 Canvas (标注工具)

### 数据库设计
- **用户表** (users): 用户信息、角色权限
- **任务表** (tasks): 任务配置、状态、进度
- **图像表** (images): 图像信息、标注状态
- **标注表** (annotations): 标注数据、审核状态
- **任务分配表** (task_assignments): 多对多分配关系
- **导出记录表** (export_records): 导出历史持久化 ✨

## 🚀 快速开始

### 📋 环境要求
- Python 3.8+ (推荐 3.10+)
- Node.js 16+ (推荐 18+)
- SQLite (开发环境，已内置) / PostgreSQL (生产环境)

### 1️⃣ 克隆项目
```bash
git clone https://github.com/PengBY91/DataAnnotate.git
cd DataAnnotate
```

### 2️⃣ 一键安装（推荐 ⭐）
```bash
# 添加执行权限
chmod +x install.sh start.sh stop.sh

# 运行一键安装脚本（自动安装所有依赖并创建管理员账号）
./install.sh
```

**安装脚本会自动完成以下操作：**
- ✅ 检查Python和Node.js环境
- ✅ 创建Python虚拟环境
- ✅ 安装后端依赖（requirements.txt）
- ✅ 安装前端依赖（npm install）
- ✅ 初始化数据库（创建所有表）
- ✅ 创建默认管理员账号（admin / admin123）

### 3️⃣ 启动服务
```bash
# 一键启动前后端服务
./start.sh

# 或者手动启动
# 后端（终端1）
cd backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 前端（终端2）
cd frontend && npm run dev
```

### 4️⃣ 停止服务
```bash
# 一键停止所有服务
./stop.sh
```

### 5️⃣ 访问系统
服务启动后，在浏览器中访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 🌐 **前端界面** | http://localhost:3000 | 用户交互界面 |
| 🔌 **后端API** | http://localhost:8000 | RESTful API |
| 📚 **API文档** | http://localhost:8000/docs | Swagger UI文档 |
| 📖 **ReDoc文档** | http://localhost:8000/redoc | ReDoc格式文档 |

**默认管理员账号：**
- 用户名：`admin`
- 密码：`admin123`
- ⚠️ 首次登录后请立即修改密码！

---

### 📦 手动安装（高级用户）

如果你不想使用一键安装脚本，可以手动安装：

#### 后端设置
```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"

# 创建管理员账号
python -c "from app.database import SessionLocal; from app.models.user import User, UserRole; from app.utils.auth import get_password_hash; db = SessionLocal(); admin = User(username='admin', full_name='管理员', email='admin@example.com', hashed_password=get_password_hash('admin123'), role=UserRole.ADMIN, is_active=True); db.add(admin); db.commit(); print('管理员账号创建成功')"

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端设置
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 👥 用户角色与权限

系统采用基于角色的访问控制（RBAC），不同角色有不同的权限和功能：

### 🔑 管理员 (Admin)
**核心职责：** 系统管理、质量控制、用户管理

**权限清单：**
- ✅ 用户管理：创建、编辑、删除用户，分配角色
- ✅ 任务管理：创建、编辑、删除任务，分配任务
- ✅ 质量控制：审核标注、批量审核、质量统计（**仅管理员可审核**）
- ✅ 数据导出：导出标注数据、管理导出历史
- ✅ 系统配置：查看系统状态、管理配置
- ❌ **不能标注**：管理员专注于管理和审核，不参与实际标注工作

**典型场景：** 项目管理者、质量负责人

---

### 🛠️ 算法工程师 (Engineer)
**核心职责：** 任务创建、数据准备、结果导出

**权限清单：**
- ✅ 任务创建：创建标注任务、设置标注类型和要求
- ✅ 数据上传：单文件上传、文件夹批量上传
- ✅ 任务分配：将任务分配给标注员
- ✅ 数据导出：导出标注结果（CSV、JSON、COCO、YOLO等）
- ✅ 进度监控：查看任务进度、标注质量统计
- ⚠️ 可以标注：工程师可以参与标注（与管理员不同）

**典型场景：** 算法开发人员、数据集准备人员

---

### ✏️ 标注员 (Annotator)
**核心职责：** 图像标注、质量保证

**权限清单：**
- ✅ 任务查看：查看分配给自己的任务
- ✅ 图像标注：使用多种工具进行标注（边界框、多边形、关键点、分类、回归）
- ✅ 进度查看：查看个人标注进度、完成情况
- ✅ 重新标注：对被拒绝的标注进行修改和重新提交
- ✅ 个人仪表盘：查看个人统计数据
- ❌ **不能审核**：标注员只能标注，不能审核自己或他人的标注

**典型场景：** 数据标注人员、众包标注者

---

### 🔍 审核员 (Reviewer)
**核心职责：** 标注审核、质量反馈

**权限清单：**
- ✅ 标注审核：审核标注员提交的标注（通过/拒绝）
- ✅ 批量审核：批量处理多个标注
- ✅ 质量统计：查看标注质量、通过率等指标
- ✅ 反馈管理：提供标注反馈、质量评估
- ⚠️ **注意**：在当前版本中，审核权限与管理员合并

**典型场景：** 质量检查人员、高级标注员

## 📚 API 文档

系统提供完整的 RESTful API，支持自动生成的交互式文档：

- **Swagger UI**: http://localhost:8000/docs
  - 交互式API文档，可直接测试API
  - 包含所有端点、请求参数、响应格式
  
- **ReDoc**: http://localhost:8000/redoc
  - 更友好的阅读格式
  - 适合API文档查阅和分享

**主要API端点：**
- `/api/auth/*` - 用户认证（登录、注册、token刷新）
- `/api/users/*` - 用户管理（CRUD、角色分配）
- `/api/tasks/*` - 任务管理（创建、分配、状态更新）
- `/api/files/*` - 文件管理（上传、下载、预览）
- `/api/annotations/*` - 标注管理（创建、查询、更新）
- `/api/quality/*` - 质量控制（审核、统计）
- `/api/export/*` - 导出管理（多格式导出、历史记录）

## 📁 项目结构

```
DataAnnotate/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── models/                  # SQLAlchemy 数据模型
│   │   │   ├── __init__.py          # 模型导出
│   │   │   ├── user.py              # 用户模型（角色、权限）
│   │   │   ├── task.py              # 任务模型（状态、进度）
│   │   │   ├── image.py             # 图像模型（标注状态）
│   │   │   ├── annotation.py        # 标注模型（标注数据）
│   │   │   ├── task_assignment.py   # 任务分配模型（多对多关系）
│   │   │   └── export.py            # 导出记录模型（新增✨）
│   │   ├── routes/                  # FastAPI 路由
│   │   │   ├── auth.py              # 认证路由（登录、token）
│   │   │   ├── users.py             # 用户管理路由
│   │   │   ├── tasks.py             # 任务管理路由
│   │   │   ├── files.py             # 文件管理路由（上传、下载）
│   │   │   ├── annotations.py       # 标注路由（CRUD、审核）
│   │   │   ├── quality_control.py   # 质量控制路由（新增✨）
│   │   │   └── export.py            # 导出管理路由
│   │   ├── schemas/                 # Pydantic 数据验证模型
│   │   │   ├── user.py              # 用户schema
│   │   │   ├── task.py              # 任务schema
│   │   │   ├── annotation.py        # 标注schema
│   │   │   └── export.py            # 导出schema
│   │   ├── services/                # 业务服务层
│   │   │   └── export_service.py    # 导出服务（CSV、JSON、COCO等）
│   │   └── utils/                   # 工具函数
│   │       └── auth.py              # 认证工具（JWT、密码加密）
│   ├── static/                      # 静态文件
│   │   ├── uploads/                 # 上传的图像
│   │   └── exports/                 # 导出的文件
│   ├── main.py                      # FastAPI 应用入口
│   ├── database.py                  # 数据库配置
│   ├── requirements.txt             # Python 依赖
│   └── datalabels.db               # SQLite 数据库（开发环境）
├── frontend/                        # 前端应用
│   ├── src/
│   │   ├── components/              # Vue 公共组件
│   │   │   └── AnnotationCanvas.vue # 标注画布组件
│   │   ├── views/                   # 页面视图
│   │   │   ├── Login.vue            # 登录页面
│   │   │   ├── Dashboard.vue        # 仪表盘
│   │   │   ├── Tasks.vue            # 任务管理（列表、创建）
│   │   │   ├── TaskDetail.vue       # 任务详情（分配、编辑）
│   │   │   ├── Annotate.vue         # 标注页面（多工具、Tab切换）
│   │   │   ├── QualityControl.vue   # 质量控制（审核、统计）
│   │   │   ├── Export.vue           # 导出管理（新增✨）
│   │   │   ├── Users.vue            # 用户管理
│   │   │   └── Profile.vue          # 个人信息
│   │   ├── stores/                  # Pinia 状态管理
│   │   │   └── auth.js              # 认证状态
│   │   ├── router/                  # Vue Router 配置
│   │   │   └── index.js             # 路由定义、导航守卫
│   │   ├── utils/                   # 工具函数
│   │   │   └── api.js               # Axios 实例、拦截器
│   │   ├── layouts/                 # 布局组件
│   │   │   └── MainLayout.vue       # 主布局（侧边栏、头部）
│   │   ├── App.vue                  # 根组件
│   │   ├── main.js                  # 应用入口
│   │   └── style.css                # 全局样式
│   ├── package.json                 # NPM 依赖
│   └── vite.config.js              # Vite 配置
├── install.sh                       # 一键安装脚本
├── start.sh                         # 一键启动脚本
├── stop.sh                          # 一键停止脚本
└── README.md                        # 项目文档
```

## 💡 使用指南

### 完整工作流程

#### 1️⃣ 管理员创建任务
```
登录后台 → 任务管理 → 新建任务
├─ 设置任务信息（名称、描述、优先级）
├─ 选择标注类型（边界框、多边形、关键点、分类、回归）
├─ 定义标签列表（如：人、车、狗等）
├─ 上传图像（单文件或文件夹批量上传）
└─ 保存任务
```

#### 2️⃣ 分配任务给标注员
```
任务详情页 → 分配任务
├─ 选择标注员（支持多选）
├─ 设置每张图像需要的标注数量（如：3人标注同一张图）
└─ 确定分配
```

#### 3️⃣ 标注员进行标注
```
我的任务 → 选择任务 → 开始标注
├─ 查看任务要求和标签列表
├─ 使用标注工具进行标注
│   ├─ 边界框：拖拽创建矩形框
│   ├─ 多边形：点击创建多边形顶点
│   ├─ 关键点：点击标记关键点
│   ├─ 分类：选择分类标签
│   └─ 回归：输入数值
├─ 保存当前图像标注
└─ 自动跳转到下一张未标注图像
```

#### 4️⃣ 管理员审核标注
```
质量控制 → 待审核列表
├─ 查看标注详情
├─ 单个审核（通过/拒绝）
├─ 批量审核（批量通过/批量拒绝）
└─ 添加审核备注
```

#### 5️⃣ 导出标注数据
```
导出管理 → 新建导出
├─ 选择任务
├─ 选择导出格式（CSV、JSON、COCO、YOLO、Pascal VOC）
├─ 设置导出选项（是否包含图像、状态过滤）
├─ 开始导出（异步处理）
├─ 查看导出进度
└─ 下载导出文件
```

### 标注工具使用技巧

#### 边界框标注
- **创建**：鼠标左键拖拽
- **移动**：点击选中后拖拽
- **调整大小**：拖拽边框控制点
- **删除**：选中后点击删除按钮

#### 多边形标注
- **创建**：点击创建顶点，双击或点击起点完成
- **编辑**：拖拽顶点调整形状
- **删除**：选中后点击删除按钮

#### 关键点标注
- **创建**：点击图像添加关键点
- **移动**：拖拽关键点调整位置
- **删除**：选中后点击删除按钮

#### 分类和回归标注
- **分类**：从下拉列表选择分类标签
- **回归**：输入数值（如：年龄、距离等）
- **保存**：点击保存按钮

## 🔧 开发指南

### 后端开发

#### 添加新的API端点
```python
# 1. 在 app/routes/ 下创建新路由文件
# app/routes/my_feature.py
from fastapi import APIRouter, Depends
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/my-feature", tags=["My Feature"])

@router.get("/")
async def get_items(current_user = Depends(get_current_user)):
    return {"items": []}

# 2. 在 main.py 中注册路由
from app.routes import my_feature
app.include_router(my_feature.router)
```

#### 添加新的数据模型
```python
# 1. 在 app/models/ 下创建模型文件
# app/models/my_model.py
from sqlalchemy import Column, Integer, String
from app.database import Base

class MyModel(Base):
    __tablename__ = "my_table"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))

# 2. 在 app/models/__init__.py 中导出
from .my_model import MyModel
__all__ = [..., "MyModel"]

# 3. 创建数据库表
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### 前端开发

#### 添加新页面
```vue
<!-- 1. 在 src/views/ 下创建Vue组件 -->
<!-- src/views/MyPage.vue -->
<template>
  <div>
    <h1>My Page</h1>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/utils/api'

const data = ref([])
// ... your logic
</script>

<!-- 2. 在 src/router/index.js 中添加路由 -->
{
  path: '/my-page',
  name: 'MyPage',
  component: () => import('@/views/MyPage.vue'),
  meta: { requiresAuth: true, roles: ['admin'] }
}
```

#### 调用API
```javascript
// src/utils/api.js 已配置好 axios 实例
import api from '@/utils/api'

// GET 请求
const data = await api.get('/api/my-feature/')

// POST 请求
const result = await api.post('/api/my-feature/', { name: 'test' })

// 错误处理会自动通过拦截器显示
```

## ❓ 常见问题

### 安装和配置

**Q: 安装时提示缺少依赖？**

A: 确保已安装Python 3.8+和Node.js 16+：
```bash
python --version  # 应该 >= 3.8
node --version    # 应该 >= 16
```

**Q: 如何重置管理员密码？**

A: 运行以下命令：
```bash
cd backend
source venv/bin/activate
python -c "from app.database import SessionLocal; from app.models.user import User; from app.utils.auth import get_password_hash; db = SessionLocal(); admin = db.query(User).filter(User.username == 'admin').first(); admin.hashed_password = get_password_hash('new_password'); db.commit(); print('密码已重置')"
```

**Q: 端口被占用怎么办？**

A: 停止占用端口的进程：
```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9  # 后端端口
lsof -ti:3000 | xargs kill -9  # 前端端口

# 或使用停止脚本
./stop.sh
```

### 数据管理

**Q: 如何备份标注数据？**

A: 备份SQLite数据库文件：
```bash
cp backend/datalabels.db backend/datalabels_backup_$(date +%Y%m%d).db
```

**Q: 支持哪些图像格式？**

A: 支持所有常见格式：`jpg`、`jpeg`、`png`、`bmp`、`gif`、`tiff`、`webp`

**Q: 如何批量上传图像？**

A: 两种方式：
1. **单文件上传**：在任务详情页拖拽多个文件
2. **文件夹上传**（推荐）：输入文件夹路径，系统自动递归上传

**Q: 导出的数据在哪里？**

A: 导出文件保存在 `backend/static/exports/` 目录，也可在"导出管理"页面下载。

### 功能使用

**Q: 任务状态不更新？**

A: 任务状态会自动更新：
- **进行中**：有标注员开始标注
- **已完成**：所有图像都已标注
- **已审核**：所有图像都已审核通过

如果状态未更新，检查后端日志是否有错误。

**Q: 标注员看不到任务？**

A: 确保：
1. 任务已分配给该标注员
2. 标注员账号已激活
3. 刷新页面或重新登录

**Q: 导出历史为空？**

A: 导出历史现在持久化存储到数据库，服务重启后也不会丢失。如果仍为空，说明没有导出记录。

### 权限问题

**Q: 管理员能标注吗？**

A: 不能。管理员专注于审核和管理，不能参与标注。如需标注，请使用标注员或工程师账号。

**Q: 标注员能审核吗？**

A: 不能。只有管理员可以审核标注。

**Q: 如何修改用户角色？**

A: 管理员在"用户管理"页面可以修改用户角色。

## 🚀 生产部署

### 使用 Systemd 管理服务

创建服务文件：

```ini
# /etc/systemd/system/dataannotate-backend.service
[Unit]
Description=DataAnnotate Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/DataAnnotate/backend
Environment="PATH=/path/to/DataAnnotate/backend/venv/bin"
ExecStart=/path/to/DataAnnotate/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl enable dataannotate-backend
sudo systemctl start dataannotate-backend
sudo systemctl status dataannotate-backend
```

### Nginx 反向代理

```nginx
# /etc/nginx/sites-available/dataannotate
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /path/to/DataAnnotate/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 静态文件
    location /static {
        alias /path/to/DataAnnotate/backend/static;
    }
}
```

### 环境变量配置

创建 `.env` 文件：

```bash
# backend/.env
DATABASE_URL=postgresql://user:password@localhost/dataannotate
SECRET_KEY=your-super-secret-key-change-this
ENVIRONMENT=production
```

### 性能优化建议

1. **数据库**：生产环境使用 PostgreSQL
2. **缓存**：配置 Redis 缓存（未来版本）
3. **静态文件**：使用 CDN 或 Nginx 直接提供
4. **图像处理**：考虑使用对象存储（如 S3）
5. **负载均衡**：多实例部署 + Nginx 负载均衡

## 🤝 贡献指南

我们欢迎所有形式的贡献！无论是新功能、Bug修复、文档改进还是问题反馈。

### 如何贡献

1. **Fork 项目**
   ```bash
   # 在 GitHub 上 Fork 项目
   git clone https://github.com/YOUR_USERNAME/DataAnnotate.git
   cd DataAnnotate
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/my-new-feature
   # 或
   git checkout -b fix/bug-description
   ```

3. **进行开发**
   - 遵循项目现有的代码风格
   - 添加必要的测试
   - 更新相关文档

4. **提交更改**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   # 提交信息格式：
   # feat: 新功能
   # fix: 修复Bug
   # docs: 文档更新
   # style: 代码格式调整
   # refactor: 重构
   # test: 测试相关
   ```

5. **推送到分支**
   ```bash
   git push origin feature/my-new-feature
   ```

6. **创建 Pull Request**
   - 在 GitHub 上创建 PR
   - 详细描述你的更改
   - 等待审核和讨论

### 开发规范

- **Python 代码**: 遵循 PEP 8 规范
- **JavaScript 代码**: 使用 ESLint 和 Prettier
- **提交信息**: 使用语义化提交信息
- **文档**: 更新相关的 README 和 API 文档

### 报告 Bug

在 [GitHub Issues](https://github.com/PengBY91/DataAnnotate/issues) 提交 Bug 报告时，请包含：

- 详细的问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Python版本、Node.js版本等）
- 错误日志（如果有）

### 功能建议

欢迎提出新功能建议！请在 Issues 中描述：

- 功能的使用场景
- 预期的功能行为
- 可能的实现方案（如果有想法）

## 📝 更新日志

### v1.0.0 (2025-01)
- ✨ 核心功能发布
- ✅ 支持多种标注类型（边界框、多边形、关键点、分类、回归）
- ✅ 完整的任务管理和用户权限系统
- ✅ 质量控制和批量审核
- ✅ 多格式数据导出（CSV、JSON、COCO、YOLO、Pascal VOC）
- ✅ 导出历史数据库持久化
- ✅ 任务状态自动更新
- ✅ Tab页标注工具切换
- ✅ 多标注员协作支持

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

```
MIT License

Copyright (c) 2025 DataAnnotate Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 📞 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 📧 **邮箱**: baoyun20@gmail.com
- 🐙 **GitHub**: [https://github.com/PengBY91/DataAnnotate](https://github.com/PengBY91/DataAnnotate)
- 💬 **Issues**: [提交问题](https://github.com/PengBY91/DataAnnotate/issues)
- 🔀 **Pull Requests**: [贡献代码](https://github.com/PengBY91/DataAnnotate/pulls)

## ⭐ 致谢

感谢所有为本项目做出贡献的开发者！

如果这个项目对你有帮助，欢迎 Star ⭐ 支持我们！

---

**Made with ❤️ by the DataAnnotate Team**