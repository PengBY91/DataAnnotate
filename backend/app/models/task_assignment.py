"""
任务分配关联模型 - 支持一个任务分配给多个用户
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class TaskAssignment(Base):
    """任务分配表 - 多对多关系"""
    __tablename__ = "task_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 分配角色
    role = Column(String(20), default="annotator")  # annotator, reviewer
    
    # 状态
    is_active = Column(Boolean, default=True)
    
    # 进度跟踪
    assigned_images_count = Column(Integer, default=0)  # 分配的图像数量
    completed_images_count = Column(Integer, default=0)  # 完成的图像数量
    
    # 时间信息
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # 关联关系
    task = relationship("Task", back_populates="assignments")
    user = relationship("User", back_populates="task_assignments")
    
    def __repr__(self):
        return f"<TaskAssignment(task_id={self.task_id}, user_id={self.user_id}, role='{self.role}')>"

