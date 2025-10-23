<template>
  <div class="annotation-canvas-container">
    <canvas
      ref="canvas"
      :width="canvasWidth"
      :height="canvasHeight"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @wheel="handleWheel"
      class="annotation-canvas"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  imageUrl: {
    type: String,
    required: true
  },
  annotations: {
    type: Array,
    default: () => []
  },
  currentTool: {
    type: String,
    default: 'select'
  }
})

const emit = defineEmits(['annotation-added', 'annotation-updated', 'annotation-deleted'])

const canvas = ref(null)
const canvasWidth = ref(800)
const canvasHeight = ref(600)
const ctx = ref(null)
const isDrawing = ref(false)
const startPoint = ref({ x: 0, y: 0 })
const currentPoint = ref({ x: 0, y: 0 })

onMounted(() => {
  if (canvas.value) {
    ctx.value = canvas.value.getContext('2d')
    loadImage()
  }
})

const loadImage = () => {
  if (!props.imageUrl) return
  
  const img = new Image()
  img.onload = () => {
    canvasWidth.value = img.naturalWidth
    canvasHeight.value = img.naturalHeight
    canvas.value.width = img.naturalWidth
    canvas.value.height = img.naturalHeight
    
    if (ctx.value) {
      ctx.value.drawImage(img, 0, 0)
      drawAnnotations()
    }
  }
  img.src = props.imageUrl
}

const drawAnnotations = () => {
  if (!ctx.value) return
  
  // 清除画布
  ctx.value.clearRect(0, 0, canvasWidth.value, canvasHeight.value)
  
  // 重新绘制图像
  const img = new Image()
  img.onload = () => {
    ctx.value.drawImage(img, 0, 0)
    
    // 绘制标注
    props.annotations.forEach((annotation, index) => {
      drawAnnotation(annotation, index)
    })
  }
  img.src = props.imageUrl
}

const drawAnnotation = (annotation, index) => {
  if (!ctx.value) return
  
  ctx.value.strokeStyle = '#ff0000'
  ctx.value.lineWidth = 2
  
  if (annotation.type === 'bbox') {
    const { x, y, width, height } = annotation.data
    ctx.value.strokeRect(x, y, width, height)
    
    // 绘制标签
    ctx.value.fillStyle = '#ff0000'
    ctx.value.font = '12px Arial'
    ctx.value.fillText(annotation.label, x, y - 5)
  } else if (annotation.type === 'keypoint') {
    const { x, y } = annotation.data
    ctx.value.beginPath()
    ctx.value.arc(x, y, 5, 0, 2 * Math.PI)
    ctx.value.fill()
    
    ctx.value.fillStyle = '#ff0000'
    ctx.value.font = '12px Arial'
    ctx.value.fillText(annotation.label, x + 10, y - 5)
  }
}

const handleMouseDown = (event) => {
  if (props.currentTool === 'select') return
  
  const rect = canvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  startPoint.value = { x, y }
  isDrawing.value = true
  
  if (props.currentTool === 'keypoint') {
    addKeypoint(x, y)
  }
}

const handleMouseMove = (event) => {
  if (!isDrawing.value || props.currentTool === 'keypoint') return
  
  const rect = canvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  currentPoint.value = { x, y }
  
  // 重绘画布
  drawAnnotations()
  
  // 绘制当前正在绘制的形状
  if (props.currentTool === 'bbox') {
    drawBoundingBox(startPoint.value, currentPoint.value)
  }
}

const handleMouseUp = (event) => {
  if (!isDrawing.value) return
  
  const rect = canvas.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top
  
  if (props.currentTool === 'bbox') {
    addBoundingBox(startPoint.value, { x, y })
  }
  
  isDrawing.value = false
}

const handleWheel = (event) => {
  event.preventDefault()
  // 实现缩放功能
}

const addBoundingBox = (start, end) => {
  const x = Math.min(start.x, end.x)
  const y = Math.min(start.y, end.y)
  const width = Math.abs(end.x - start.x)
  const height = Math.abs(end.y - start.y)
  
  if (width < 5 || height < 5) return
  
  const annotation = {
    type: 'bbox',
    label: '未命名',
    data: { x, y, width, height }
  }
  
  emit('annotation-added', annotation)
}

const addKeypoint = (x, y) => {
  const annotation = {
    type: 'keypoint',
    label: '未命名',
    data: { x, y }
  }
  
  emit('annotation-added', annotation)
}

const drawBoundingBox = (start, end) => {
  if (!ctx.value) return
  
  ctx.value.strokeStyle = '#ff0000'
  ctx.value.lineWidth = 2
  ctx.value.setLineDash([5, 5])
  
  const x = Math.min(start.x, end.x)
  const y = Math.min(start.y, end.y)
  const width = Math.abs(end.x - start.x)
  const height = Math.abs(end.y - start.y)
  
  ctx.value.strokeRect(x, y, width, height)
  ctx.value.setLineDash([])
}

// 监听props变化
watch(() => props.imageUrl, loadImage)
watch(() => props.annotations, drawAnnotations, { deep: true })
</script>

<style scoped>
.annotation-canvas-container {
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f0f0f0;
  border: 1px solid #ddd;
}

.annotation-canvas {
  border: 1px solid #ddd;
  cursor: crosshair;
}

.annotation-canvas.drawing {
  cursor: crosshair;
}

.annotation-canvas.selecting {
  cursor: move;
}
</style>
