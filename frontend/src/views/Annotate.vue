<template>
  <div class="annotate-container">
    <!-- 顶部操作栏 -->
    <div class="top-toolbar">
      <div class="toolbar-left">
        <h3>图像标注</h3>
      </div>
      <div class="toolbar-right">
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
      
        <el-button type="success" @click="saveAnnotations">
          <el-icon><Check /></el-icon>
          保存并继续
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
      
      <!-- 标注工具面板 -->
      <div class="annotations-panel">
        <el-tabs v-model="activeAnnotationType" type="card">
          <!-- 边界框标注 -->
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('bbox')" 
            label="边界框" 
            name="bbox"
          >
            <div class="annotation-tools">
              <div class="tool-section">
                <el-button
                  :type="currentTool === 'bbox' ? 'primary' : 'default'"
                  @click="setTool('bbox')"
                  style="width: 100%; margin-bottom: 10px"
                >
                  <el-icon><Crop /></el-icon>
                  绘制边界框
                </el-button>
                
                <el-select 
                  v-model="selectedLabel" 
                  placeholder="选择标签" 
                  style="width: 100%; margin-bottom: 10px"
                >
                  <el-option
                    v-for="label in availableLabels"
                    :key="label"
                    :label="label"
                    :value="label"
                  />
                </el-select>
              </div>
              
              <el-divider>已标注列表</el-divider>
              
        <div class="annotations-list">
          <div
                  v-for="(annotation, index) in bboxAnnotations"
            :key="index"
            class="annotation-item"
            :class="{ selected: selectedAnnotation === index }"
            @click="selectAnnotation(index)"
          >
            <div class="annotation-info">
                    <div class="annotation-label">标签: {{ annotation.label }}</div>
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    @click.stop="deleteAnnotation(annotations.indexOf(annotation))"
                  >
                    删除
                  </el-button>
                </div>
                <el-empty v-if="bboxAnnotations.length === 0" description="暂无边界框标注" />
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 分类标注 -->
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('classification')" 
            label="分类" 
            name="classification"
          >
            <div class="annotation-tools">
              <div class="tool-section">
                <el-select
                  v-model="classificationValue"
                  placeholder="选择分类"
                  style="width: 100%; margin-bottom: 10px"
                >
                  <el-option
                    v-for="label in availableLabels"
                    :key="label"
                    :label="label"
                    :value="label"
                  />
                </el-select>
                
                <el-button
                  type="primary"
                  @click="saveClassification"
                  style="width: 100%"
                >
                  添加分类
                </el-button>
              </div>
              
              <el-divider>已标注列表</el-divider>
              
              <div class="annotations-list">
                <div
                  v-for="(annotation, index) in classificationAnnotations"
                  :key="index"
                  class="annotation-item"
                >
                  <div class="annotation-info">
                    <div class="annotation-label">分类值: {{ annotation.data.value }}</div>
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    @click.stop="deleteAnnotation(annotations.indexOf(annotation))"
                  >
                    删除
                  </el-button>
                </div>
                <el-empty v-if="classificationAnnotations.length === 0" description="暂无分类标注" />
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 回归标注 -->
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('regression')" 
            label="回归" 
            name="regression"
          >
            <div class="annotation-tools">
              <div class="tool-section">
                <el-input-number
                  v-model="regressionValue"
                  placeholder="输入数值"
                  style="width: 100%; margin-bottom: 10px"
                  :precision="2"
                  controls-position="right"
                />
                
                <el-button
                  type="primary"
                  @click="saveRegression"
                  style="width: 100%"
                >
                  添加回归值
                </el-button>
              </div>
              
              <el-divider>已标注列表</el-divider>
              
              <div class="annotations-list">
                <div
                  v-for="(annotation, index) in regressionAnnotations"
                  :key="index"
                  class="annotation-item"
                >
                  <div class="annotation-info">
                    <div class="annotation-label">数值: {{ annotation.data.value }}</div>
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    @click.stop="deleteAnnotation(annotations.indexOf(annotation))"
                  >
                    删除
                  </el-button>
                </div>
                <el-empty v-if="regressionAnnotations.length === 0" description="暂无回归标注" />
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 多边形标注 -->
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('polygon')" 
            label="多边形" 
            name="polygon"
          >
            <div class="annotation-tools">
              <div class="tool-section">
                <el-button
                  :type="currentTool === 'polygon' ? 'primary' : 'default'"
                  @click="setTool('polygon')"
                  style="width: 100%; margin-bottom: 10px"
                >
                  <el-icon><Edit /></el-icon>
                  绘制多边形
                </el-button>
                
                <el-select 
                  v-model="selectedLabel" 
                  placeholder="选择标签" 
                  style="width: 100%; margin-bottom: 10px"
                >
                  <el-option
                    v-for="label in availableLabels"
                    :key="label"
                    :label="label"
                    :value="label"
                  />
                </el-select>
              </div>
              
              <el-divider>已标注列表</el-divider>
              
              <div class="annotations-list">
                <div
                  v-for="(annotation, index) in polygonAnnotations"
                  :key="index"
                  class="annotation-item"
                >
                  <div class="annotation-info">
                    <div class="annotation-label">标签: {{ annotation.label }}</div>
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    @click.stop="deleteAnnotation(annotations.indexOf(annotation))"
                  >
                    删除
                  </el-button>
                </div>
                <el-empty v-if="polygonAnnotations.length === 0" description="暂无多边形标注" />
              </div>
            </div>
          </el-tab-pane>
          
          <!-- 关键点标注 -->
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('keypoint')" 
            label="关键点" 
            name="keypoint"
          >
            <div class="annotation-tools">
              <div class="tool-section">
                <el-button
                  :type="currentTool === 'keypoint' ? 'primary' : 'default'"
                  @click="setTool('keypoint')"
                  style="width: 100%; margin-bottom: 10px"
                >
                  <el-icon><Location /></el-icon>
                  标记关键点
                </el-button>
                
                <el-select 
                  v-model="selectedLabel" 
                  placeholder="选择标签" 
                  style="width: 100%; margin-bottom: 10px"
                >
                  <el-option
                    v-for="label in availableLabels"
                    :key="label"
                    :label="label"
                    :value="label"
                  />
                </el-select>
              </div>
              
              <el-divider>已标注列表</el-divider>
              
              <div class="annotations-list">
                <div
                  v-for="(annotation, index) in keypointAnnotations"
                  :key="index"
                  class="annotation-item"
                >
                  <div class="annotation-info">
                    <div class="annotation-label">标签: {{ annotation.label }}</div>
                  </div>
              <el-button
                type="danger"
                size="small"
                    @click.stop="deleteAnnotation(annotations.indexOf(annotation))"
              >
                删除
              </el-button>
            </div>
                <el-empty v-if="keypointAnnotations.length === 0" description="暂无关键点标注" />
          </div>
        </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
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
const activeAnnotationType = ref('')  // 当前激活的标注类型 Tab
const selectedLabel = ref('')
const availableLabels = ref([])
const availableAnnotationTypes = ref([])  // 任务支持的标注类型
const annotations = ref([])
const selectedAnnotation = ref(-1)
const classificationValue = ref('')  // 分类值
const regressionValue = ref(0)  // 回归值

const imageUrl = ref('')
const imageInfo = ref({ width: 0, height: 0 })

// 画布相关状态
const canvas = ref(null)
const ctx = ref(null)
const isDrawing = ref(false)
const startPoint = ref({ x: 0, y: 0 })
const currentPoint = ref({ x: 0, y: 0 })

// 计算属性：按类型过滤标注
const bboxAnnotations = computed(() => {
  return annotations.value.filter(a => a.type === 'bbox')
})

const classificationAnnotations = computed(() => {
  return annotations.value.filter(a => a.type === 'classification')
})

const regressionAnnotations = computed(() => {
  return annotations.value.filter(a => a.type === 'regression')
})

const polygonAnnotations = computed(() => {
  return annotations.value.filter(a => a.type === 'polygon')
})

const keypointAnnotations = computed(() => {
  return annotations.value.filter(a => a.type === 'keypoint')
})

// 监听 Tab 切换，自动设置工具
watch(activeAnnotationType, (newType) => {
  if (newType && newType !== 'select') {
    setTool(newType)
  }
})

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
    classification: '分类',
    regression: '回归'
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

const saveClassification = () => {
  if (!classificationValue.value) {
    ElMessage.warning('请选择分类')
    return
  }
  
  const annotation = {
    type: 'classification',
    label: classificationValue.value,
    data: { value: classificationValue.value },
    id: Date.now()
  }
  
  annotations.value.push(annotation)
  ElMessage.success('分类已添加')
}

const saveRegression = () => {
  if (regressionValue.value === null || regressionValue.value === undefined) {
    ElMessage.warning('请输入数值')
    return
  }
  
  const annotation = {
    type: 'regression',
    label: 'regression_value',
    data: { value: regressionValue.value },
    id: Date.now()
  }
  
  annotations.value.push(annotation)
  ElMessage.success('回归值已添加')
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
        data: annotation.data,
        status: 'submitted'  // 标记为已提交
      })
    }
    
    ElMessage.success('标注保存成功')
    
    // 获取下一张未标注的图像
    try {
      const response = await api.get(`/files/task/${taskId}/next-unannotated`, {
        params: {
          current_image_id: parseInt(imageId)
        }
      })
      
      if (response.data) {
        ElMessage.success('正在跳转到下一张图像...')
        // 1秒后跳转到下一张
        setTimeout(() => {
          router.push(`/annotate/${taskId}/${response.data.id}`)
          // 重新加载页面数据
          window.location.href = `/annotate/${taskId}/${response.data.id}`
        }, 1000)
      } else {
        ElMessage.success('恭喜！所有图像都已标注完成')
        // 3秒后返回任务详情页
        setTimeout(() => {
          router.push(`/tasks/${taskId}`)
        }, 3000)
      }
    } catch (error) {
      console.error('获取下一张图像失败:', error)
      // 即使获取失败，也不影响保存成功的提示
    }
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
    const imagePath = response.data.file_path
    
    // 构建完整的图像 URL
    if (imagePath.startsWith('http')) {
      imageUrl.value = imagePath
    } else {
      // 使用当前页面的协议和主机，端口改为8000（后端端口）
      const protocol = window.location.protocol
      const hostname = window.location.hostname
      imageUrl.value = `${protocol}//${hostname}:8000${imagePath}`
    }
    
    console.log('加载图像:', imageUrl.value)
  } catch (error) {
    console.error('获取图像失败:', error)
    ElMessage.error('获取图像失败')
  }
}

const fetchTaskLabels = async () => {
  try {
    const response = await api.get(`/tasks/${taskId}`)
    availableLabels.value = response.data.labels || []
    
    // 获取支持的标注类型
    if (response.data.annotation_types && response.data.annotation_types.length > 0) {
      availableAnnotationTypes.value = response.data.annotation_types
    } else {
      // 兼容旧数据，使用 annotation_type
      availableAnnotationTypes.value = [response.data.annotation_type]
    }
    
    // 默认激活第一个标注类型的 Tab
    if (availableAnnotationTypes.value.length > 0) {
      activeAnnotationType.value = availableAnnotationTypes.value[0]
    }
    
    console.log('支持的标注类型:', availableAnnotationTypes.value)
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
  background: #f5f7fa;
}

.top-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.toolbar-left h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.toolbar-right {
  display: flex;
  gap: 10px;
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
  width: 360px;
  background: white;
  border-left: 1px solid #e4e7ed;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.annotation-tools {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tool-section {
  margin-bottom: 12px;
}

.annotations-list {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 400px);
}

.annotation-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 8px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.annotation-item:hover {
  background: #ecf5ff;
  border-color: #c6e2ff;
}

.annotation-item.selected {
  background: #e3f2fd;
  border-color: #2196f3;
  box-shadow: 0 2px 4px rgba(33, 150, 243, 0.2);
}

.annotation-info {
  flex: 1;
  margin-right: 10px;
}

.annotation-label {
  font-weight: 500;
  margin-bottom: 4px;
  color: #303133;
  font-size: 14px;
}

.annotation-value {
  font-size: 12px;
  color: #606266;
}

:deep(.el-tabs__header) {
  margin: 0;
  padding: 0 16px;
  background: #fafafa;
}

:deep(.el-tabs__content) {
  padding: 0;
  height: calc(100% - 40px);
  overflow: hidden;
}

:deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto;
}

:deep(.el-divider__text) {
  font-weight: 500;
  color: #606266;
}
</style>
