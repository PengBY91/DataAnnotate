"""
图像优化工具
处理图像存储、缩略图生成等
"""
import os
import hashlib
from pathlib import Path
from typing import Tuple, Optional

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app.config import settings


class ImageOptimizer:
    """图像优化工具类"""
    
    @staticmethod
    def get_hash_path(task_id: int, filename: str) -> str:
        """
        生成基于hash的分级目录路径
        使用文件名的hash值前4位作为子目录，避免单目录文件过多
        
        例如: task_123/a/b/filename.jpg
        """
        # 计算文件名的MD5 hash
        file_hash = hashlib.md5(filename.encode()).hexdigest()
        
        # 使用hash的前两个字符作为两级子目录
        level1 = file_hash[0:2]
        level2 = file_hash[2:4]
        
        return os.path.join(str(task_id), level1, level2)
    
    @staticmethod
    def get_storage_path(task_id: int, filename: str, use_hash: bool = True) -> Tuple[str, str]:
        """
        获取文件存储路径
        
        Args:
            task_id: 任务ID
            filename: 文件名
            use_hash: 是否使用hash分散存储
        
        Returns:
            (relative_dir, full_path): 相对目录和完整路径
        """
        if use_hash and settings.USE_HASH_DIRECTORY:
            relative_dir = ImageOptimizer.get_hash_path(task_id, filename)
        else:
            relative_dir = str(task_id)
        
        full_dir = os.path.join(settings.UPLOAD_DIR, relative_dir)
        os.makedirs(full_dir, exist_ok=True)
        
        full_path = os.path.join(full_dir, filename)
        
        return relative_dir, full_path
    
    @staticmethod
    def generate_thumbnail(
        source_path: str,
        thumbnail_path: str,
        size: Tuple[int, int] = None,
        quality: int = None
    ) -> bool:
        """
        生成缩略图
        
        Args:
            source_path: 源图像路径
            thumbnail_path: 缩略图保存路径
            size: 缩略图尺寸，默认使用配置
            quality: 图像质量，默认使用配置
        
        Returns:
            bool: 是否成功生成
        """
        if not PIL_AVAILABLE:
            return False
        
        try:
            size = size or settings.THUMBNAIL_SIZE
            quality = quality or settings.THUMBNAIL_QUALITY
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)
            
            # 打开并处理图像
            with Image.open(source_path) as img:
                # 转换RGBA为RGB
                if img.mode == 'RGBA':
                    # 创建白色背景
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])  # 使用alpha通道作为mask
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 使用高质量的缩略图算法
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 保存缩略图
                img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            
            return True
        except Exception as e:
            print(f"生成缩略图失败: {e}")
            return False
    
    @staticmethod
    def get_thumbnail_path(original_path: str, task_id: int) -> str:
        """
        获取缩略图路径
        
        Args:
            original_path: 原始图像路径
            task_id: 任务ID
        
        Returns:
            str: 缩略图路径
        """
        # 提取文件名（不包含目录）
        filename = os.path.basename(original_path)
        name_without_ext, _ = os.path.splitext(filename)
        
        # 缩略图统一使用.jpg格式
        thumbnail_filename = f"{name_without_ext}_thumb.jpg"
        
        # 使用相同的hash路径结构
        if settings.USE_HASH_DIRECTORY:
            relative_dir = ImageOptimizer.get_hash_path(task_id, filename)
        else:
            relative_dir = str(task_id)
        
        thumbnail_dir = os.path.join(settings.THUMBNAIL_DIR, relative_dir)
        os.makedirs(thumbnail_dir, exist_ok=True)
        
        return os.path.join(thumbnail_dir, thumbnail_filename)
    
    @staticmethod
    def get_image_info(image_path: str) -> Optional[Tuple[int, int, int]]:
        """
        获取图像信息
        
        Args:
            image_path: 图像路径
        
        Returns:
            Optional[Tuple[int, int, int]]: (width, height, file_size) 或 None
        """
        if not PIL_AVAILABLE:
            file_size = os.path.getsize(image_path) if os.path.exists(image_path) else 0
            return (800, 600, file_size)
        
        try:
            with Image.open(image_path) as img:
                width, height = img.size
            
            file_size = os.path.getsize(image_path)
            return (width, height, file_size)
        except Exception as e:
            print(f"读取图像信息失败: {e}")
            return None
    
    @staticmethod
    def cleanup_empty_directories(base_dir: str):
        """
        清理空目录（自底向上）
        
        Args:
            base_dir: 基础目录
        """
        try:
            for root, dirs, files in os.walk(base_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):  # 目录为空
                            os.rmdir(dir_path)
                    except OSError:
                        pass  # 目录不为空或其他错误，忽略
        except Exception as e:
            print(f"清理空目录失败: {e}")

