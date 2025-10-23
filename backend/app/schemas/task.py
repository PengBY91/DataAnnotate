"""
任务相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    annotation_type: str
    labels: Optional[List[str]] = None
    instructions: Optional[str] = None
    deadline: Optional[datetime] = None

class TaskCreate(TaskBase):
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    labels: Optional[List[str]] = None
    instructions: Optional[str] = None
    deadline: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    creator_id: int
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    total_images: int
    annotated_images: int
    reviewed_images: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskStats(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    my_tasks: int
    my_completed_tasks: int
