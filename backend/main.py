"""
图像数据标注管理系统 - 主应用入口
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.routes import auth, tasks, annotations, users, files, quality_control, export
from app.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="图像数据标注管理系统",
    description="一个完整的图像数据标注管理平台",
    version="1.0.0"
)

# 健康检查端点
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "服务运行正常"}

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务管理"])
app.include_router(annotations.router, prefix="/api/annotations", tags=["标注管理"])
app.include_router(files.router, prefix="/api/files", tags=["文件管理"])
app.include_router(quality_control.router, prefix="/api/quality", tags=["质量控制"])
app.include_router(export.router, prefix="/api/export", tags=["导出管理"])

@app.get("/")
async def root():
    return {"message": "图像数据标注管理系统 API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
