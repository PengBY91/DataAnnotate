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
from app.models.annotation import Annotation, AnnotationStatus
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
    files: UploadFile = File(...),  # 改为单个文件
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传图像文件"""
    print(f"收到上传请求: task_id={task_id}, 文件名={files.filename}")
    
    # 验证任务存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        print(f"任务不存在: task_id={task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查：只有管理员、算法工程师或任务创建者可以上传
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        if task.creator_id != current_user.id:
            print(f"权限不足: user_id={current_user.id}, creator_id={task.creator_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
    
    # 确保上传目录存在
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(task_id))
    os.makedirs(upload_dir, exist_ok=True)
    print(f"上传目录: {upload_dir}")
    
    uploaded_files = []
    file_list = [files]  # 转换为列表以保持后续代码兼容
    
    for file in file_list:
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
    
    print(f"上传成功: {uploaded_files}")
    
    return {
        "message": "上传成功",
        "file": uploaded_files[0] if uploaded_files else None
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
    if current_user.role == UserRole.ANNOTATOR:
        # 检查旧的分配方式
        if task.assignee_id != current_user.id:
            # 检查新的分配方式
            from app.models.task_assignment import TaskAssignment
            is_assigned = db.query(TaskAssignment).filter(
                TaskAssignment.task_id == task_id,
                TaskAssignment.user_id == current_user.id,
                TaskAssignment.role == "annotator"
            ).first() is not None
            
            if not is_assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
    
    images = db.query(Image).filter(Image.task_id == task_id).offset(skip).limit(limit).all()
    
    result = []
    for img in images:
        # 如果是标注员，显示自己的标注状态；如果是管理员，显示整体状态
        if current_user.role == UserRole.ANNOTATOR:
            # 获取当前标注员对该图像的标注
            user_annotations = db.query(Annotation).filter(
                Annotation.image_id == img.id,
                Annotation.annotator_id == current_user.id
            ).all()
            
            annotation_count = len(user_annotations)
            
            # 确定当前标注员的标注状态
            if annotation_count == 0:
                annotation_status = "未标注"
                has_rejected = False
            else:
                # 获取最新的标注状态
                latest_annotation = max(user_annotations, key=lambda a: a.created_at)
                if latest_annotation.status == AnnotationStatus.SUBMITTED:
                    annotation_status = "待审核"
                    has_rejected = False
                elif latest_annotation.status == AnnotationStatus.APPROVED:
                    annotation_status = "已通过"
                    has_rejected = False
                elif latest_annotation.status == AnnotationStatus.REJECTED:
                    annotation_status = "未通过"
                    has_rejected = True
                else:
                    annotation_status = "标注中"
                    has_rejected = False
        else:
            # 管理员看到的是所有标注的整体状态
            annotations = db.query(Annotation).filter(Annotation.image_id == img.id).all()
            
            annotation_count = len(annotations)
            has_rejected = any(ann.status == AnnotationStatus.REJECTED for ann in annotations)
            has_approved = any(ann.status == AnnotationStatus.APPROVED for ann in annotations)
            has_submitted = any(ann.status == AnnotationStatus.SUBMITTED for ann in annotations)
            has_draft = any(ann.status == AnnotationStatus.DRAFT for ann in annotations)
            
            # 确定图像的整体状态
            if annotation_count == 0:
                annotation_status = "未标注"
            elif has_submitted:
                annotation_status = "待审核"
            elif has_approved and not has_submitted:
                if has_rejected:
                    annotation_status = "未通过"
                else:
                    annotation_status = "已通过"
            elif has_draft:
                annotation_status = "标注中"
            else:
                annotation_status = "标注中"
        
        result.append({
            "id": img.id,
            "filename": img.original_filename,
            "file_path": f"/{img.file_path.replace(chr(92), '/')}" if not img.file_path.startswith('/') else img.file_path.replace(chr(92), '/'),
            "is_annotated": img.is_annotated,
            "is_reviewed": img.is_reviewed,
            "annotation_count": annotation_count,
            "annotation_status": annotation_status,
            "has_rejected": has_rejected,
            "folder_relative_path": img.folder_relative_path,
            "created_at": img.created_at
        })
    
    return result

@router.get("/task/{task_id}/next-unannotated")
async def get_next_unannotated_image(
    task_id: int,
    current_image_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取下一张未标注的图像"""
    from app.models.task_assignment import TaskAssignment
    from app.models.annotation import Annotation
    
    # 验证任务存在
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查 - 检查是否在分配列表中
    is_assigned = db.query(TaskAssignment).filter(
        TaskAssignment.task_id == task_id,
        TaskAssignment.user_id == current_user.id
    ).first() is not None
    
    if not is_assigned and task.assignee_id != current_user.id:
        if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
    
    # 查询未被当前用户标注的图像
    # 获取所有图像
    all_images = db.query(Image).filter(Image.task_id == task_id).order_by(Image.id).all()
    
    # 找到下一张需要标注的图像（未标注或标注被拒绝）
    for img in all_images:
        # 跳过当前图像之前的所有图像
        if current_image_id and img.id <= current_image_id:
            continue
        
        # 检查该图像的标注状态
        user_annotations = db.query(Annotation).filter(
            Annotation.image_id == img.id,
            Annotation.annotator_id == current_user.id
        ).all()
        
        # 如果没有标注，或者所有标注都被拒绝，则需要标注
        needs_annotation = (
            len(user_annotations) == 0 or  # 未标注
            all(ann.status == AnnotationStatus.REJECTED for ann in user_annotations)  # 所有标注都被拒绝
        )
        
        if needs_annotation:
            return {
                "id": img.id,
                "filename": img.original_filename,
                "file_path": f"/{img.file_path.replace(chr(92), '/')}" if not img.file_path.startswith('/') else img.file_path.replace(chr(92), '/'),
                "width": img.width,
                "height": img.height,
                "task_id": task_id
            }
    
    # 如果没有找到，返回第一张未标注的（从头开始）
    for img in all_images:
        user_annotation = db.query(Annotation).filter(
            Annotation.image_id == img.id,
            Annotation.annotator_id == current_user.id
        ).first()
        
        if not user_annotation:
            return {
                "id": img.id,
                "filename": img.original_filename,
                "file_path": f"/{img.file_path.replace(chr(92), '/')}" if not img.file_path.startswith('/') else img.file_path.replace(chr(92), '/'),
                "width": img.width,
                "height": img.height,
                "task_id": task_id
            }
    
    # 所有图像都已标注
    return None

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
    if current_user.role == UserRole.ANNOTATOR:
        # 检查旧的分配方式
        if image.task.assignee_id != current_user.id:
            # 检查新的分配方式
            from app.models.task_assignment import TaskAssignment
            is_assigned = db.query(TaskAssignment).filter(
                TaskAssignment.task_id == image.task.id,
                TaskAssignment.user_id == current_user.id,
                TaskAssignment.role == "annotator"
            ).first() is not None
            
            if not is_assigned:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
    
    # 构建可访问的 URL
    # 从 file_path 中提取相对路径
    # file_path 格式: static/uploads/1/xxx.jpg
    relative_path = image.file_path.replace('\\', '/')  # Windows 兼容
    image_url = f"/{relative_path}" if not relative_path.startswith('/') else relative_path
    
    return {
        "id": image.id,
        "filename": image.original_filename,
        "file_path": image_url,  # 返回可访问的 URL
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

@router.post("/upload-folder")
async def upload_folder(
    task_id: int = Form(...),
    folder_path: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文件夹中的所有图像"""
    print(f"收到文件夹上传请求: task_id={task_id}, 文件夹路径={folder_path}")
    
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
    
    # 检查文件夹是否存在
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件夹不存在或不是有效目录"
        )
    
    # 确保上传目录存在
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(task_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    uploaded_files = []
    supported_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
    
    # 遍历文件夹中的所有文件
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 检查文件扩展名
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()
            
            if file_ext not in supported_extensions:
                continue
            
            try:
                # 计算相对路径（相对于上传的文件夹）
                relative_path = os.path.relpath(file_path, folder_path)
                
                # 生成唯一文件名
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                target_path = os.path.join(upload_dir, unique_filename)
                
                # 复制文件
                import shutil
                shutil.copy2(file_path, target_path)
                
                # 获取图像信息
                if PIL_AVAILABLE:
                    try:
                        with PILImage.open(target_path) as img:
                            width, height = img.size
                    except Exception:
                        os.remove(target_path)
                        continue
                else:
                    width, height = 800, 600
                
                # 保存到数据库
                db_image = Image(
                    task_id=task_id,
                    original_filename=file,
                    file_path=target_path,
                    width=width,
                    height=height,
                    folder_relative_path=relative_path  # 记录文件夹内的相对路径
                )
                
                db.add(db_image)
                uploaded_files.append({
                    "filename": file,
                    "relative_path": relative_path,
                    "width": width,
                    "height": height
                })
                
            except Exception as e:
                print(f"处理文件失败 {file_path}: {e}")
                continue
    
    db.commit()
    
    return {
        "message": f"成功上传 {len(uploaded_files)} 个图像文件",
        "uploaded_files": uploaded_files,
        "count": len(uploaded_files)
    }
