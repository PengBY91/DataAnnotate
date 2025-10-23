"""
标注相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.annotation import AnnotationType, AnnotationStatus

class AnnotationBase(BaseModel):
    annotation_type: AnnotationType
    label: str
    data: Dict[str, Any]
    notes: Optional[str] = None

class AnnotationCreate(AnnotationBase):
    image_id: int

class AnnotationUpdate(BaseModel):
    label: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    status: Optional[AnnotationStatus] = None

class AnnotationResponse(AnnotationBase):
    id: int
    image_id: int
    annotator_id: int
    reviewer_id: Optional[int] = None
    status: AnnotationStatus
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ImageAnnotation(BaseModel):
    image_id: int
    filename: str
    width: int
    height: int
    annotations: List[AnnotationResponse]
    is_annotated: bool
    is_reviewed: bool
