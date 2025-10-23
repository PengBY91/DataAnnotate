"""
标注模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class AnnotationType(enum.Enum):
    BBOX = "bbox"           # 边界框
    POLYGON = "polygon"     # 多边形
    KEYPOINT = "keypoint"   # 关键点
    CLASSIFICATION = "classification"  # 分类

class AnnotationStatus(enum.Enum):
    DRAFT = "draft"         # 草稿
    SUBMITTED = "submitted" # 已提交
    APPROVED = "approved"   # 已通过
    REJECTED = "rejected"   # 已拒绝

class Annotation(Base):
    __tablename__ = "annotations"
    
    id = Column(Integer, primary_key=True, index=True)
    annotation_type = Column(Enum(AnnotationType), nullable=False)
    label = Column(String(100), nullable=False)
    data = Column(JSON, nullable=False)  # 标注数据（坐标、分类等）
    status = Column(Enum(AnnotationStatus), default=AnnotationStatus.DRAFT)
    
    # 关联关系
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    annotator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    
    # 时间信息
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    reviewed_at = Column(DateTime(timezone=True))
    
    # 备注
    notes = Column(Text)
    review_notes = Column(Text)
    
    # 关联关系
    image = relationship("Image", back_populates="annotations")
    annotator = relationship("User", foreign_keys=[annotator_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    
    def __repr__(self):
        return f"<Annotation(id={self.id}, type='{self.annotation_type.value}', label='{self.label}')>"
