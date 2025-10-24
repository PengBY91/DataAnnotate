"""
质量控制API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.user import User, UserRole
from app.models.annotation import Annotation, AnnotationStatus
from app.models.image import Image
from app.models.task import Task
from app.schemas.quality_control import (
    QualityReviewCreate, QualityReviewResponse,
    QualityMetrics, AnnotationReview, ReviewStats
)
from app.utils.auth import get_current_user

router = APIRouter()

@router.get("/pending-reviews", response_model=List[QualityReviewResponse])
async def get_pending_reviews(
    skip: int = 0,
    limit: int = 100,
    task_id: Optional[int] = None,
    annotator_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取待审核的标注列表"""
    # 只有管理员可以查看待审核列表
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问质量控制"
        )
    
    query = db.query(Annotation).filter(
        Annotation.status == AnnotationStatus.SUBMITTED
    )
    
    if task_id:
        query = query.join(Image).filter(Image.task_id == task_id)
    
    if annotator_id:
        query = query.filter(Annotation.annotator_id == annotator_id)
    
    annotations = query.offset(skip).limit(limit).all()
    
    # 转换为审核格式
    reviews = []
    for annotation in annotations:
        review = QualityReviewResponse(
            id=annotation.id,
            image_id=annotation.image_id,
            task_id=annotation.image.task_id,
            annotator_id=annotation.annotator_id,
            annotator_name=annotation.annotator.full_name if annotation.annotator else "未知",
            annotation_type=annotation.annotation_type,
            label=annotation.label,
            data=annotation.data,
            notes=annotation.notes,
            created_at=annotation.created_at,
            image_filename=annotation.image.original_filename if annotation.image else "未知"
        )
        reviews.append(review)
    
    return reviews

@router.post("/review", response_model=dict)
async def review_annotation(
    review: QualityReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """审核标注"""
    # 只有管理员可以审核
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以审核标注"
        )
    
    annotation = db.query(Annotation).filter(
        Annotation.id == review.annotation_id
    ).first()
    
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标注不存在"
        )
    
    # 更新标注状态
    annotation.status = review.status
    annotation.reviewer_id = current_user.id
    annotation.review_notes = review.review_notes
    annotation.reviewed_at = datetime.now()
    
    # 更新图像状态
    # 检查该图像的所有标注状态
    all_annotations = db.query(Annotation).filter(
        Annotation.image_id == annotation.image_id
    ).all()
    
    # 统计各种状态的标注数量
    total_annotations = len(all_annotations)
    approved_annotations = sum(1 for ann in all_annotations if ann.status == AnnotationStatus.APPROVED)
    rejected_annotations = sum(1 for ann in all_annotations if ann.status == AnnotationStatus.REJECTED)
    pending_annotations = sum(1 for ann in all_annotations if ann.status == AnnotationStatus.SUBMITTED)
    
    # 更新图像状态
    if total_annotations > 0:
        # 确保图像标记为已标注
        annotation.image.is_annotated = True
        
        # 如果所有标注都已审核（通过或拒绝），且没有待审核的标注
        if pending_annotations == 0:
            # 如果所有标注都已通过，标记为已审核
            if approved_annotations == total_annotations and rejected_annotations == 0:
                annotation.image.is_reviewed = True
                annotation.image.reviewed_at = datetime.now()
            # 如果有被拒绝的标注，标记为未审核
            elif rejected_annotations > 0:
                annotation.image.is_reviewed = False
                annotation.image.reviewed_at = None
        
        # 更新任务的审核统计
        if annotation.image.task:
            reviewed_count = db.query(Image).filter(
                Image.task_id == annotation.image.task_id,
                Image.is_reviewed == True
            ).count()
            annotation.image.task.reviewed_images = reviewed_count
    
    db.commit()
    
    return {"message": "审核完成", "status": review.status.value}

@router.get("/metrics/{task_id}", response_model=QualityMetrics)
async def get_quality_metrics(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务质量指标"""
    # 只有管理员可以查看质量指标
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问质量控制"
        )
    
    # 获取任务信息
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 计算质量指标 - 按图像数量计算
    total_images = db.query(Image).filter(Image.task_id == task_id).count()
    
    # 已审核的图像数量（所有标注都已审核通过或拒绝）
    reviewed_images = db.query(Image).filter(
        Image.task_id == task_id,
        Image.is_reviewed == True
    ).count()
    
    # 已通过审核的图像数量（所有标注都已通过）
    approved_images = 0
    rejected_images = 0
    pending_images = 0
    
    # 遍历所有图像，统计状态
    images = db.query(Image).filter(Image.task_id == task_id).all()
    for image in images:
        # 获取该图像的所有标注
        annotations = db.query(Annotation).filter(Annotation.image_id == image.id).all()
        
        if not annotations:
            continue
            
        # 统计标注状态
        has_approved = any(ann.status == AnnotationStatus.APPROVED for ann in annotations)
        has_rejected = any(ann.status == AnnotationStatus.REJECTED for ann in annotations)
        has_submitted = any(ann.status == AnnotationStatus.SUBMITTED for ann in annotations)
        
        if has_submitted:
            pending_images += 1
        elif has_approved and not has_rejected and not has_submitted:
            approved_images += 1
        elif has_rejected:
            rejected_images += 1
    
    # 计算通过率（按图像数量）
    if reviewed_images > 0:
        approval_rate = (approved_images / reviewed_images) * 100
    else:
        approval_rate = 0
    
    # 按标注员统计 - 按图像数量计算
    annotator_metrics = []
    
    # 获取所有参与标注的用户
    annotator_ids = db.query(Annotation.annotator_id).join(Image).filter(
        Image.task_id == task_id
    ).distinct().all()
    
    for annotator_id_tuple in annotator_ids:
        annotator_id = annotator_id_tuple[0]
        user = db.query(User).filter(User.id == annotator_id).first()
        if not user:
            continue
            
        # 获取该标注员标注的所有图像
        user_images = db.query(Image).join(Annotation).filter(
            Image.task_id == task_id,
            Annotation.annotator_id == annotator_id
        ).distinct().all()
        
        total_images = len(user_images)
        approved_images = 0
        rejected_images = 0
        
        # 统计该标注员的图像状态
        for image in user_images:
            annotations = db.query(Annotation).filter(
                Annotation.image_id == image.id,
                Annotation.annotator_id == annotator_id
            ).all()
            
            if not annotations:
                continue
                
            has_approved = any(ann.status == AnnotationStatus.APPROVED for ann in annotations)
            has_rejected = any(ann.status == AnnotationStatus.REJECTED for ann in annotations)
            has_submitted = any(ann.status == AnnotationStatus.SUBMITTED for ann in annotations)
            
            if has_approved and not has_rejected and not has_submitted:
                approved_images += 1
            elif has_rejected:
                rejected_images += 1
        
        approval_rate = (approved_images / total_images * 100) if total_images > 0 else 0
        
        annotator_metrics.append({
            "annotator_id": annotator_id,
            "annotator_name": user.full_name,
            "total_annotations": total_images,  # 总图像数
            "approved_count": approved_images,  # 已通过图像数
            "rejected_count": rejected_images,  # 已拒绝图像数
            "approval_rate": approval_rate
        })
    
    return QualityMetrics(
        task_id=task_id,
        total_annotations=total_images,  # 总图像数
        approved_annotations=approved_images,  # 已通过图像数
        rejected_annotations=rejected_images,  # 已拒绝图像数
        pending_annotations=pending_images,  # 待审核图像数
        approval_rate=approval_rate,
        annotator_metrics=annotator_metrics
    )

@router.get("/review-stats", response_model=ReviewStats)
async def get_review_stats(
    reviewer_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取审核统计信息"""
    # 只有管理员可以查看统计
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以访问质量控制"
        )
    
    # 计算时间范围
    from datetime import datetime, timedelta
    start_date = datetime.now() - timedelta(days=days)
    
    query = db.query(Annotation).filter(
        Annotation.reviewer_id == (reviewer_id or current_user.id),
        Annotation.reviewed_at >= start_date
    )
    
    total_reviews = query.count()
    approved_reviews = query.filter(
        Annotation.status == AnnotationStatus.APPROVED
    ).count()
    rejected_reviews = query.filter(
        Annotation.status == AnnotationStatus.REJECTED
    ).count()
    
    return ReviewStats(
        reviewer_id=reviewer_id or current_user.id,
        period_days=days,
        total_reviews=total_reviews,
        approved_reviews=approved_reviews,
        rejected_reviews=rejected_reviews,
        approval_rate=(approved_reviews / total_reviews * 100) if total_reviews > 0 else 0
    )
