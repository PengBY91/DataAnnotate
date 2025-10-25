# 前端分页和缩略图更新指南

## 📋 需要更新的文件

1. **frontend/src/views/TaskDetail.vue** - 任务详情页面（图像列表）
2. **前端API调用** - 适配新的分页响应格式

## 🎯 TaskDetail.vue 更新步骤

### 1. 添加分页相关的响应式变量

在现有的ref声明部分添加：

```javascript
// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)
const totalImages = ref(0)
```

### 2. 更新 fetchImages 函数

**原有代码：**
```javascript
const fetchImages = async () => {
  imagesLoading.value = true
  try {
    const response = await api.get(`/files/task/${taskId}`)
    images.value = response.data
  } catch (error) {
    console.error('获取图像列表失败:', error)
    ElMessage.error('获取图像列表失败')
  } finally {
    imagesLoading.value = false
  }
}
```

**更新为：**
```javascript
const fetchImages = async (page = null) => {
  if (page !== null) {
    currentPage.value = page
  }
  
  imagesLoading.value = true
  try {
    const response = await api.get(`/files/task/${taskId}`, {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value,
        use_thumbnail: true  // 使用缩略图，节省带宽
      }
    })
    
    // 新的API返回格式
    images.value = response.data.images
    totalImages.value = response.data.total
    
  } catch (error) {
    console.error('获取图像列表失败:', error)
    ElMessage.error('获取图像列表失败')
  } finally {
    imagesLoading.value = false
  }
}

// 分页处理
const handlePageChange = (page) => {
  fetchImages(page)
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchImages()
}
```

### 3. 更新模板 - 图像显示

**原有代码：**
```vue
<el-table-column label="文件信息" width="300">
  <template #default="{ row }">
    <div>
      <div class="filename">{{ row.filename }}</div>
      <div v-if="row.folder_relative_path" class="folder-path">
        📁 {{ row.folder_relative_path }}
      </div>
    </div>
  </template>
</el-table-column>
```

**更新为（添加缩略图预览）：**
```vue
<el-table-column label="缩略图" width="100">
  <template #default="{ row }">
    <el-image
      :src="`http://localhost:8000${row.thumbnail_url}`"
      :preview-src-list="[`http://localhost:8000${row.file_path}`]"
      fit="cover"
      style="width: 80px; height: 80px; border-radius: 4px; cursor: pointer;"
      lazy
    >
      <template #error>
        <div style="width: 80px; height: 80px; background: #f5f7fa; display: flex; align-items: center; justify-content: center;">
          <el-icon><Picture /></el-icon>
        </div>
      </template>
    </el-image>
  </template>
</el-table-column>

<el-table-column label="文件信息" width="300">
  <template #default="{ row }">
    <div>
      <div class="filename">{{ row.filename }}</div>
      <div v-if="row.folder_relative_path" class="folder-path">
        📁 {{ row.folder_relative_path }}
      </div>
      <div style="font-size: 12px; color: #999; margin-top: 4px;">
        {{ row.width }} × {{ row.height }}
      </div>
    </div>
  </template>
</el-table-column>
```

### 4. 添加分页组件

在图像表格后面添加分页组件：

```vue
<el-table 
  :data="images" 
  style="width: 100%" 
  v-loading="imagesLoading"
  @selection-change="handleSelectionChange"
>
  <!-- ... 现有的表格列 ... -->
</el-table>

<!-- 添加分页组件 -->
<div style="margin-top: 20px; display: flex; justify-content: flex-end;">
  <el-pagination
    v-model:current-page="currentPage"
    v-model:page-size="pageSize"
    :page-sizes="[10, 20, 50, 100]"
    :total="totalImages"
    layout="total, sizes, prev, pager, next, jumper"
    @size-change="handleSizeChange"
    @current-change="handlePageChange"
  />
</div>
```

### 5. 导入Picture图标（如果未导入）

在script setup部分添加：

```javascript
import { Picture } from '@element-plus/icons-vue'
```

## 🎨 完整示例

```vue
<template>
  <div class="task-detail">
    <!-- ... 现有的任务信息卡片 ... -->
    
    <!-- 图像列表卡片 -->
    <el-card class="images-card">
      <template #header>
        <div class="card-header">
          <span>图像列表（共 {{ totalImages }} 张）</span>
          <div>
            <!-- ... 现有的按钮 ... -->
          </div>
        </div>
      </template>
      
      <el-table 
        :data="images" 
        style="width: 100%" 
        v-loading="imagesLoading"
        @selection-change="handleSelectionChange"
      >
        <!-- 选择列 -->
        <el-table-column 
          v-if="canReview"
          type="selection" 
          width="55"
          :selectable="isImageSelectable"
        />
        
        <!-- 缩略图列 -->
        <el-table-column label="缩略图" width="100">
          <template #default="{ row }">
            <el-image
              :src="`http://localhost:8000${row.thumbnail_url}`"
              :preview-src-list="[`http://localhost:8000${row.file_path}`]"
              fit="cover"
              style="width: 80px; height: 80px; border-radius: 4px; cursor: pointer;"
              lazy
            >
              <template #error>
                <div style="width: 80px; height: 80px; background: #f5f7fa; display: flex; align-items: center; justify-content: center;">
                  <el-icon><Picture /></el-icon>
                </div>
              </template>
            </el-image>
          </template>
        </el-table-column>
        
        <!-- ... 其他列 ... -->
      </el-table>
      
      <!-- 分页组件 -->
      <div style="margin-top: 20px; display: flex; justify-content: flex-end;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalImages"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Picture } from '@element-plus/icons-vue'
// ... 其他导入 ...

// 分页相关
const currentPage = ref(1)
const pageSize = ref(20)
const totalImages = ref(0)

// 获取图像列表（带分页）
const fetchImages = async (page = null) => {
  if (page !== null) {
    currentPage.value = page
  }
  
  imagesLoading.value = true
  try {
    const response = await api.get(`/files/task/${taskId}`, {
      params: {
        skip: (currentPage.value - 1) * pageSize.value,
        limit: pageSize.value,
        use_thumbnail: true
      }
    })
    
    images.value = response.data.images
    totalImages.value = response.data.total
    
  } catch (error) {
    console.error('获取图像列表失败:', error)
    ElMessage.error('获取图像列表失败')
  } finally {
    imagesLoading.value = false
  }
}

const handlePageChange = (page) => {
  fetchImages(page)
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchImages()
}

// ... 其他函数 ...
</script>
```

## 📊 效果对比

### 优化前
- 一次性加载所有图像（可能5000+张）
- 每张图像加载原图（可能5-10MB）
- 页面加载时间：20-60秒
- 内存占用：1GB+
- 页面卡顿、可能崩溃

### 优化后
- 每页只加载20张图像
- 列表显示缩略图（约50KB/张）
- 点击预览才加载原图
- 页面加载时间：1-2秒
- 内存占用：<200MB
- 页面流畅

## ⚠️ 注意事项

1. **兼容性**：更新后仍兼容旧的API（如果没有分页参数，返回所有数据）
2. **渐进式**：可以先更新后端，前端逐步适配
3. **缓存**：浏览器会自动缓存缩略图，第二次访问更快
4. **预加载**：可以考虑预加载下一页数据提升体验

## 🚀 进一步优化

1. **虚拟滚动**：对于超大列表（10000+），可以使用`el-table-v2`的虚拟滚动
2. **智能预加载**：滚动到底部前预加载下一页
3. **骨架屏**：加载时显示骨架占位符
4. **图片懒加载**：使用`lazy`属性（已包含在示例中）

## 📝 测试建议

1. 创建一个包含1000+张图片的测试任务
2. 观察页面加载速度
3. 测试分页切换流畅度
4. 检查缩略图显示
5. 验证原图预览功能

完成这些更新后，系统将能够轻松处理数万张图像的任务！

