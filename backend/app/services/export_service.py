"""
标注结果导出服务
"""
import os
import json
import zipfile
import uuid
import asyncio
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.annotation import Annotation, AnnotationStatus
from app.models.image import Image
from app.models.task import Task
from app.models.user import User
from app.models.export import ExportRecord
from app.schemas.export import ExportProgress, ExportHistoryItem

class ExportService:
    def __init__(self):
        self.export_dir = "static/exports"
        self.ensure_export_dir()
    
    def ensure_export_dir(self):
        """确保导出目录存在"""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir, exist_ok=True)
    
    async def start_export(
        self,
        task_id: int,
        format: str,
        include_images: bool = False,
        status_filter: Optional[List[AnnotationStatus]] = None,
        user_id: int = None
    ) -> str:
        """开始导出任务"""
        export_id = str(uuid.uuid4())
        
        # 保存导出记录到数据库
        db = SessionLocal()
        try:
            # 将状态过滤器转换为JSON字符串
            status_filter_str = None
            if status_filter:
                status_filter_str = json.dumps([s.value if hasattr(s, 'value') else s for s in status_filter])
            
            export_record = ExportRecord(
                export_id=export_id,
                task_id=task_id,
                user_id=user_id,
                format=format,
                include_images=include_images,
                status_filter=status_filter_str,
                status="processing",
                progress=0,
                message="等待处理..."
            )
            db.add(export_record)
            db.commit()
        finally:
            db.close()
        
        # 在后台任务中执行导出
        asyncio.create_task(self._process_export(
            export_id, task_id, format, include_images, status_filter, user_id
        ))
        
        return export_id
    
    async def _process_export(
        self,
        export_id: str,
        task_id: int,
        format: str,
        include_images: bool,
        status_filter: Optional[List[AnnotationStatus]],
        user_id: int
    ):
        """处理导出任务"""
        try:
            # 更新进度
            await self._update_progress(export_id, "processing", 10, "开始导出...")
            
            # 获取任务和标注数据
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    raise Exception("任务不存在")
                
                # 获取图像列表
                images_query = db.query(Image).filter(Image.task_id == task_id)
                images = images_query.all()
                
                await self._update_progress(export_id, "processing", 30, f"找到 {len(images)} 张图像")
                
                # 获取标注数据
                annotations_query = db.query(Annotation).join(Image).filter(
                    Image.task_id == task_id
                )
                
                if status_filter:
                    annotations_query = annotations_query.filter(
                        Annotation.status.in_(status_filter)
                    )
                
                annotations = annotations_query.all()
                
                await self._update_progress(export_id, "processing", 50, f"找到 {len(annotations)} 个标注")
                
                # 根据格式导出
                if format == "pascal_voc":
                    file_path = await self._export_pascal_voc(
                        export_id, task, images, annotations, include_images
                    )
                elif format == "coco":
                    file_path = await self._export_coco(
                        export_id, task, images, annotations, include_images
                    )
                elif format == "yolo":
                    file_path = await self._export_yolo(
                        export_id, task, images, annotations, include_images
                    )
                elif format == "json":
                    file_path = await self._export_json(
                        export_id, task, images, annotations, include_images
                    )
                elif format == "csv":
                    file_path = await self._export_csv(
                        export_id, task, images, annotations, include_images, db
                    )
                else:
                    raise Exception(f"不支持的导出格式: {format}")
                
                await self._update_progress(export_id, "completed", 100, "导出完成", file_path)
                
            finally:
                db.close()
                
        except Exception as e:
            await self._update_progress(export_id, "failed", 0, f"导出失败: {str(e)}")
    
    async def _export_pascal_voc(
        self,
        export_id: str,
        task: Task,
        images: List[Image],
        annotations: List[Annotation],
        include_images: bool
    ) -> str:
        """导出为Pascal VOC格式"""
        export_path = os.path.join(self.export_dir, f"{export_id}.zip")
        
        with zipfile.ZipFile(export_path, 'w') as zip_file:
            # 创建标注文件
            for image in images:
                image_annotations = [a for a in annotations if a.image_id == image.id]
                
                if not image_annotations:
                    continue
                
                # 创建XML文件
                xml_content = self._create_pascal_voc_xml(image, image_annotations)
                zip_file.writestr(f"annotations/{image.filename}.xml", xml_content)
                
                # 如果需要包含图像
                if include_images and os.path.exists(image.file_path):
                    zip_file.write(image.file_path, f"images/{image.filename}")
        
        return export_path
    
    async def _export_coco(
        self,
        export_id: str,
        task: Task,
        images: List[Image],
        annotations: List[Annotation],
        include_images: bool
    ) -> str:
        """导出为COCO格式"""
        export_path = os.path.join(self.export_dir, f"{export_id}.zip")
        
        # 创建COCO格式数据
        coco_data = {
            "info": {
                "description": task.title,
                "version": "1.0",
                "year": datetime.now().year,
                "contributor": "DataAnnotate System",
                "date_created": datetime.now().isoformat()
            },
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": []
        }
        
        # 处理图像
        image_id_map = {}
        for idx, image in enumerate(images):
            image_id = idx + 1
            image_id_map[image.id] = image_id
            
            coco_data["images"].append({
                "id": image_id,
                "file_name": image.filename,
                "width": image.width,
                "height": image.height,
                "date_captured": image.created_at.isoformat() if image.created_at else None
            })
        
        # 处理标注
        category_id_map = {}
        category_id = 1
        
        for annotation in annotations:
            if annotation.image_id not in image_id_map:
                continue
            
            # 处理类别
            if annotation.label not in category_id_map:
                category_id_map[annotation.label] = category_id
                coco_data["categories"].append({
                    "id": category_id,
                    "name": annotation.label,
                    "supercategory": "object"
                })
                category_id += 1
            
            # 处理标注数据
            if annotation.annotation_type.value == "bbox":
                bbox_data = annotation.data
                coco_data["annotations"].append({
                    "id": annotation.id,
                    "image_id": image_id_map[annotation.image_id],
                    "category_id": category_id_map[annotation.label],
                    "bbox": [bbox_data["x"], bbox_data["y"], bbox_data["width"], bbox_data["height"]],
                    "area": bbox_data["width"] * bbox_data["height"],
                    "iscrowd": 0
                })
        
        # 创建ZIP文件
        with zipfile.ZipFile(export_path, 'w') as zip_file:
            # 添加COCO JSON文件
            zip_file.writestr("annotations.json", json.dumps(coco_data, indent=2, ensure_ascii=False))
            
            # 如果需要包含图像
            if include_images:
                for image in images:
                    if os.path.exists(image.file_path):
                        zip_file.write(image.file_path, f"images/{image.filename}")
        
        return export_path
    
    async def _export_yolo(
        self,
        export_id: str,
        task: Task,
        images: List[Image],
        annotations: List[Annotation],
        include_images: bool
    ) -> str:
        """导出为YOLO格式"""
        export_path = os.path.join(self.export_dir, f"{export_id}.zip")
        
        # 获取所有标签
        labels = set()
        for annotation in annotations:
            labels.add(annotation.label)
        
        labels = sorted(list(labels))
        label_map = {label: idx for idx, label in enumerate(labels)}
        
        with zipfile.ZipFile(export_path, 'w') as zip_file:
            # 创建标签文件
            zip_file.writestr("classes.txt", "\n".join(labels))
            
            # 为每个图像创建标注文件
            for image in images:
                image_annotations = [a for a in annotations if a.image_id == image.id]
                
                if not image_annotations:
                    continue
                
                # 创建YOLO格式标注
                yolo_lines = []
                for annotation in image_annotations:
                    if annotation.annotation_type.value == "bbox":
                        bbox_data = annotation.data
                        # 转换为YOLO格式（归一化坐标）
                        x_center = (bbox_data["x"] + bbox_data["width"] / 2) / image.width
                        y_center = (bbox_data["y"] + bbox_data["height"] / 2) / image.height
                        width = bbox_data["width"] / image.width
                        height = bbox_data["height"] / image.height
                        
                        class_id = label_map[annotation.label]
                        yolo_lines.append(f"{class_id} {x_center} {y_center} {width} {height}")
                
                if yolo_lines:
                    zip_file.writestr(f"labels/{image.filename}.txt", "\n".join(yolo_lines))
            
            # 如果需要包含图像
            if include_images:
                for image in images:
                    if os.path.exists(image.file_path):
                        zip_file.write(image.file_path, f"images/{image.filename}")
        
        return export_path
    
    async def _export_json(
        self,
        export_id: str,
        task: Task,
        images: List[Image],
        annotations: List[Annotation],
        include_images: bool
    ) -> str:
        """导出为JSON格式"""
        export_path = os.path.join(self.export_dir, f"{export_id}.zip")
        
        # 创建JSON数据
        export_data = {
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "annotation_type": task.annotation_type,
                "labels": task.labels,
                "instructions": task.instructions,
                "created_at": task.created_at.isoformat() if task.created_at else None
            },
            "images": [],
            "annotations": []
        }
        
        # 处理图像
        for image in images:
            export_data["images"].append({
                "id": image.id,
                "filename": image.filename,
                "original_filename": image.original_filename,
                "width": image.width,
                "height": image.height,
                "is_annotated": image.is_annotated,
                "is_reviewed": image.is_reviewed,
                "created_at": image.created_at.isoformat() if image.created_at else None
            })
        
        # 处理标注
        for annotation in annotations:
            export_data["annotations"].append({
                "id": annotation.id,
                "image_id": annotation.image_id,
                "annotation_type": annotation.annotation_type.value,
                "label": annotation.label,
                "data": annotation.data,
                "status": annotation.status.value,
                "notes": annotation.notes,
                "review_notes": annotation.review_notes,
                "annotator_id": annotation.annotator_id,
                "reviewer_id": annotation.reviewer_id,
                "created_at": annotation.created_at.isoformat() if annotation.created_at else None,
                "reviewed_at": annotation.reviewed_at.isoformat() if annotation.reviewed_at else None
            })
        
        # 创建ZIP文件
        with zipfile.ZipFile(export_path, 'w') as zip_file:
            # 添加JSON文件
            zip_file.writestr("annotations.json", json.dumps(export_data, indent=2, ensure_ascii=False))
            
            # 如果需要包含图像
            if include_images:
                for image in images:
                    if os.path.exists(image.file_path):
                        zip_file.write(image.file_path, f"images/{image.filename}")
        
        return export_path
    
    async def _export_csv(
        self,
        export_id: str,
        task: Task,
        images: List[Image],
        annotations: List[Annotation],
        include_images: bool,
        db: Session
    ) -> str:
        """导出为CSV格式"""
        export_path = os.path.join(self.export_dir, f"{export_id}.zip")
        
        # 准备CSV数据
        csv_data = []
        
        # 对于每个图像的每个标注员的最终标注
        for image in images:
            # 获取该图像的所有标注，按标注员分组
            image_annotations = [a for a in annotations if a.image_id == image.id]
            
            # 按标注员分组
            annotator_annotations = {}
            for ann in image_annotations:
                annotator_id = ann.annotator_id
                if annotator_id not in annotator_annotations:
                    annotator_annotations[annotator_id] = []
                annotator_annotations[annotator_id].append(ann)
            
            # 每个标注员的最新标注
            for annotator_id, anns in annotator_annotations.items():
                # 获取最新的标注
                latest_ann = max(anns, key=lambda a: a.created_at)
                
                # 获取标注员和审核员信息
                annotator = db.query(User).filter(User.id == latest_ann.annotator_id).first()
                reviewer = db.query(User).filter(User.id == latest_ann.reviewer_id).first() if latest_ann.reviewer_id else None
                
                # 处理标注数据
                data_str = json.dumps(latest_ann.data, ensure_ascii=False) if latest_ann.data else ""
                
                # 对于边界框，提取具体坐标
                bbox_x, bbox_y, bbox_width, bbox_height = "", "", "", ""
                if latest_ann.annotation_type.value == "bbox" and latest_ann.data:
                    bbox_x = latest_ann.data.get("x", "")
                    bbox_y = latest_ann.data.get("y", "")
                    bbox_width = latest_ann.data.get("width", "")
                    bbox_height = latest_ann.data.get("height", "")
                
                # 对于分类，提取分类值
                classification_value = ""
                if latest_ann.annotation_type.value == "classification" and latest_ann.data:
                    classification_value = latest_ann.data.get("value", "")
                
                # 对于回归，提取数值
                regression_value = ""
                if latest_ann.annotation_type.value == "regression" and latest_ann.data:
                    regression_value = latest_ann.data.get("value", "")
                
                # 对于排序，提取排序值
                ranking_value = ""
                if latest_ann.annotation_type.value == "ranking" and latest_ann.data:
                    ranking_value = latest_ann.data.get("ranking", "")
                    ranking_count = latest_ann.data.get("expected_count", "")
                
                csv_data.append({
                    "任务ID": task.id,
                    "任务名称": task.title,
                    "图像ID": image.id,
                    "图像文件名": image.original_filename,
                    "图像宽度": image.width,
                    "图像高度": image.height,
                    "图像文件夹路径": image.folder_relative_path or "",
                    "标注ID": latest_ann.id,
                    "标注类型": latest_ann.annotation_type.value,
                    "标签": latest_ann.label or "",
                    "边界框X": bbox_x,
                    "边界框Y": bbox_y,
                    "边界框宽度": bbox_width,
                    "边界框高度": bbox_height,
                    "分类值": classification_value,
                    "回归值": regression_value,
                    "排序值": ranking_value if latest_ann.annotation_type.value == "ranking" else "",
                    "排序元素数量": ranking_count if latest_ann.annotation_type.value == "ranking" and 'ranking_count' in locals() else "",
                    "原始数据JSON": data_str,
                    "标注备注": latest_ann.notes or "",
                    "标注状态": latest_ann.status.value,
                    "标注员ID": latest_ann.annotator_id,
                    "标注员姓名": annotator.full_name if annotator else "",
                    "标注员用户名": annotator.username if annotator else "",
                    "审核员ID": latest_ann.reviewer_id or "",
                    "审核员姓名": reviewer.full_name if reviewer else "",
                    "审核员用户名": reviewer.username if reviewer else "",
                    "审核备注": latest_ann.review_notes or "",
                    "创建时间": latest_ann.created_at.strftime("%Y-%m-%d %H:%M:%S") if latest_ann.created_at else "",
                    "审核时间": latest_ann.reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if latest_ann.reviewed_at else "",
                })
        
        # 创建ZIP文件
        with zipfile.ZipFile(export_path, 'w') as zip_file:
            # 创建CSV文件
            if csv_data:
                csv_buffer = io.StringIO()
                fieldnames = csv_data[0].keys()
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
                
                csv_content = csv_buffer.getvalue()
                zip_file.writestr("annotations.csv", csv_content.encode('utf-8-sig'))  # 使用 utf-8-sig 以支持 Excel
            
            # 如果需要包含图像
            if include_images:
                for image in images:
                    if os.path.exists(image.file_path):
                        zip_file.write(image.file_path, f"images/{image.original_filename}")
        
        return export_path
    
    def _create_pascal_voc_xml(self, image: Image, annotations: List[Annotation]) -> str:
        """创建Pascal VOC XML内容"""
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<annotation>
    <filename>{image.filename}</filename>
    <size>
        <width>{image.width}</width>
        <height>{image.height}</height>
        <depth>3</depth>
    </size>
    <segmented>0</segmented>
"""
        
        for annotation in annotations:
            if annotation.annotation_type.value == "bbox":
                bbox_data = annotation.data
                xml_content += f"""    <object>
        <name>{annotation.label}</name>
        <pose>Unspecified</pose>
        <truncated>0</truncated>
        <difficult>0</difficult>
        <bndbox>
            <xmin>{bbox_data['x']}</xmin>
            <ymin>{bbox_data['y']}</ymin>
            <xmax>{bbox_data['x'] + bbox_data['width']}</xmax>
            <ymax>{bbox_data['y'] + bbox_data['height']}</ymax>
        </bndbox>
    </object>
"""
        
        xml_content += "</annotation>"
        return xml_content
    
    async def _update_progress(
        self,
        export_id: str,
        status: str,
        progress: int,
        message: str,
        file_path: Optional[str] = None
    ):
        """更新导出进度"""
        db = SessionLocal()
        try:
            export_record = db.query(ExportRecord).filter(
                ExportRecord.export_id == export_id
            ).first()
            
            if export_record:
                export_record.status = status
                export_record.progress = progress
                export_record.message = message
                
                if file_path:
                    export_record.file_path = file_path
                    # 获取文件大小
                    if os.path.exists(file_path):
                        export_record.file_size = os.path.getsize(file_path)
                
                if status in ["completed", "failed"]:
                    export_record.completed_at = datetime.now()
                
                db.commit()
                print(f"Export {export_id}: {status} - {progress}% - {message}")
            else:
                print(f"Warning: Export record not found: {export_id}")
        finally:
            db.close()
    
    async def get_export_progress(self, export_id: str) -> ExportProgress:
        """获取导出进度"""
        db = SessionLocal()
        try:
            export_record = db.query(ExportRecord).filter(
                ExportRecord.export_id == export_id
            ).first()
            
            if not export_record:
                return ExportProgress(
                    export_id=export_id,
                    status="not_found",
                    progress=0,
                    message="导出任务不存在",
                    created_at=datetime.now()
                )
            
            return ExportProgress(
                export_id=export_id,
                status=export_record.status,
                progress=export_record.progress,
                message=export_record.message or "",
                file_path=export_record.file_path,
                file_size=export_record.file_size,
                created_at=export_record.created_at,
                completed_at=export_record.completed_at
            )
        finally:
            db.close()
    
    async def get_export_file(self, export_id: str) -> str:
        """获取导出文件路径"""
        file_path = os.path.join(self.export_dir, f"{export_id}.zip")
        if not os.path.exists(file_path):
            raise Exception("导出文件不存在")
        return file_path
    
    async def get_export_history(
        self,
        user_id: int,
        task_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取导出历史"""
        db = SessionLocal()
        try:
            # 构建查询
            query = db.query(ExportRecord).filter(ExportRecord.user_id == user_id)
            
            # 如果指定了任务ID，添加过滤条件
            if task_id:
                query = query.filter(ExportRecord.task_id == task_id)
            
            # 按创建时间倒序排序
            query = query.order_by(ExportRecord.created_at.desc())
            
            # 分页
            export_records = query.offset(skip).limit(limit).all()
            
            # 转换为字典列表
            history_list = []
            for record in export_records:
                # 获取任务标题
                task = db.query(Task).filter(Task.id == record.task_id).first()
                task_title = task.title if task else "未知任务"
                
                history_list.append({
                    "export_id": record.export_id,
                    "task_id": record.task_id,
                    "task_title": task_title,
                    "format": record.format,
                    "status": record.status,
                    "file_path": record.file_path,
                    "file_size": record.file_size,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "completed_at": record.completed_at.isoformat() if record.completed_at else None
                })
            
            return history_list
        finally:
            db.close()
