#!/bin/bash

# 图像数据标注管理系统安装脚本

echo "🔧 安装图像数据标注管理系统..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python 3.11+"
    exit 1
fi

# 检查Node.js是否安装
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js 18+"
    exit 1
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p backend/static/uploads
mkdir -p frontend/node_modules

# 复制环境变量文件
if [ ! -f backend/.env ]; then
    echo "📝 创建环境变量文件..."
    cp backend/.env.example backend/.env
fi

# 安装后端依赖
echo "🐍 安装后端依赖..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# 安装前端依赖
echo "🟢 安装前端依赖..."
cd frontend
npm install
cd ..

# 创建默认管理员用户
echo "👤 创建默认管理员用户..."
cd backend
source venv/bin/activate
python -c "
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash

db = SessionLocal()
try:
    admin_user = db.query(User).filter(User.username == 'admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            full_name='系统管理员',
            role=UserRole.ADMIN,
            hashed_password=get_password_hash('admin123'),
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print('✅ 默认管理员用户创建成功')
    else:
        print('ℹ️  管理员用户已存在')
finally:
    db.close()
"
cd ..

echo ""
echo "✅ 安装完成！"
echo ""
echo "🚀 运行以下命令启动系统："
echo "   ./start.sh"
echo ""
echo "📋 系统信息："
echo "   前端界面: http://localhost:3000"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "👤 默认管理员账户："
echo "   用户名: admin"
echo "   密码: admin123"