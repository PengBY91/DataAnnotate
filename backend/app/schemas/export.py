"""
导出相关的数据模式
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.annotation import AnnotationStatus

class ExportRequest(BaseModel):
    """导出请求"""
    task_id: int
    format: str  # pascal_voc, coco, yolo, json
    include_images: bool = False
    status_filter: Optional[List[AnnotationStatus]] = None
    image_ids: Optional[List[int]] = None  # 指定要导出的图像ID列表

class ExportResponse(BaseModel):
    """导出响应"""
    export_id: str
    task_id: int
    format: str
    status: str  # processing, completed, failed
    message: str
    created_at: datetime = datetime.now()

class ExportProgress(BaseModel):
    """导出进度"""
    export_id: str
    status: str
    progress: int  # 0-100
    message: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ExportHistoryItem(BaseModel):
    """导出历史项"""
    export_id: str
    task_id: int
    task_title: str
    format: str
    status: str
    file_path: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class ExportFormat(BaseModel):
    """导出格式"""
    name: str
    value: str
    description: str
    extensions: List[str]
