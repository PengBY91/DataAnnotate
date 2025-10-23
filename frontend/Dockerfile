FROM node:18-alpine

WORKDIR /app

# 设置npm镜像源（加速下载）
RUN npm config set registry https://registry.npmmirror.com

# 复制package文件
COPY package*.json ./

# 安装依赖（添加超时和重试机制）
RUN npm install --timeout=300000 --retry=3 --no-audit --no-fund

# 复制源代码
COPY . .

# 暴露端口
EXPOSE 3000

# 启动开发服务器
CMD ["npm", "run", "dev"]
