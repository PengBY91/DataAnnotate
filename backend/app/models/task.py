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
    annotation_type = Column(String(50), nullable=False)  # bbox, polygon, keypoint, classification（兼容旧数据）
    annotation_types = Column(JSON)  # 支持多种标注类型 ['classification', 'regression', 'bbox']
    labels = Column(JSON)  # 预设标签列表
    instructions = Column(Text)  # 标注说明
    
    # 多人标注配置
    required_annotations_per_image = Column(Integer, default=1)  # 每张图片需要的标注人数
    auto_assign_images = Column(Boolean, default=True)  # 是否自动分配图像给标注员
    
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
    
    # 新增：多对多关系 - 任务分配
    assignments = relationship("TaskAssignment", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}')>"
