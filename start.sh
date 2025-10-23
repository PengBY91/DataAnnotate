#!/bin/bash

# 图像数据标注管理系统启动脚本

echo "🚀 启动图像数据标注管理系统..."

# 启动后端服务
echo "🐍 启动后端服务..."
cd backend
source venv/bin/activate

# 创建数据库文件（如果不存在）
touch datalabels.db

# 启动应用
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# 启动前端服务
echo "🟢 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# 保存进程ID
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

echo ""
echo "✅ 系统启动完成！"
echo ""
echo "📋 服务访问地址："
echo "   前端界面: http://localhost:3000 (或更高端口)"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "👤 默认管理员账户："
echo "   用户名: admin"
echo "   密码: admin123"
echo ""
echo "🛑 停止服务："
echo "   ./stop.sh"