"""
任务管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskStats
from app.utils.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=TaskResponse)
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
    
    db_task = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        annotation_type=task.annotation_type,
        labels=task.labels,
        instructions=task.instructions,
        deadline=task.deadline,
        creator_id=current_user.id,
        assignee_id=task.assignee_id,
        reviewer_id=task.reviewer_id
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TaskStatus] = None,
    assignee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    query = db.query(Task)
    
    # 根据用户角色过滤任务
    if current_user.role == UserRole.ANNOTATOR:
        # 标注员只能看到分配给自己的任务
        query = query.filter(Task.assignee_id == current_user.id)
    elif current_user.role == UserRole.REVIEWER:
        # 审核员可以看到分配给自己的任务
        query = query.filter(Task.reviewer_id == current_user.id)
    elif current_user.role == UserRole.ENGINEER:
        # 算法工程师可以看到自己创建的任务
        query = query.filter(Task.creator_id == current_user.id)
    # 管理员可以看到所有任务
    
    # 应用过滤条件
    if status:
        query = query.filter(Task.status == status)
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
        total_tasks = db.query(Task).filter(Task.assignee_id == current_user.id).count()
        pending_tasks = db.query(Task).filter(
            Task.assignee_id == current_user.id,
            Task.status == TaskStatus.PENDING
        ).count()
        in_progress_tasks = db.query(Task).filter(
            Task.assignee_id == current_user.id,
            Task.status == TaskStatus.IN_PROGRESS
        ).count()
        completed_tasks = db.query(Task).filter(
            Task.assignee_id == current_user.id,
            Task.status == TaskStatus.COMPLETED
        ).count()
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
    
    # 权限检查
    if (current_user.role == UserRole.ANNOTATOR and task.assignee_id != current_user.id) or \
       (current_user.role == UserRole.REVIEWER and task.reviewer_id != current_user.id) or \
       (current_user.role == UserRole.ENGINEER and task.creator_id != current_user.id):
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
    
    return task

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
    for field, value in update_data.items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    return task

@router.post("/{task_id}/assign")
async def assign_task(
    task_id: int,
    assignee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分配任务"""
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
    
    task.assignee_id = assignee_id
    task.status = TaskStatus.ASSIGNED
    db.commit()
    
    return {"message": "任务分配成功"}

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
