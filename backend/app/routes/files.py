"""
文件管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from app.database import get_db
from app.models.user import User, UserRole
from app.models.task import Task
from app.models.image import Image
from app.utils.auth import get_current_user
from app.config import settings

# 尝试导入PIL，如果失败则使用替代方案
try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

router = APIRouter()

@router.post("/upload")
async def upload_images(
    task_id: int = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传图像文件"""
    # 验证任务存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查：只有管理员、算法工程师或任务创建者可以上传
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if task.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
    
    # 确保上传目录存在
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(task_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    uploaded_files = []
    
    for file in files:
        # 验证文件类型
        if not any(file.filename.lower().endswith(ext) for ext in settings.SUPPORTED_IMAGE_FORMATS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file.filename}"
            )
        
        # 验证文件大小
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件过大: {file.filename}"
            )
        
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 获取图像信息
        if PIL_AVAILABLE:
            try:
                with PILImage.open(file_path) as img:
                    width, height = img.size
            except Exception:
                # 如果无法读取图像信息，删除文件
                os.remove(file_path)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无法读取图像文件: {file.filename}"
                )
        else:
            # 如果没有PIL，使用默认值
            width, height = 800, 600
        
        # 保存到数据库
        db_image = Image(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=len(content),
            width=width,
            height=height,
            task_id=task_id
        )
        
        db.add(db_image)
        uploaded_files.append({
            "filename": file.filename,
            "saved_filename": unique_filename,
            "size": len(content),
            "dimensions": f"{width}x{height}"
        })
    
    # 更新任务图像数量
    task.total_images = db.query(Image).filter(Image.task_id == task_id).count()
    
    db.commit()
    
    return {
        "message": f"成功上传 {len(uploaded_files)} 个文件",
        "files": uploaded_files
    }

@router.get("/task/{task_id}")
async def get_task_images(
    task_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务的图像列表"""
    # 验证任务存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role == UserRole.ANNOTATOR and task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    images = db.query(Image).filter(Image.task_id == task_id).offset(skip).limit(limit).all()
    
    return [
        {
            "id": img.id,
            "filename": img.original_filename,
            "width": img.width,
            "height": img.height,
            "is_annotated": img.is_annotated,
            "is_reviewed": img.is_reviewed,
            "created_at": img.created_at
        }
        for img in images
    ]

@router.get("/{image_id}")
async def get_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取图像详情"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )
    
    # 权限检查
    if current_user.role == UserRole.ANNOTATOR and image.task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    return {
        "id": image.id,
        "filename": image.original_filename,
        "width": image.width,
        "height": image.height,
        "is_annotated": image.is_annotated,
        "is_reviewed": image.is_reviewed,
        "annotation_data": image.annotation_data,
        "created_at": image.created_at
    }

@router.delete("/{image_id}")
async def delete_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除图像"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )
    
    # 权限检查：只有管理员或任务创建者可以删除
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if image.task.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
    
    # 删除文件
    if os.path.exists(image.file_path):
        os.remove(image.file_path)
    
    # 删除数据库记录
    db.delete(image)
    db.commit()
    
    return {"message": "图像已删除"}
