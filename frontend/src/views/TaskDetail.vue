<template>
  <div class="task-detail">
    <div class="page-header">
      <el-button @click="$router.back()">
        <el-icon><Back /></el-icon>
        返回
      </el-button>
      <h1>{{ task?.title }}</h1>
    </div>
    
    <el-row :gutter="20">
      <el-col :span="16">
        <!-- 任务信息 -->
        <el-card class="task-info">
          <template #header>
            <span>任务信息</span>
          </template>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务名称">{{ task?.title }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(task?.status)">
                {{ getStatusText(task?.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="优先级">
              <el-tag :type="getPriorityType(task?.priority)">
                {{ getPriorityText(task?.priority) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="标注类型">{{ task?.annotation_type }}</el-descriptions-item>
            <el-descriptions-item label="总图像数">{{ task?.total_images }}</el-descriptions-item>
            <el-descriptions-item label="已标注">{{ task?.annotated_images }}</el-descriptions-item>
            <el-descriptions-item label="已审核">{{ task?.reviewed_images }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDate(task?.created_at) }}</el-descriptions-item>
          </el-descriptions>
          
          <div v-if="task?.description" class="task-description">
            <h4>任务描述</h4>
            <p>{{ task.description }}</p>
          </div>
          
          <div v-if="task?.instructions" class="task-instructions">
            <h4>标注说明</h4>
            <p>{{ task.instructions }}</p>
          </div>
          
          <div v-if="task?.labels?.length" class="task-labels">
            <h4>标签列表</h4>
            <el-tag
              v-for="label in task.labels"
              :key="label"
              style="margin-right: 8px; margin-bottom: 8px"
            >
              {{ label }}
            </el-tag>
          </div>
        </el-card>
        
        <!-- 图像列表 -->
        <el-card class="images-card">
          <template #header>
            <div class="card-header">
              <span>图像列表</span>
              <el-button
                v-if="canUpload"
                type="primary"
                @click="showUploadDialog = true"
              >
                上传图像
              </el-button>
            </div>
          </template>
          
          <el-table :data="images" style="width: 100%" v-loading="imagesLoading">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="width" label="宽度" />
            <el-table-column prop="height" label="高度" />
            <el-table-column label="标注状态">
              <template #default="{ row }">
                <el-tag :type="row.is_annotated ? 'success' : 'info'">
                  {{ row.is_annotated ? '已标注' : '未标注' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="审核状态">
              <template #default="{ row }">
                <el-tag :type="row.is_reviewed ? 'success' : 'warning'">
                  {{ row.is_reviewed ? '已审核' : '未审核' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  @click="startAnnotate(row.id)"
                >
                  标注
                </el-button>
                <el-button
                  type="info"
                  size="small"
                  @click="previewImage(row)"
                >
                  预览
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <!-- 任务统计 -->
        <el-card class="task-stats">
          <template #header>
            <span>任务统计</span>
          </template>
          
          <div class="stat-item">
            <div class="stat-label">完成进度</div>
            <el-progress
              :percentage="completionPercentage"
              :color="getProgressColor(completionPercentage)"
            />
          </div>
          
          <div class="stat-item">
            <div class="stat-label">审核进度</div>
            <el-progress
              :percentage="reviewPercentage"
              :color="getProgressColor(reviewPercentage)"
            />
          </div>
        </el-card>
        
        <!-- 操作面板 -->
        <el-card class="actions-panel">
          <template #header>
            <span>操作</span>
          </template>
          
          <div class="action-buttons">
            <el-button
              v-if="canStartTask"
              type="success"
              @click="startTask"
              style="width: 100%; margin-bottom: 10px"
            >
              开始任务
            </el-button>
            
            <el-button
              v-if="canCompleteTask"
              type="warning"
              @click="completeTask"
              style="width: 100%; margin-bottom: 10px"
            >
              完成任务
            </el-button>
            
            <el-button
              type="primary"
              @click="exportAnnotations"
              style="width: 100%; margin-bottom: 10px"
            >
              导出标注
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传图像"
      width="600px"
    >
      <el-upload
        ref="uploadRef"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :data="{ task_id: taskId }"
        :file-list="fileList"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        multiple
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 jpg/png/bmp/tiff 格式，单个文件不超过50MB
          </div>
        </template>
      </el-upload>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'

const route = useRoute()
const authStore = useAuthStore()

const taskId = route.params.id
const task = ref(null)
const images = ref([])
const imagesLoading = ref(false)
const showUploadDialog = ref(false)
const fileList = ref([])

const uploadUrl = '/api/files/upload'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${authStore.token}`
}))

const completionPercentage = computed(() => {
  if (!task.value || !task.value.total_images) return 0
  return Math.round((task.value.annotated_images / task.value.total_images) * 100)
})

const reviewPercentage = computed(() => {
  if (!task.value || !task.value.total_images) return 0
  return Math.round((task.value.reviewed_images / task.value.total_images) * 100)
})

const canUpload = computed(() => {
  return authStore.hasRole(['admin', 'engineer']) || 
         (task.value && task.value.creator_id === authStore.user?.id)
})

const canStartTask = computed(() => {
  return task.value && 
         task.value.assignee_id === authStore.user?.id && 
         task.value.status === 'assigned'
})

const canCompleteTask = computed(() => {
  return task.value && 
         task.value.assignee_id === authStore.user?.id && 
         task.value.status === 'in_progress'
})

const getStatusType = (status) => {
  const statusMap = {
    pending: 'warning',
    assigned: 'info',
    in_progress: 'primary',
    completed: 'success',
    reviewed: 'success'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待分配',
    assigned: '已分配',
    in_progress: '进行中',
    completed: '已完成',
    reviewed: '已审核'
  }
  return statusMap[status] || status
}

const getPriorityType = (priority) => {
  const priorityMap = {
    low: 'info',
    medium: 'warning',
    high: 'danger',
    urgent: 'danger'
  }
  return priorityMap[priority] || 'info'
}

const getPriorityText = (priority) => {
  const priorityMap = {
    low: '低',
    medium: '中',
    high: '高',
    urgent: '紧急'
  }
  return priorityMap[priority] || priority
}

const getProgressColor = (percentage) => {
  if (percentage < 30) return '#f56c6c'
  if (percentage < 70) return '#e6a23c'
  return '#67c23a'
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

const fetchTask = async () => {
  try {
    const response = await api.get(`/tasks/${taskId}`)
    task.value = response.data
  } catch (error) {
    console.error('获取任务详情失败:', error)
    ElMessage.error('获取任务详情失败')
  }
}

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

const startAnnotate = (imageId) => {
  window.open(`/annotate/${taskId}/${imageId}`, '_blank')
}

const previewImage = (image) => {
  // 实现图像预览
  ElMessage.info('图像预览功能开发中')
}

const startTask = async () => {
  try {
    await api.post(`/tasks/${taskId}/start`)
    ElMessage.success('任务已开始')
    fetchTask()
  } catch (error) {
    console.error('开始任务失败:', error)
  }
}

const completeTask = async () => {
  try {
    await api.post(`/tasks/${taskId}/complete`)
    ElMessage.success('任务已完成')
    fetchTask()
  } catch (error) {
    console.error('完成任务失败:', error)
  }
}

const exportAnnotations = async () => {
  try {
    ElMessage.info('导出功能开发中')
  } catch (error) {
    console.error('导出失败:', error)
  }
}

const handleUploadSuccess = (response, file) => {
  ElMessage.success('上传成功')
  fetchImages()
  fetchTask()
}

const handleUploadError = (error, file) => {
  ElMessage.error('上传失败')
  console.error('上传错误:', error)
}

onMounted(() => {
  fetchTask()
  fetchImages()
})
</script>

<style scoped>
.task-detail {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.task-info {
  margin-bottom: 20px;
}

.task-description,
.task-instructions,
.task-labels {
  margin-top: 20px;
}

.task-labels {
  margin-top: 20px;
}

.images-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-stats {
  margin-bottom: 20px;
}

.stat-item {
  margin-bottom: 20px;
}

.stat-label {
  margin-bottom: 8px;
  font-weight: bold;
}

.actions-panel {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
}
</style>
