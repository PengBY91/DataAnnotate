"""
标注管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User, UserRole
from app.models.annotation import Annotation, AnnotationStatus, AnnotationType
from app.models.image import Image
from app.schemas.annotation import AnnotationCreate, AnnotationUpdate, AnnotationResponse, ImageAnnotation
from app.utils.auth import get_current_user
from app.utils.ranking_validator import validate_ranking, format_ranking

router = APIRouter()

@router.post("", response_model=AnnotationResponse)
async def create_annotation(
    annotation: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建标注"""
    # 管理员不能参与标注
    if current_user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员不能参与标注，只能审核"
        )
    
    # 验证图像存在
    image = db.query(Image).filter(Image.id == annotation.image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )
    
    # 检查权限：只有被分配任务的标注员可以创建标注
    if current_user.role == UserRole.ANNOTATOR:
        if not image.task:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
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
    
    # 检查该用户是否已经标注过此图像（在插入新标注之前检查）
    existing_count = db.query(Annotation).filter(
        Annotation.image_id == annotation.image_id,
        Annotation.annotator_id == current_user.id
    ).count()
    
    # 如果是排序类型，验证输入合法性
    if annotation.annotation_type == AnnotationType.RANKING:
        # 从data中获取ranking字符串
        ranking_str = annotation.data.get("ranking", "")
        expected_count = annotation.data.get("expected_count")
        
        # 验证排序
        is_valid, error_msg = validate_ranking(ranking_str, expected_count)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"排序格式错误: {error_msg}"
            )
        
        # 将排序字符串转换为列表存储
        annotation.data["ranking_list"] = format_ranking(ranking_str)
    
    db_annotation = Annotation(
        annotation_type=annotation.annotation_type,
        label=annotation.label,
        data=annotation.data,
        notes=annotation.notes,
        image_id=annotation.image_id,
        annotator_id=current_user.id,
        status=annotation.status if hasattr(annotation, 'status') else AnnotationStatus.SUBMITTED
    )
    
    db.add(db_annotation)
    
    # 更新图像的标注计数
    from app.models.task_assignment import TaskAssignment
    
    # 如果是第一次标注，增加计数
    if existing_count == 0:
        image.annotation_count = (image.annotation_count or 0) + 1
        
        # 更新已完成用户列表
        if not image.completed_by_users:
            image.completed_by_users = []
        if current_user.id not in image.completed_by_users:
            image.completed_by_users.append(current_user.id)
        
        # 更新标注状态文本
        if image.annotation_count == 0:
            image.annotation_status = "未标注"
        else:
            image.annotation_status = "标注中"
        
        # 检查是否达到要求的标注数量
        required_count = image.required_annotation_count or 1
        if image.annotation_count >= required_count:
            image.is_annotated = True
            image.annotation_status = "待审核"
        
        # 更新任务统计
        if image.task:
            from app.models.task import TaskStatus
            
            # 先 flush 确保当前修改被写入数据库
            db.flush()
            
            # 更新任务的已标注图像数
            annotated_count = db.query(Image).filter(
                Image.task_id == image.task_id,
                Image.is_annotated == True
            ).count()
            image.task.annotated_images = annotated_count
            
            # 检查是否所有图像都已标注完成，自动更新任务状态
            total_images = db.query(Image).filter(Image.task_id == image.task_id).count()
            print(f"[任务状态更新] 任务ID: {image.task_id}, 总图像: {total_images}, 已标注: {annotated_count}, 当前状态: {image.task.status}")
            
            if total_images > 0 and annotated_count >= total_images:
                # 所有图像都已标注完成
                if image.task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                    print(f"[任务状态更新] 所有图像已标注完成，更新任务状态: {image.task.status} -> COMPLETED")
                    image.task.status = TaskStatus.COMPLETED
            elif annotated_count > 0:
                # 有部分图像已标注，更新为进行中
                if image.task.status == TaskStatus.ASSIGNED:
                    print(f"[任务状态更新] 部分图像已标注，更新任务状态: ASSIGNED -> IN_PROGRESS")
                    image.task.status = TaskStatus.IN_PROGRESS
            
            # 更新用户的完成计数
            assignment = db.query(TaskAssignment).filter(
                TaskAssignment.task_id == image.task_id,
                TaskAssignment.user_id == current_user.id
            ).first()
            
            if assignment:
                user_completed = db.query(Image).filter(
                    Image.task_id == image.task_id,
                    Image.completed_by_users.contains([current_user.id])
                ).count()
                assignment.completed_images_count = user_completed
    
    db.commit()
    db.refresh(db_annotation)
    
    return db_annotation

@router.get("", response_model=List[AnnotationResponse])
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

@router.get("/image/{image_id}")
async def get_image_annotations(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取图像的所有标注详情（每个标注员的最终标注）"""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )
    
    # 获取所有标注
    all_annotations = db.query(Annotation).filter(Annotation.image_id == image_id).all()
    
    # 按标注员分组，只保留每个标注员的最新标注
    annotator_latest = {}
    for ann in all_annotations:
        annotator_id = ann.annotator_id
        if annotator_id not in annotator_latest:
            annotator_latest[annotator_id] = ann
        else:
            # 比较创建时间，保留最新的
            if ann.created_at > annotator_latest[annotator_id].created_at:
                annotator_latest[annotator_id] = ann
    
    # 转换为列表，并包含标注员信息
    final_annotations = []
    for ann in annotator_latest.values():
        # 获取标注员信息
        annotator = db.query(User).filter(User.id == ann.annotator_id).first()
        
        ann_dict = {
            "id": ann.id,
            "annotation_type": ann.annotation_type,
            "label": ann.label,
            "data": ann.data,
            "notes": ann.notes,
            "image_id": ann.image_id,
            "annotator_id": ann.annotator_id,
            "annotator": {
                "id": annotator.id,
                "full_name": annotator.full_name,
                "username": annotator.username
            } if annotator else None,
            "reviewer_id": ann.reviewer_id,
            "status": ann.status,
            "review_notes": ann.review_notes,
            "created_at": ann.created_at,
            "updated_at": ann.updated_at,
            "reviewed_at": ann.reviewed_at
        }
        final_annotations.append(ann_dict)
    
    return {
        "image_id": image.id,
        "filename": image.original_filename,
        "is_annotated": image.is_annotated,
        "is_reviewed": image.is_reviewed,
        "annotation_count": image.annotation_count or 0,
        "required_annotation_count": image.required_annotation_count or 1,
        "annotations": final_annotations
    }

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
    """审核单个标注"""
    # 只有管理员可以审核
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以审核标注"
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
    
    # 更新图像的审核状态
    image = db.query(Image).filter(Image.id == annotation.image_id).first()
    if image:
        # 检查该图像的所有标注是否都已审核
        total_annotations = db.query(Annotation).filter(
            Annotation.image_id == image.id
        ).count()
        
        approved_annotations = db.query(Annotation).filter(
            Annotation.image_id == image.id,
            Annotation.status == AnnotationStatus.APPROVED
        ).count()
        
        # 如果所有标注都已通过审核，标记图像为已审核
        if total_annotations > 0 and approved_annotations >= total_annotations:
            image.is_reviewed = True
            image.annotation_status = "已通过"
            
            # 更新任务统计
            if image.task:
                from app.models.task import TaskStatus
                
                # 先 flush 确保当前修改被写入数据库
                db.flush()
                
                reviewed_count = db.query(Image).filter(
                    Image.task_id == image.task_id,
                    Image.is_reviewed == True
                ).count()
                image.task.reviewed_images = reviewed_count
                
                # 检查是否所有图像都已审核完成，自动更新任务状态
                total_images = db.query(Image).filter(Image.task_id == image.task_id).count()
                if total_images > 0 and reviewed_count >= total_images:
                    # 所有图像都已审核完成
                    if image.task.status == TaskStatus.COMPLETED:
                        image.task.status = TaskStatus.REVIEWED
        elif status == AnnotationStatus.REJECTED:
            image.annotation_status = "未通过"
    
    db.commit()
    
    return {"message": "标注审核完成"}

@router.post("/image/{image_id}/review")
async def review_image_annotations(
    image_id: int,
    status: AnnotationStatus,
    review_notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量审核图像的所有标注"""
    # 只有管理员可以审核
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以审核标注"
        )
    
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图像不存在"
        )
    
    # 更新该图像的所有标注
    annotations = db.query(Annotation).filter(Annotation.image_id == image_id).all()
    
    if not annotations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该图像没有标注"
        )
    
    for annotation in annotations:
        annotation.status = status
        annotation.reviewer_id = current_user.id
        if review_notes:
            annotation.review_notes = review_notes
    
    # 更新图像的审核状态
    if status == AnnotationStatus.APPROVED:
        image.is_reviewed = True
        image.annotation_status = "已通过"
    elif status == AnnotationStatus.REJECTED:
        image.is_reviewed = False
        image.annotation_status = "未通过"
    
    # 更新任务统计
    if image.task:
        from app.models.task import TaskStatus
        
        # 先 flush 确保当前修改被写入数据库
        db.flush()
        
        reviewed_count = db.query(Image).filter(
            Image.task_id == image.task_id,
            Image.is_reviewed == True
        ).count()
        image.task.reviewed_images = reviewed_count
        
        # 检查是否所有图像都已审核完成，自动更新任务状态
        total_images = db.query(Image).filter(Image.task_id == image.task_id).count()
        if total_images > 0 and reviewed_count >= total_images:
            # 所有图像都已审核完成
            if image.task.status == TaskStatus.COMPLETED:
                image.task.status = TaskStatus.REVIEWED
    
    db.commit()
    
    return {
        "message": f"已审核 {len(annotations)} 个标注",
        "count": len(annotations),
        "status": status
    }

@router.delete("/image/{image_id}/rejected")
async def delete_rejected_annotations(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除图像的所有被拒绝的标注"""
    # 权限检查：只有标注员可以删除自己的被拒绝标注
    if current_user.role != UserRole.ANNOTATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有标注员可以删除被拒绝的标注"
        )
    
    # 查找该图像的所有被拒绝的标注
    rejected_annotations = db.query(Annotation).filter(
        Annotation.image_id == image_id,
        Annotation.annotator_id == current_user.id,
        Annotation.status == AnnotationStatus.REJECTED
    ).all()
    
    # 如果没有被拒绝的标注，直接返回成功（而不是抛出错误）
    if not rejected_annotations:
        return {"message": "没有需要删除的被拒绝标注", "deleted_count": 0}
    
    # 删除所有被拒绝的标注
    for annotation in rejected_annotations:
        db.delete(annotation)
    
    db.commit()
    
    return {
        "message": f"已删除 {len(rejected_annotations)} 个被拒绝的标注",
        "deleted_count": len(rejected_annotations)
    }

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
