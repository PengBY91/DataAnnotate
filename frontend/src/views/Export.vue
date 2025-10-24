<template>
  <div class="export">
    <div class="page-header">
      <h1>导出管理</h1>
      <el-button type="primary" @click="showExportDialog = true">
        <el-icon><Download /></el-icon>
        新建导出
      </el-button>
    </div>
    
    <!-- 导出历史 -->
    <el-card class="export-history-card">
      <template #header>
        <div class="card-header">
          <span>导出历史</span>
          <el-button @click="fetchExportHistory">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table :data="exportHistory" style="width: 100%" v-loading="loading">
        <el-table-column prop="task_title" label="任务" width="200" />
        
        <el-table-column prop="format" label="格式" width="120">
          <template #default="{ row }">
            <el-tag :type="getFormatTag(row.format)">
              {{ getFormatName(row.format) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">
              {{ getStatusName(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="file_size" label="文件大小" width="120">
          <template #default="{ row }">
            <span v-if="row.file_size">{{ formatFileSize(row.file_size) }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="completed_at" label="完成时间" width="160">
          <template #default="{ row }">
            <span v-if="row.completed_at">{{ formatDate(row.completed_at) }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'completed' && row.file_path"
              type="primary"
              size="small"
              @click="downloadExport(row.export_id)"
            >
              下载
            </el-button>
            <el-button
              v-if="row.status === 'processing'"
              type="info"
              size="small"
              @click="checkProgress(row.export_id)"
            >
              查看进度
            </el-button>
            <el-button
              v-if="row.status === 'failed'"
              type="danger"
              size="small"
              @click="retryExport(row)"
            >
              重试
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 导出对话框 -->
    <el-dialog
      v-model="showExportDialog"
      title="新建导出"
      width="600px"
    >
      <el-form :model="exportForm" :rules="exportRules" ref="exportFormRef" label-width="100px">
        <el-form-item label="任务" prop="task_id">
          <el-select v-model="exportForm.task_id" placeholder="选择任务" style="width: 100%">
            <el-option
              v-for="task in tasks"
              :key="task.id"
              :label="task.title"
              :value="task.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="导出格式" prop="format">
          <el-select v-model="exportForm.format" placeholder="选择格式" style="width: 100%">
            <el-option
              v-for="format in exportFormats"
              :key="format.value"
              :label="format.name"
              :value="format.value"
            >
              <div>
                <div>{{ format.name }}</div>
                <div style="font-size: 12px; color: #666;">{{ format.description }}</div>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="包含图像">
          <el-switch v-model="exportForm.include_images" />
          <span style="margin-left: 10px; color: #666;">
            是否在导出文件中包含原始图像
          </span>
        </el-form-item>
        
        <el-form-item label="状态筛选">
          <el-checkbox-group v-model="exportForm.status_filter">
            <el-checkbox label="approved">已通过</el-checkbox>
            <el-checkbox label="rejected">已拒绝</el-checkbox>
            <el-checkbox label="submitted">待审核</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitExport"
          :loading="exporting"
        >
          开始导出
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 进度对话框 -->
    <el-dialog
      v-model="showProgressDialog"
      title="导出进度"
      width="500px"
    >
      <div v-if="currentProgress" class="progress-dialog">
        <div class="progress-info">
          <div class="progress-text">{{ currentProgress.message }}</div>
          <el-progress
            :percentage="currentProgress.progress"
            :status="getProgressStatus(currentProgress.status)"
          />
        </div>
        
        <div v-if="currentProgress.status === 'completed'" class="completion-info">
          <el-alert
            title="导出完成"
            type="success"
            :closable="false"
            style="margin-top: 20px;"
          />
          <div style="margin-top: 20px; text-align: center;">
            <el-button type="primary" @click="downloadCurrentExport">
              下载文件
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const route = useRoute()

// 数据状态
const loading = ref(false)
const exporting = ref(false)
const exportHistory = ref([])
const tasks = ref([])
const exportFormats = ref([])

// 对话框状态
const showExportDialog = ref(false)
const showProgressDialog = ref(false)
const currentProgress = ref(null)

// 导出表单
const exportForm = reactive({
  task_id: null,
  format: 'json',
  include_images: false,
  status_filter: ['approved']
})

const exportRules = {
  task_id: [{ required: true, message: '请选择任务', trigger: 'change' }],
  format: [{ required: true, message: '请选择导出格式', trigger: 'change' }]
}

const exportFormRef = ref()

// 获取导出历史
const fetchExportHistory = async () => {
  try {
    loading.value = true
    const response = await api.get('/export/history')
    exportHistory.value = response.data
  } catch (error) {
    console.error('获取导出历史失败:', error)
    ElMessage.error('获取导出历史失败')
  } finally {
    loading.value = false
  }
}

// 获取任务列表
const fetchTasks = async () => {
  try {
    const response = await api.get('/tasks')
    tasks.value = response.data
  } catch (error) {
    console.error('获取任务列表失败:', error)
  }
}

// 获取导出格式
const fetchExportFormats = async () => {
  try {
    const response = await api.get('/export/formats')
    exportFormats.value = response.data.formats
  } catch (error) {
    console.error('获取导出格式失败:', error)
  }
}

// 提交导出
const submitExport = async () => {
  try {
    await exportFormRef.value.validate()
    
    exporting.value = true
    const response = await api.post('/export/export', exportForm)
    
    ElMessage.success('导出任务已创建')
    showExportDialog.value = false
    await fetchExportHistory()
    
    // 显示进度对话框
    currentProgress.value = {
      export_id: response.data.export_id,
      status: 'processing',
      progress: 0,
      message: '正在处理中...'
    }
    showProgressDialog.value = true
    
    // 开始轮询进度
    pollProgress(response.data.export_id)
  } catch (error) {
    console.error('创建导出失败:', error)
    ElMessage.error('创建导出失败')
  } finally {
    exporting.value = false
  }
}

// 轮询进度
const pollProgress = async (exportId) => {
  const pollInterval = setInterval(async () => {
    try {
      const response = await api.get(`/export/${exportId}/status`)
      currentProgress.value = response.data
      
      if (response.data.status === 'completed' || response.data.status === 'failed') {
        clearInterval(pollInterval)
        await fetchExportHistory()
      }
    } catch (error) {
      console.error('获取进度失败:', error)
      clearInterval(pollInterval)
    }
  }, 2000)
}

// 检查进度
const checkProgress = async (exportId) => {
  try {
    const response = await api.get(`/export/${exportId}/status`)
    currentProgress.value = response.data
    showProgressDialog.value = true
  } catch (error) {
    console.error('获取进度失败:', error)
    ElMessage.error('获取进度失败')
  }
}

// 下载导出
const downloadExport = async (exportId) => {
  try {
    const response = await api.get(`/export/${exportId}/download`, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `export_${exportId}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('下载开始')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

// 下载当前导出
const downloadCurrentExport = () => {
  if (currentProgress.value) {
    downloadExport(currentProgress.value.export_id)
    showProgressDialog.value = false
  }
}

// 重试导出
const retryExport = async (exportItem) => {
  try {
    exportForm.task_id = exportItem.task_id
    exportForm.format = exportItem.format
    exportForm.include_images = false // 默认不包含图像
    exportForm.status_filter = ['approved']
    
    showExportDialog.value = true
  } catch (error) {
    console.error('重试导出失败:', error)
    ElMessage.error('重试导出失败')
  }
}

// 获取格式名称
const getFormatName = (format) => {
  const formatMap = {
    'csv': 'CSV',
    'pascal_voc': 'Pascal VOC',
    'coco': 'COCO',
    'yolo': 'YOLO',
    'json': 'JSON'
  }
  return formatMap[format] || format
}

// 获取格式标签
const getFormatTag = (format) => {
  const tagMap = {
    'csv': 'success',
    'pascal_voc': 'info',
    'coco': 'warning',
    'yolo': 'primary',
    'json': 'danger'
  }
  return tagMap[format] || ''
}

// 获取状态名称
const getStatusName = (status) => {
  const statusMap = {
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return statusMap[status] || status
}

// 获取状态标签
const getStatusTag = (status) => {
  const tagMap = {
    'processing': 'info',
    'completed': 'success',
    'failed': 'danger'
  }
  return tagMap[status] || ''
}

// 获取进度状态
const getProgressStatus = (status) => {
  const statusMap = {
    'processing': '',
    'completed': 'success',
    'failed': 'exception'
  }
  return statusMap[status] || ''
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchExportHistory()
  fetchTasks()
  fetchExportFormats()
  
  // 如果URL中有task_id参数，自动选择该任务
  if (route.query.task_id) {
    exportForm.task_id = parseInt(route.query.task_id)
  }
})
</script>

<style scoped>
.export {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.export-history-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-muted {
  color: #999;
}

.progress-dialog .progress-info {
  margin-bottom: 20px;
}

.progress-dialog .progress-text {
  margin-bottom: 10px;
  font-size: 14px;
  color: #666;
}

.completion-info {
  margin-top: 20px;
}
</style>
