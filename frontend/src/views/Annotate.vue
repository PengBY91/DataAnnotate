<template>
  <div class="annotate-container-fullscreen">
    <!-- 顶部工具栏 - 压缩为一行 -->
    <div class="compact-toolbar">
      <!-- 左侧：返回按钮 -->
      <div class="toolbar-section">
        <el-button size="small" @click="goBack">
          <el-icon><Back /></el-icon>
          返回
        </el-button>
      </div>
      
      <!-- 中间：标注工具选择 -->
      <div class="toolbar-section toolbar-center">
        <el-tabs v-model="activeAnnotationType" type="border-card" size="small" style="flex: 1;">
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('bbox')" 
            label="边界框" 
            name="bbox"
          >
            <el-select 
              v-model="selectedLabel" 
              placeholder="选择标签" 
              size="small"
              style="width: 150px; margin-right: 10px;"
            >
              <el-option
                v-for="label in availableLabels"
                :key="label"
                :label="label"
                :value="label"
              />
            </el-select>
            <el-button size="small" :type="currentTool === 'bbox' ? 'primary' : 'default'" @click="setTool('bbox')">
              绘制边界框
            </el-button>
          </el-tab-pane>
          
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('classification')" 
            label="分类" 
            name="classification"
          >
            <el-select 
              v-model="classificationValue" 
              placeholder="选择分类" 
              size="small"
              style="width: 150px; margin-right: 10px;"
            >
              <el-option
                v-for="label in availableLabels"
                :key="label"
                :label="label"
                :value="label"
              />
            </el-select>
            <el-button size="small" type="primary" @click="saveClassification">添加</el-button>
          </el-tab-pane>
          
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('regression')" 
            label="回归" 
            name="regression"
          >
            <el-input-number
              v-model="regressionValue"
              size="small"
              :precision="2"
              style="width: 150px; margin-right: 10px;"
            />
            <el-button size="small" type="primary" @click="saveRegression">添加</el-button>
          </el-tab-pane>
          
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('ranking')" 
            label="排序" 
            name="ranking"
          >
            <span style="margin-right: 10px; font-size: 12px;">最大范围: {{ rankingCount }}</span>
            <el-input
              v-model="rankingValue"
              placeholder="如: 213"
              size="small"
              maxlength="20"
              style="width: 120px; margin-right: 10px;"
              @input="validateRankingInput"
            />
            <el-button size="small" type="primary" @click="saveRanking" :disabled="!!rankingError || !rankingValue">添加</el-button>
            <span v-if="rankingError" style="color: #F56C6C; font-size: 12px; margin-left: 10px;">{{ rankingError }}</span>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <!-- 右侧：操作按钮 -->
      <div class="toolbar-section">
        <el-button-group>
          <el-button size="small" @click="undo" title="撤销">
            <el-icon><RefreshLeft /></el-icon>
          </el-button>
          <el-button size="small" @click="redo" title="重做">
            <el-icon><RefreshRight /></el-icon>
          </el-button>
          <el-button size="small" @click="clearAll" title="清空">
            <el-icon><Delete /></el-icon>
          </el-button>
        </el-button-group>
        <el-button type="success" size="small" @click="saveAnnotations" style="margin-left: 10px;">
          <el-icon><Check /></el-icon>
          保存并继续
        </el-button>
      </div>
    </div>
    
    <!-- 图像显示区域 - 占满剩余空间 -->
    <div class="image-container-fullscreen">
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
      
      <!-- 标注列表悬浮面板 -->
      <div class="annotations-floating-panel" v-if="annotations.length > 0">
        <div class="panel-header">
          已标注 ({{ annotations.length }})
          <el-button size="small" text @click="showAnnotationList = !showAnnotationList">
            {{ showAnnotationList ? '收起' : '展开' }}
          </el-button>
        </div>
        <div v-show="showAnnotationList" class="panel-content">
          <div
            v-for="(annotation, index) in annotations"
            :key="index"
            class="floating-annotation-item"
            :class="{ selected: selectedAnnotation === index }"
            @click="selectAnnotation(index)"
          >
            <span class="annotation-type-badge">{{ getAnnotationTypeText(annotation.type) }}</span>
            <span class="annotation-label-text">{{ annotation.label || (annotation.data && annotation.data.value) }}</span>
            <el-button
              type="danger"
              size="small"
              text
              @click.stop="deleteAnnotation(index)"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
      
      <!-- 废弃的旧代码，保留结构以防编译错误 -->
      <div style="display: none;">
        <el-tabs v-model="activeAnnotationType" type="card">
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
          
          <!-- 排序标注 -->
          <el-tab-pane 
            v-if="availableAnnotationTypes.includes('ranking')" 
            label="排序" 
            name="ranking"
          >
            <div class="annotation-tools">
              <div class="tool-section">
                <el-alert
                  title="排序说明"
                  type="info"
                  :closable="false"
                  style="margin-bottom: 15px"
                >
                  <template #default>
                    <p style="margin: 0; font-size: 13px;">
                      请输入排序结果，例如有3个元素需要排序，排序结果是 2、1、3，则输入 "213"。
                    </p>
                    <p style="margin: 5px 0 0 0; font-size: 13px; color: #E6A23C;">
                      排序必须是从1开始的连续数字，不能重复，不能缺失。
                    </p>
                  </template>
                </el-alert>
                
                <el-form-item label="排序最大范围">
                  <el-input-number
                    v-model="rankingCount"
                    :min="2"
                    :max="20"
                    placeholder="排序最大范围"
                    style="width: 100%; margin-bottom: 10px"
                    controls-position="right"
                    disabled
                  />
                  <div style="color: #999; font-size: 12px; margin-top: 4px;">
                    排序最大范围由任务配置决定，不可修改
                  </div>
                </el-form-item>
                
                <el-form-item label="排序结果">
                  <el-input
                    v-model="rankingValue"
                    placeholder="例如：213"
                    style="width: 100%; margin-bottom: 10px"
                    maxlength="20"
                    @input="validateRankingInput"
                  />
                  <div v-if="rankingError" style="color: #F56C6C; font-size: 12px; margin-top: 4px;">
                    {{ rankingError }}
                  </div>
                  <div v-else style="color: #999; font-size: 12px; margin-top: 4px;">
                    输入1到{{ rankingCount }}的排列组合
                  </div>
                </el-form-item>
                
                <el-button
                  type="primary"
                  @click="saveRanking"
                  :disabled="!!rankingError || !rankingValue"
                  style="width: 100%"
                >
                  添加排序
                </el-button>
              </div>
              
              <el-divider>已标注列表</el-divider>
              
              <div class="annotations-list">
                <div
                  v-for="(annotation, index) in rankingAnnotations"
                  :key="index"
                  class="annotation-item"
                >
                  <div class="annotation-info">
                    <div class="annotation-label">
                      排序: {{ annotation.data.ranking }} 
                      <span style="color: #909399; font-size: 12px;">
                        ({{ annotation.data.expected_count }}个元素)
                      </span>
                    </div>
                    <div class="annotation-display" style="margin-top: 5px; font-size: 12px; color: #606266;">
                      {{ formatRankingDisplay(annotation.data.ranking) }}
                    </div>
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    @click.stop="deleteAnnotation(annotations.indexOf(annotation))"
                  >
                    删除
                  </el-button>
                </div>
                <el-empty v-if="rankingAnnotations.length === 0" description="暂无排序标注" />
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
const rankingValue = ref('')  // 排序输入值
const rankingCount = ref(3)  // 排序元素数量
const rankingError = ref('')  // 排序验证错误信息
const showAnnotationList = ref(true)  // 是否显示标注列表

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

const rankingAnnotations = computed(() => {
  return annotations.value.filter(a => a.type === 'ranking')
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
    regression: '回归',
    ranking: '排序'
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

// 验证排序输入
const validateRankingInput = () => {
  const value = rankingValue.value.trim()
  
  if (!value) {
    rankingError.value = ''
    return
  }
  
  // 检查是否只包含数字
  if (!/^\d+$/.test(value)) {
    rankingError.value = '排序只能包含数字'
    return
  }
  
  const numbers = value.split('').map(Number)
  const count = rankingCount.value
  
  // 检查长度
  if (numbers.length !== count) {
    rankingError.value = `排序长度应为${count}位`
    return
  }
  
  // 检查重复
  if (new Set(numbers).size !== numbers.length) {
    rankingError.value = '排序不能有重复数字'
    return
  }
  
  // 检查是否是1到n的排列
  const expectedSet = new Set(Array.from({ length: count }, (_, i) => i + 1))
  const actualSet = new Set(numbers)
  
  for (let num of actualSet) {
    if (!expectedSet.has(num)) {
      rankingError.value = `排序必须是1到${count}的排列`
      return
    }
  }
  
  // 检查是否包含0或负数
  if (numbers.some(n => n <= 0)) {
    rankingError.value = '排序必须从1开始'
    return
  }
  
  rankingError.value = ''
}

// 保存排序标注
const saveRanking = () => {
  // 再次验证
  validateRankingInput()
  
  if (rankingError.value) {
    ElMessage.warning(rankingError.value)
    return
  }
  
  if (!rankingValue.value) {
    ElMessage.warning('请输入排序')
    return
  }
  
  const annotation = {
    type: 'ranking',
    label: 'ranking_value',
    data: { 
      ranking: rankingValue.value,
      expected_count: rankingCount.value,
      ranking_list: rankingValue.value.split('').map(Number)
    },
    id: Date.now()
  }
  
  annotations.value.push(annotation)
  ElMessage.success('排序已添加')
  
  // 清空输入
  rankingValue.value = ''
  rankingError.value = ''
}

// 格式化排序显示
const formatRankingDisplay = (ranking) => {
  if (!ranking) return ''
  const numbers = ranking.split('').map(Number)
  return numbers.map((num, idx) => `第${idx + 1}位: ${num}`).join(', ')
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
    // 先删除该图像的所有被拒绝的标注
    try {
      await api.delete(`/annotations/image/${imageId}/rejected`)
    } catch (error) {
      // 如果没有被拒绝的标注，忽略错误
      console.log('没有需要删除的被拒绝标注')
    }
    
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
    
    // 获取排序配置
    if (response.data.ranking_config && response.data.ranking_config.max) {
      rankingCount.value = response.data.ranking_config.max
    } else if (response.data.ranking_max) {
      // 兼容直接存储 ranking_max 的情况
      rankingCount.value = response.data.ranking_max
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
/* 全屏容器 - 不使用 MainLayout */
.annotate-container-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  z-index: 999;
}

/* 压缩的顶部工具栏 - 一行搞定 */
.compact-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
  height: 56px;
}

.toolbar-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-center {
  flex: 1;
  max-width: 800px;
  margin: 0 20px;
}

/* 全屏图像容器 */
.image-container-fullscreen {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #2c2c2c;
  overflow: hidden;
  position: relative;
}

.image-wrapper {
  position: relative;
  display: inline-block;
  max-width: 95%;
  max-height: 95%;
}

.annotation-canvas {
  border: 2px solid #409eff;
  cursor: crosshair;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* 悬浮的标注列表面板 */
.annotations-floating-panel {
  position: absolute;
  bottom: 20px;
  right: 20px;
  width: 320px;
  max-height: 400px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  backdrop-filter: blur(10px);
  z-index: 100;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.panel-content {
  max-height: 350px;
  overflow-y: auto;
  padding: 8px;
}

.floating-annotation-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  margin-bottom: 6px;
  background: #f5f7fa;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.floating-annotation-item:hover {
  background: #ecf5ff;
  border-color: #b3d8ff;
}

.floating-annotation-item.selected {
  background: #e3f2fd;
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.annotation-type-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #409eff;
  color: white;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 10px;
  flex-shrink: 0;
}

.annotation-label-text {
  flex: 1;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Tab 样式覆盖 */
:deep(.el-tabs--border-card) {
  border: none;
  box-shadow: none;
}

:deep(.el-tabs__header) {
  background: transparent;
  border: none;
  margin: 0;
}

:deep(.el-tabs__content) {
  padding: 0;
}

:deep(.el-tabs__item) {
  padding: 6px 12px;
  height: auto;
  line-height: 1.4;
  font-size: 13px;
}
</style>
