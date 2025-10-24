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
    annotation_type: str  # 保留用于兼容
    annotation_types: Optional[List[str]] = None  # 支持多种标注类型 ['classification', 'regression', 'bbox', 'ranking']
    labels: Optional[List[str]] = None
    instructions: Optional[str] = None
    deadline: Optional[datetime] = None
    required_annotations_per_image: int = 1  # 每张图片需要的标注人数
    auto_assign_images: bool = True  # 是否自动分配图像
    ranking_max: Optional[int] = 3  # 排序类型的最大范围

class TaskCreate(TaskBase):
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    assignee_ids: Optional[List[int]] = None  # 多人分配
    reviewer_ids: Optional[List[int]] = None  # 多个审核人

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    reviewer_id: Optional[int] = None
    annotation_type: Optional[str] = None
    annotation_types: Optional[List[str]] = None
    labels: Optional[List[str]] = None
    instructions: Optional[str] = None
    deadline: Optional[datetime] = None
    required_annotations_per_image: Optional[int] = None
    auto_assign_images: Optional[bool] = None
    ranking_max: Optional[int] = None  # 排序类型的最大范围

class AssigneeInfo(BaseModel):
    """分配用户信息"""
    user_id: int
    username: str
    full_name: str
    role: str
    completed_images: int = 0
    
    class Config:
        from_attributes = True

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
    assignees: Optional[List[AssigneeInfo]] = None  # 分配的用户列表
    ranking_config: Optional[Dict[str, Any]] = None  # 排序配置 {'max': 3}
    
    class Config:
        from_attributes = True

class TaskStats(BaseModel):
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    my_tasks: int
    my_completed_tasks: int
