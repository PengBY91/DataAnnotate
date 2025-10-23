"""
应用配置
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # 应用配置
    APP_NAME = "图像数据标注管理系统"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/datalabels")
    
    # JWT配置
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # 文件存储配置
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "static/uploads")
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    # Redis配置（用于缓存和任务队列）
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # 标注工具配置
    SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]
    SUPPORTED_ANNOTATION_TYPES = ["bbox", "polygon", "keypoint", "classification"]
    
    # 导出格式配置
    EXPORT_FORMATS = ["pascal_voc", "coco", "yolo", "json"]

settings = Settings()
