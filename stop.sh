#!/bin/bash

# 图像数据标注管理系统停止脚本

echo "🛑 停止图像数据标注管理系统..."

# 停止后端服务
if [ -f .backend.pid ]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null; then
        echo "🐍 停止后端服务..."
        kill $BACKEND_PID
    fi
    rm .backend.pid
fi

# 停止前端服务
if [ -f .frontend.pid ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null; then
        echo "🟢 停止前端服务..."
        kill $FRONTEND_PID
    fi
    rm .frontend.pid
fi

echo "✅ 系统已停止"