"""
标注管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User, UserRole
from app.models.annotation import Annotation, AnnotationStatus
from app.models.image import Image
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate, AnnotationResponse, ImageAnnotation
from app.utils.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=AnnotationResponse)
async def create_annotation(
    annotation: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建标注"""
    # 验证图像存在
    image = db.query(Image).filter(Image.id == annotation.image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )
    
    # 检查权限：只有被分配任务的标注员可以创建标注
    if current_user.role == UserRole.ANNOTATOR:
        if not image.task or image.task.assignee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
    
    db_annotation = Annotation(
        annotation_type=annotation.annotation_type,
        label=annotation.label,
        data=annotation.data,
        notes=annotation.notes,
        image_id=annotation.image_id,
        annotator_id=current_user.id
    )
    
    db.add(db_annotation)
    db.commit()
    db.refresh(db_annotation)
    
    return db_annotation

@router.get("/", response_model=List[AnnotationResponse])
async def get_annotations(
    image_id: Optional[int] = None,
    task_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取标注列表"""
    query = db.query(Annotation)
    
    # 根据用户角色过滤
    if current_user.role == UserRole.ANNOTATOR:
        query = query.filter(Annotation.annotator_id == current_user.id)
    elif current_user.role == UserRole.REVIEWER:
        query = query.filter(Annotation.reviewer_id == current_user.id)
    # 管理员和算法工程师可以看到所有标注
    
    if image_id:
        query = query.filter(Annotation.image_id == image_id)
    
    if task_id:
        query = query.join(Image).filter(Image.task_id == task_id)
    
    annotations = query.offset(skip).limit(limit).all()
    return annotations

@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定标注详情"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在"
        )
    
    # 权限检查
    if (current_user.role == UserRole.ANNOTATOR and annotation.annotator_id != current_user.id) or \
       (current_user.role == UserRole.REVIEWER and annotation.reviewer_id != current_user.id):
        if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
    
    return annotation

@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: int,
    annotation_update: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新标注"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在"
        )
    
    # 权限检查：只有创建者可以更新，或者审核员可以审核
    if current_user.role == UserRole.ANNOTATOR and annotation.annotator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 更新标注信息
    update_data = annotation_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(annotation, field, value)
    
    db.commit()
    db.refresh(annotation)
    
    return annotation

@router.post("/{annotation_id}/review")
async def review_annotation(
    annotation_id: int,
    status: AnnotationStatus,
    review_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """审核标注"""
    if current_user.role not in [UserRole.ADMIN, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在"
        )
    
    annotation.status = status
    annotation.reviewer_id = current_user.id
    annotation.review_notes = review_notes
    
    db.commit()
    
    return {"message": "标注审核完成"}

@router.delete("/{annotation_id}")
async def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除标注"""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在"
        )
    
    # 权限检查：只有创建者或管理员可以删除
    if annotation.annotator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    db.delete(annotation)
    db.commit()
    
    return {"message": "标注已删除"}
