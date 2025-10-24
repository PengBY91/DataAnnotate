"""
任务管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from app.models.task_assignment import TaskAssignment
from app.models.image import Image
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStats, AssigneeInfo
from app.utils.auth import get_current_user

router = APIRouter()

@router.post("", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建任务"""
    # 只有管理员和算法工程师可以创建任务
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 处理排序配置
    ranking_config = None
    if task.annotation_types and 'ranking' in task.annotation_types:
        ranking_config = {'max': task.ranking_max or 3}
    
    db_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        annotation_type=task.annotation_type,
        annotation_types=task.annotation_types,
        labels=task.labels,
        instructions=task.instructions,
        deadline=task.deadline,
        creator_id=current_user.id,
        assignee_id=task.assignee_id,
        reviewer_id=task.reviewer_id,
        required_annotations_per_image=task.required_annotations_per_image,
        auto_assign_images=task.auto_assign_images,
        ranking_config=ranking_config
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task

@router.get("", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    query = db.query(Task)
    
    # 根据用户角色过滤任务
    if current_user.role == UserRole.ANNOTATOR:
        # 标注员可以看到分配给自己的任务（包括新的分配系统）
        query = query.filter(
            (Task.assignee_id == current_user.id) |
            (Task.id.in_(
                db.query(TaskAssignment.task_id).filter(
                    TaskAssignment.user_id == current_user.id,
                    TaskAssignment.role == "annotator"
                )
            ))
        )
    elif current_user.role == UserRole.REVIEWER:
        # 审核员可以看到分配给自己的任务
        query = query.filter(Task.reviewer_id == current_user.id)
    elif current_user.role == UserRole.ENGINEER:
        # 算法工程师可以看到自己创建的任务
        query = query.filter(Task.creator_id == current_user.id)
    # 管理员可以看到所有任务
    
    # 应用过滤条件（忽略空字符串）
    if status and status.strip():
        try:
            status_enum = TaskStatus(status)
            query = query.filter(Task.status == status_enum)
        except ValueError:
            pass  # 忽略无效的状态值
    
    if priority and priority.strip():
        query = query.filter(Task.priority == priority)
    
    if assignee_id:
        query = query.filter(Task.assignee_id == assignee_id)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks

@router.get("/stats", response_model=TaskStats)
async def get_task_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务统计信息"""
    # 根据用户角色计算统计信息
    if current_user.role == UserRole.ANNOTATOR:
        from app.models.task_assignment import TaskAssignment
        
        # 查询该标注员参与的所有任务（包括旧的assignee_id和新的TaskAssignment）
        # 方法1: 通过旧的assignee_id
        old_assigned_task_ids = db.query(Task.id).filter(Task.assignee_id == current_user.id).all()
        old_assigned_task_ids = [t[0] for t in old_assigned_task_ids]
        
        # 方法2: 通过新的TaskAssignment
        new_assigned_task_ids = db.query(TaskAssignment.task_id).filter(
            TaskAssignment.user_id == current_user.id,
            TaskAssignment.role == "annotator"
        ).all()
        new_assigned_task_ids = [t[0] for t in new_assigned_task_ids]
        
        # 合并两种方式的任务ID
        all_task_ids = list(set(old_assigned_task_ids + new_assigned_task_ids))
        
        if all_task_ids:
            total_tasks = db.query(Task).filter(Task.id.in_(all_task_ids)).count()
            pending_tasks = db.query(Task).filter(
                Task.id.in_(all_task_ids),
                Task.status == TaskStatus.PENDING
            ).count()
            in_progress_tasks = db.query(Task).filter(
                Task.id.in_(all_task_ids),
                Task.status == TaskStatus.IN_PROGRESS
            ).count()
            completed_tasks = db.query(Task).filter(
                Task.id.in_(all_task_ids),
                Task.status == TaskStatus.COMPLETED
            ).count()
        else:
            total_tasks = 0
            pending_tasks = 0
            in_progress_tasks = 0
            completed_tasks = 0
    else:
        total_tasks = db.query(Task).count()
        pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).count()
        in_progress_tasks = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
        completed_tasks = db.query(Task).filter(Task.status == TaskStatus.COMPLETED).count()
    
    return TaskStats(
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        completed_tasks=completed_tasks,
        my_tasks=total_tasks,
        my_completed_tasks=completed_tasks
    )

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定任务详情"""
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
    
    if (current_user.role == UserRole.ANNOTATOR and not is_assigned and task.assignee_id != current_user.id) or \
       (current_user.role == UserRole.REVIEWER and task.reviewer_id != current_user.id) or \
       (current_user.role == UserRole.ENGINEER and task.creator_id != current_user.id):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
    
    # 获取分配的用户列表
    assignments = db.query(TaskAssignment).filter(
        TaskAssignment.task_id == task_id
    ).all()
    
    assignees_info = []
    for assignment in assignments:
        user = db.query(User).filter(User.id == assignment.user_id).first()
        if user:
            assignees_info.append(AssigneeInfo(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                role=user.role.value,
                completed_images=assignment.completed_images_count
            ))
    
    # 重新计算统计信息 - 按图像数量计算
    
    total_images = db.query(Image).filter(Image.task_id == task_id).count()
    annotated_images = db.query(Image).filter(
        Image.task_id == task_id,
        Image.is_annotated == True
    ).count()
    reviewed_images = db.query(Image).filter(
        Image.task_id == task_id,
        Image.is_reviewed == True
    ).count()
    
    # 更新任务统计信息
    task.total_images = total_images
    task.annotated_images = annotated_images
    task.reviewed_images = reviewed_images
    db.commit()
    
    # 将 task 转换为字典并添加 assignees
    task_dict = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "annotation_type": task.annotation_type,
        "labels": task.labels,
        "instructions": task.instructions,
        "deadline": task.deadline,
        "required_annotations_per_image": task.required_annotations_per_image,
        "auto_assign_images": task.auto_assign_images,
        "status": task.status,
        "creator_id": task.creator_id,
        "assignee_id": task.assignee_id,
        "reviewer_id": task.reviewer_id,
        "total_images": total_images,
        "annotated_images": annotated_images,
        "reviewed_images": reviewed_images,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "assignees": assignees_info
    }
    
    return task_dict

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    # 更新任务信息
    update_data = task_update.dict(exclude_unset=True)
    
    # 处理排序配置
    if 'ranking_max' in update_data and update_data.get('annotation_types') and 'ranking' in update_data['annotation_types']:
        ranking_config = {'max': update_data['ranking_max']}
        update_data['ranking_config'] = ranking_config
        # ranking_max不需要存储到数据库，只存储ranking_config
        del update_data['ranking_max']
    elif 'ranking_max' in update_data:
        # 如果没有ranking类型但有ranking_max，删除它
        del update_data['ranking_max']
    
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    return task

@router.post("/{task_id}/assign")
async def assign_task(
    task_id: int,
    assignee_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分配任务（单人，兼容旧接口）"""
    print(f"分配任务: task_id={task_id}, assignee_id={assignee_id}, current_user={current_user.username}")
    
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 验证分配用户存在
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分配用户不存在"
        )
    
    # 创建任务分配记录
    existing_assignment = db.query(TaskAssignment).filter(
        TaskAssignment.task_id == task_id,
        TaskAssignment.user_id == assignee_id
    ).first()
    
    if not existing_assignment:
        assignment = TaskAssignment(
            task_id=task_id,
            user_id=assignee_id,
            role="annotator"
        )
        db.add(assignment)
    
    # 更新旧字段以保持兼容性
    task.assignee_id = assignee_id
    task.status = TaskStatus.ASSIGNED
    db.commit()
    
    print(f"任务分配成功: {task.title} -> {assignee.username}")
    
    return {"message": "任务分配成功", "task_id": task_id, "assignee": assignee.username}

@router.post("/{task_id}/assign-multiple")
async def assign_task_to_multiple_users(
    task_id: int,
    assignee_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量分配任务给多个用户"""
    print(f"批量分配任务: task_id={task_id}, assignee_ids={assignee_ids}")
    
    if current_user.role not in [UserRole.ADMIN, UserRole.ENGINEER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 验证所有用户存在
    users = db.query(User).filter(User.id.in_(assignee_ids)).all()
    if len(users) != len(assignee_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部分用户不存在"
        )
    
    assigned_count = 0
    for user_id in assignee_ids:
        # 检查是否已经分配过
        existing = db.query(TaskAssignment).filter(
            TaskAssignment.task_id == task_id,
            TaskAssignment.user_id == user_id
        ).first()
        
        if not existing:
            assignment = TaskAssignment(
                task_id=task_id,
                user_id=user_id,
                role="annotator"
            )
            db.add(assignment)
            assigned_count += 1
    
    # 更新任务状态
    if task.status == TaskStatus.PENDING:
        task.status = TaskStatus.ASSIGNED
    
    # 根据任务配置，为每张图像设置需要的标注数量
    images = db.query(Image).filter(Image.task_id == task_id).all()
    for image in images:
        image.required_annotation_count = task.required_annotations_per_image
    
    db.commit()
    
    print(f"批量分配完成: {assigned_count} 个用户被分配到任务 {task.title}")
    
    return {
        "message": f"成功分配任务给 {assigned_count} 个用户",
        "task_id": task_id,
        "assigned_count": assigned_count
    }

@router.post("/{task_id}/start")
async def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """开始任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 只有被分配的用户可以开始任务
    if task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    task.status = TaskStatus.IN_PROGRESS
    db.commit()
    
    return {"message": "任务已开始"}

@router.post("/{task_id}/complete")
async def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """完成任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 只有被分配的用户可以完成任务
    if task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    
    task.status = TaskStatus.COMPLETED
    db.commit()
    
    return {"message": "任务已完成"}

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除任务（仅管理员）"""
    # 权限检查：只有管理员可以删除任务
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除任务"
        )
    
    # 查找任务
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 获取统计信息用于返回
    from app.models.image import Image
    from app.models.annotation import Annotation
    
    image_count = db.query(Image).filter(Image.task_id == task_id).count()
    annotation_count = db.query(Annotation).join(Image).filter(Image.task_id == task_id).count()
    
    # 删除任务（由于设置了cascade，会自动删除关联的images, annotations, assignments等）
    db.delete(task)
    db.commit()
    
    return {
        "message": "任务删除成功",
        "task_id": task_id,
        "task_title": task.title,
        "deleted_images": image_count,
        "deleted_annotations": annotation_count
    }
