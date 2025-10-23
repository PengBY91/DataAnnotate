<template>
  <div class="annotate-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-group">
        <el-button
          :type="currentTool === 'select' ? 'primary' : 'default'"
          @click="setTool('select')"
        >
          <el-icon><Pointer /></el-icon>
          选择
        </el-button>
        
        <el-button
          :type="currentTool === 'bbox' ? 'primary' : 'default'"
          @click="setTool('bbox')"
        >
          <el-icon><Crop /></el-icon>
          边界框
        </el-button>
        
        <el-button
          :type="currentTool === 'polygon' ? 'primary' : 'default'"
          @click="setTool('polygon')"
        >
          <el-icon><Edit /></el-icon>
          多边形
        </el-button>
        
        <el-button
          :type="currentTool === 'keypoint' ? 'primary' : 'default'"
          @click="setTool('keypoint')"
        >
          <el-icon><Location /></el-icon>
          关键点
        </el-button>
      </div>
      
      <div class="toolbar-group">
        <el-select v-model="selectedLabel" placeholder="选择标签" style="width: 150px">
          <el-option
            v-for="label in availableLabels"
            :key="label"
            :label="label"
            :value="label"
          />
        </el-select>
      </div>
      
      <div class="toolbar-group">
        <el-button @click="undo">
          <el-icon><RefreshLeft /></el-icon>
          撤销
        </el-button>
        
        <el-button @click="redo">
          <el-icon><RefreshRight /></el-icon>
          重做
        </el-button>
        
        <el-button @click="clearAll">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
      
      <div class="toolbar-group">
        <el-button type="success" @click="saveAnnotations">
          <el-icon><Check /></el-icon>
          保存
        </el-button>
        
        <el-button @click="goBack">
          <el-icon><Back /></el-icon>
          返回
        </el-button>
      </div>
    </div>
    
    <div class="main-content">
      <!-- 图像显示区域 -->
      <div class="image-container">
        <div class="image-wrapper" ref="imageWrapper">
          <canvas
            ref="annotationCanvas"
            class="annotation-canvas"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @wheel="handleWheel"
          />
          <img
            ref="imageElement"
            :src="imageUrl"
            @load="onImageLoad"
            style="display: none"
          />
        </div>
      </div>
      
      <!-- 标注列表 -->
      <div class="annotations-panel">
        <h3>标注列表</h3>
        <div class="annotations-list">
          <div
            v-for="(annotation, index) in annotations"
            :key="index"
            class="annotation-item"
            :class="{ selected: selectedAnnotation === index }"
            @click="selectAnnotation(index)"
          >
            <div class="annotation-info">
              <span class="annotation-label">{{ annotation.label }}</span>
              <span class="annotation-type">{{ getAnnotationTypeText(annotation.type) }}</span>
            </div>
            <div class="annotation-actions">
              <el-button
                type="danger"
                size="small"
                @click.stop="deleteAnnotation(index)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'
import AnnotationCanvas from '@/components/AnnotationCanvas.vue'

const route = useRoute()
const router = useRouter()

const taskId = route.params.taskId
const imageId = route.params.imageId

const imageWrapper = ref()
const annotationCanvas = ref()
const imageElement = ref()

const currentTool = ref('select')
const selectedLabel = ref('')
const availableLabels = ref([])
const annotations = ref([])
const selectedAnnotation = ref(-1)

const imageUrl = ref('')
const imageInfo = ref({ width: 0, height: 0 })

// 画布相关状态
const canvas = ref(null)
const ctx = ref(null)
const isDrawing = ref(false)
const startPoint = ref({ x: 0, y: 0 })
const currentPoint = ref({ x: 0, y: 0 })

const setTool = (tool) => {
  currentTool.value = tool
  if (tool === 'select') {
    annotationCanvas.value.style.cursor = 'move'
  } else {
    annotationCanvas.value.style.cursor = 'crosshair'
  }
}

const getAnnotationTypeText = (type) => {
  const typeMap = {
    bbox: '边界框',
    polygon: '多边形',
    keypoint: '关键点',
    classification: '分类'
  }
  return typeMap[type] || type
}

const onImageLoad = () => {
  const img = imageElement.value
  imageInfo.value = {
    width: img.naturalWidth,
    height: img.naturalHeight
  }
  
  // 设置画布大小
  const canvas = annotationCanvas.value
  canvas.width = img.naturalWidth
  canvas.height = img.naturalHeight
  
  // 绘制图像到画布
  const ctx = canvas.getContext('2d')
  ctx.drawImage(img, 0, 0)
  
  // 绘制现有标注
  drawAnnotations()
}

const handleMouseDown = (event) => {
  if (currentTool.value === 'select') return
  
  const rect = annotationCanvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  startPoint.value = { x, y }
  isDrawing.value = true
  
  if (currentTool.value === 'keypoint') {
    addKeypoint(x, y)
  }
}

const handleMouseMove = (event) => {
  if (!isDrawing.value || currentTool.value === 'keypoint') return
  
  const rect = annotationCanvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  currentPoint.value = { x, y }
  
  // 重绘画布
  redrawCanvas()
  
  // 绘制当前正在绘制的形状
  if (currentTool.value === 'bbox') {
    drawBoundingBox(startPoint.value, currentPoint.value)
  }
}

const handleMouseUp = (event) => {
  if (!isDrawing.value) return
  
  const rect = annotationCanvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  if (currentTool.value === 'bbox') {
    addBoundingBox(startPoint.value, { x, y })
  } else if (currentTool.value === 'polygon') {
    addPolygonPoint({ x, y })
  }
  
  isDrawing.value = false
}

const handleWheel = (event) => {
  event.preventDefault()
  // 实现缩放功能
}

const addBoundingBox = (start, end) => {
  if (!selectedLabel.value) {
    ElMessage.warning('请先选择标签')
    return
  }
  
  const x = Math.min(start.x, end.x)
  const y = Math.min(start.y, end.y)
  const width = Math.abs(end.x - start.x)
  const height = Math.abs(end.y - start.y)
  
  if (width < 5 || height < 5) {
    ElMessage.warning('标注区域太小')
    return
  }
  
  const annotation = {
    type: 'bbox',
    label: selectedLabel.value,
    data: { x, y, width, height },
    id: Date.now()
  }
  
  annotations.value.push(annotation)
  redrawCanvas()
}

const addKeypoint = (x, y) => {
  if (!selectedLabel.value) {
    ElMessage.warning('请先选择标签')
    return
  }
  
  const annotation = {
    type: 'keypoint',
    label: selectedLabel.value,
    data: { x, y },
    id: Date.now()
  }
  
  annotations.value.push(annotation)
  redrawCanvas()
}

const addPolygonPoint = (point) => {
  // 多边形标注逻辑
}

const drawBoundingBox = (start, end) => {
  const ctx = annotationCanvas.value.getContext('2d')
  ctx.strokeStyle = '#ff0000'
  ctx.lineWidth = 2
  ctx.setLineDash([5, 5])
  
  const x = Math.min(start.x, end.x)
  const y = Math.min(start.y, end.y)
  const width = Math.abs(end.x - start.x)
  const height = Math.abs(end.y - start.y)
  
  ctx.strokeRect(x, y, width, height)
  ctx.setLineDash([])
}

const drawAnnotations = () => {
  const ctx = annotationCanvas.value.getContext('2d')
  
  annotations.value.forEach((annotation, index) => {
    ctx.strokeStyle = index === selectedAnnotation.value ? '#ff0000' : '#00ff00'
    ctx.lineWidth = 2
    
    if (annotation.type === 'bbox') {
      const { x, y, width, height } = annotation.data
      ctx.strokeRect(x, y, width, height)
      
      // 绘制标签
      ctx.fillStyle = '#ff0000'
      ctx.font = '12px Arial'
      ctx.fillText(annotation.label, x, y - 5)
    } else if (annotation.type === 'keypoint') {
      const { x, y } = annotation.data
      ctx.beginPath()
      ctx.arc(x, y, 5, 0, 2 * Math.PI)
      ctx.fill()
      
      ctx.fillStyle = '#ff0000'
      ctx.font = '12px Arial'
      ctx.fillText(annotation.label, x + 10, y - 5)
    }
  })
}

const redrawCanvas = () => {
  const canvas = annotationCanvas.value
  const ctx = canvas.getContext('2d')
  
  // 清除画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 重新绘制图像
  const img = imageElement.value
  if (img) {
    ctx.drawImage(img, 0, 0)
  }
  
  // 绘制标注
  drawAnnotations()
}

const selectAnnotation = (index) => {
  selectedAnnotation.value = index
  redrawCanvas()
}

const deleteAnnotation = (index) => {
  annotations.value.splice(index, 1)
  if (selectedAnnotation.value >= index) {
    selectedAnnotation.value--
  }
  redrawCanvas()
}

const undo = () => {
  // 实现撤销功能
}

const redo = () => {
  // 实现重做功能
}

const clearAll = () => {
  annotations.value = []
  selectedAnnotation.value = -1
  redrawCanvas()
}

const saveAnnotations = async () => {
  try {
    // 保存标注数据
    for (const annotation of annotations.value) {
      await api.post('/annotations', {
        image_id: parseInt(imageId),
        annotation_type: annotation.type,
        label: annotation.label,
        data: annotation.data
      })
    }
    
    ElMessage.success('标注保存成功')
  } catch (error) {
    console.error('保存标注失败:', error)
    ElMessage.error('保存标注失败')
  }
}

const goBack = () => {
  router.push(`/tasks/${taskId}`)
}

const fetchImage = async () => {
  try {
    const response = await api.get(`/files/${imageId}`)
    imageUrl.value = response.data.file_path
  } catch (error) {
    console.error('获取图像失败:', error)
    ElMessage.error('获取图像失败')
  }
}

const fetchTaskLabels = async () => {
  try {
    const response = await api.get(`/tasks/${taskId}`)
    availableLabels.value = response.data.labels || []
  } catch (error) {
    console.error('获取任务标签失败:', error)
  }
}

onMounted(() => {
  fetchImage()
  fetchTaskLabels()
})
</script>

<style scoped>
.annotate-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0 10px;
  border-right: 1px solid #ddd;
}

.toolbar-group:last-child {
  border-right: none;
}

.main-content {
  flex: 1;
  display: flex;
}

.image-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f0f0f0;
  overflow: auto;
}

.image-wrapper {
  position: relative;
  display: inline-block;
}

.annotation-canvas {
  border: 1px solid #ddd;
  cursor: crosshair;
}

.annotations-panel {
  width: 300px;
  background: white;
  border-left: 1px solid #ddd;
  padding: 20px;
  overflow-y: auto;
}

.annotations-list {
  max-height: 400px;
  overflow-y: auto;
}

.annotation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
}

.annotation-item:hover {
  background: #f5f5f5;
}

.annotation-item.selected {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.annotation-info {
  flex: 1;
}

.annotation-label {
  font-weight: bold;
  display: block;
}

.annotation-type {
  font-size: 12px;
  color: #666;
}
</style>
