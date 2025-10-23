"""
任务模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class TaskStatus(enum.Enum):
    PENDING = "pending"       # 待分配
    ASSIGNED = "assigned"     # 已分配
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"   # 已完成
    REVIEWED = "reviewed"     # 已审核
    REJECTED = "rejected"     # 已拒绝

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # 关联用户
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    
    # 任务配置
    annotation_type = Column(String(50), nullable=False)  # bbox, polygon, keypoint, classification
    labels = Column(JSON)  # 预设标签列表
    instructions = Column(Text)  # 标注说明
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deadline = Column(DateTime(timezone=True))
    
    # 统计信息
    total_images = Column(Integer, default=0)
    annotated_images = Column(Integer, default=0)
    reviewed_images = Column(Integer, default=0)
    
    # 关联关系
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviewed_tasks")
    images = relationship("Image", back_populates="task")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}')>"
