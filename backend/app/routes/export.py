"""
标注结果导出API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import zipfile
import io
import os
from datetime import datetime
from app.database import get_db
from app.models.user import User, UserRole
from app.models.annotation import Annotation, AnnotationStatus
from app.models.image import Image
from app.models.task import Task
from app.schemas.export import ExportRequest, ExportResponse, ExportProgress
from app.utils.auth import get_current_user
from app.services.export_service import ExportService

router = APIRouter()

# 全局导出服务实例
export_service = ExportService()

@router.post("/export", response_model=ExportResponse)
async def export_annotations(
    export_request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出标注结果"""
    # 只有管理员、算法工程师和审核员可以导出
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 验证任务存在
    task = db.query(Task).filter(Task.id == export_request.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    try:
        # 开始导出
        export_id = await export_service.start_export(
            task_id=export_request.task_id,
            format=export_request.format,
            include_images=export_request.include_images,
            status_filter=export_request.status_filter,
            user_id=current_user.id
        )
        
        return ExportResponse(
            export_id=export_id,
            task_id=export_request.task_id,
            format=export_request.format,
            status="processing",
            message="导出任务已创建，正在处理中..."
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )

@router.get("/{export_id}/status", response_model=ExportProgress)
async def get_export_status(
    export_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导出进度"""
    
    try:
        progress = await export_service.get_export_progress(export_id)
        return progress
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"导出任务不存在: {str(e)}"
        )

@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载导出文件"""
    
    try:
        file_path = await export_service.get_export_file(export_id)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="导出文件不存在"
            )
        
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type='application/zip'
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"下载失败: {str(e)}"
        )

@router.get("/formats")
async def get_export_formats():
    """获取支持的导出格式"""
    return {
        "formats": [
            {
                "name": "Pascal VOC",
                "value": "pascal_voc",
                "description": "Pascal VOC XML格式，适用于目标检测任务",
                "extensions": [".xml"]
            },
            {
                "name": "COCO",
                "value": "coco",
                "description": "COCO JSON格式，适用于多种计算机视觉任务",
                "extensions": [".json"]
            },
            {
                "name": "YOLO",
                "value": "yolo",
                "description": "YOLO格式，适用于目标检测任务",
                "extensions": [".txt"]
            },
            {
                "name": "JSON",
                "value": "json",
                "description": "通用JSON格式，包含完整的标注信息",
                "extensions": [".json"]
            }
        ]
    }

@router.get("/history")
async def get_export_history(
    task_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取导出历史"""
    # 只有管理员、算法工程师和审核员可以查看导出历史
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    
    try:
        history = await export_service.get_export_history(
            user_id=current_user.id,
            task_id=task_id,
            skip=skip,
            limit=limit
        )
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取导出历史失败: {str(e)}"
        )
