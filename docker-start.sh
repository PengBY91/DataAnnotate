#!/bin/bash

# 图像数据标注管理系统 - Docker 启动脚本

echo "🚀 启动图像数据标注管理系统 (Docker 模式)"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 停止现有容器
echo "🛑 停止现有容器..."
docker-compose down

# 清理未使用的镜像（可选）
read -p "是否清理未使用的 Docker 镜像？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 清理未使用的镜像..."
    docker system prune -f
fi

# 构建并启动服务
echo "🔨 构建并启动服务..."
docker-compose up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 检查健康状态
echo "🏥 检查服务健康状态..."
echo "后端健康检查:"
curl -f http://localhost:8000/health 2>/dev/null && echo "✅ 后端服务正常" || echo "❌ 后端服务异常"

echo "前端健康检查:"
curl -f http://localhost:3000 2>/dev/null && echo "✅ 前端服务正常" || echo "❌ 前端服务异常"

echo ""
echo "🎉 服务启动完成！"
echo "📱 前端界面: http://localhost:3000"
echo "🔧 后端API: http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "👤 默认管理员: admin / admin123"
echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"
