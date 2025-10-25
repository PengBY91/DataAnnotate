# 文件名优化说明

## 改进目标

让上传后的图像文件名包含原始文件夹路径和文件名信息，便于追踪和识别图像来源。

## 实现方式

### 1. 新增文件名生成函数

在 `backend/app/routes/files.py` 中添加了 `generate_unique_filename()` 函数：

```python
def generate_unique_filename(original_filename: str, upload_dir: str, folder_path: str = None) -> tuple:
    """
    生成唯一且可读的文件名
    
    Args:
        original_filename: 原始文件名
        upload_dir: 上传目录
        folder_path: 文件夹相对路径（可选）
    
    Returns:
        (unique_filename, display_name): 唯一文件名和显示名称
    """
```

### 2. 文件名生成规则

#### 单文件上传
- 格式：`{原始文件名}_{时间戳}.{扩展名}`
- 示例：`cat_20241225_143022_123456.jpg`

#### 文件夹上传
- 格式：`{文件夹路径}_{原始文件名}_{时间戳}.{扩展名}`
- 示例：`subfolder_dog_20241225_143022_123456.jpg`

### 3. 特性

1. **可读性**：文件名包含原始名称信息，易于识别
2. **唯一性**：添加精确到毫秒的时间戳确保唯一性
3. **安全性**：清理非法字符，防止文件系统错误
4. **路径信息**：文件夹上传时保留相对路径信息

### 4. 示例

#### 上传前文件结构
```
images/
├── animals/
│   ├── cat.jpg
│   └── dog.jpg
└── plants/
    └── flower.jpg
```

#### 上传后系统文件名
```
animals_cat_20241225_143022_123456.jpg
animals_dog_20241225_143022_234567.jpg
plants_flower_20241225_143022_345678.jpg
```

#### 数据库存储
- `filename`: `animals_cat_20241225_143022_123456.jpg` (系统文件名)
- `original_filename`: `cat.jpg` (原始文件名)
- `folder_relative_path`: `animals/cat.jpg` (完整相对路径)

## 优势

1. **易于追踪**：通过文件名可以快速了解图像来源
2. **便于调试**：出问题时能快速定位原始文件
3. **保持兼容**：仍保存 `original_filename` 和 `folder_relative_path` 字段
4. **防止冲突**：时间戳和计数器确保文件名不会重复

## 向后兼容

- 保留了 `original_filename` 字段存储原始文件名
- 保留了 `folder_relative_path` 字段存储完整相对路径
- 旧数据不受影响，新上传的文件使用新命名规则

## 测试建议

### 单文件上传测试
1. 上传单个图像文件
2. 检查系统文件名是否包含原始文件名
3. 验证文件能正常显示和下载

### 文件夹上传测试
1. 上传包含子文件夹的图像文件夹
2. 检查系统文件名是否包含文件夹路径信息
3. 验证不同子文件夹的同名文件不会冲突

### 特殊字符测试
1. 上传包含中文、空格、特殊字符的文件名
2. 验证文件名被正确清理并保存
3. 确认文件仍能正常访问

## 相关文件

- `backend/app/routes/files.py` - 文件上传逻辑
- `backend/app/models/image.py` - 图像模型定义

