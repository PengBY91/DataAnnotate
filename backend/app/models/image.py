"""
图像模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Image(Base):
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    
    # 关联任务
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    
    # 标注状态
    is_annotated = Column(Boolean, default=False)
    is_reviewed = Column(Boolean, default=False)
    annotation_status = Column(String(50), default="未标注")  # 标注状态文本: 未标注、标注中、待审核、已通过、未通过
    annotation_data = Column(JSON)  # 标注数据（遗留字段，可能废弃）
    review_notes = Column(Text)     # 审核备注
    
    # 多人标注支持
    annotation_count = Column(Integer, default=0)  # 当前标注数量
    required_annotation_count = Column(Integer, default=1)  # 需要的标注数量
    completed_by_users = Column(JSON, default=list)  # 已完成标注的用户ID列表
    
    # 文件夹上传支持
    folder_relative_path = Column(String(500))  # 文件夹内的相对路径
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    annotated_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    
    # 关联关系
    task = relationship("Task", back_populates="images")
    annotations = relationship("Annotation", back_populates="image")
    
    def __repr__(self):
        return f"<Image(id={self.id}, filename='{self.filename}')>"
