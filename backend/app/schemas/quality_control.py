"""
质量控制相关的数据模式
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.annotation import AnnotationStatus

class QualityReviewBase(BaseModel):
    """质量审核基础模式"""
    review_notes: Optional[str] = None

class QualityReviewCreate(QualityReviewBase):
    """创建质量审核"""
    annotation_id: int
    status: AnnotationStatus

class QualityReviewResponse(QualityReviewBase):
    """质量审核响应"""
    id: int
    image_id: int
    task_id: int
    annotator_id: int
    annotator_name: str
    annotation_type: str
    label: str
    data: Dict[str, Any]
    notes: Optional[str]
    created_at: datetime
    image_filename: str
    
    class Config:
        from_attributes = True

class AnnotatorMetric(BaseModel):
    """标注员指标"""
    annotator_id: int
    annotator_name: str
    total_annotations: int
    approved_count: int
    rejected_count: int
    approval_rate: float

class QualityMetrics(BaseModel):
    """质量指标"""
    task_id: int
    total_annotations: int
    approved_annotations: int
    rejected_annotations: int
    pending_annotations: int
    approval_rate: float
    annotator_metrics: List[AnnotatorMetric]

class ReviewStats(BaseModel):
    """审核统计"""
    reviewer_id: int
    period_days: int
    total_reviews: int
    approved_reviews: int
    rejected_reviews: int
    approval_rate: float

class AnnotationReview(BaseModel):
    """标注审核"""
    annotation_id: int
    status: AnnotationStatus
    review_notes: Optional[str] = None
