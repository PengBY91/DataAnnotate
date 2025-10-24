"""
导出记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ExportRecord(Base):
    __tablename__ = "export_records"
    
    id = Column(Integer, primary_key=True, index=True)
    export_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID
    
    # 任务和用户信息
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 导出配置
    format = Column(String(50), nullable=False)  # csv, json, coco, yolo, pascal_voc
    include_images = Column(Boolean, default=False)
    status_filter = Column(Text)  # JSON字符串，存储状态过滤条件
    
    # 导出状态
    status = Column(String(20), default="processing")  # processing, completed, failed
    message = Column(Text)  # 状态消息
    progress = Column(Integer, default=0)  # 0-100
    
    # 文件信息
    file_path = Column(String(500))
    file_size = Column(BigInteger)  # 文件大小（字节）
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # 关联关系
    task = relationship("Task", foreign_keys=[task_id])
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self):
        return f"<ExportRecord(export_id='{self.export_id}', task_id={self.task_id}, format='{self.format}', status='{self.status}')>"

