<template>
  <div class="quality-control">
    <div class="page-header">
      <h1>质量控制</h1>
      <div class="header-actions">
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ stats.total_reviews }}</div>
            <div class="stat-label">总图像数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ stats.approved_reviews }}</div>
            <div class="stat-label">已通过图像</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ stats.rejected_reviews }}</div>
            <div class="stat-label">已拒绝图像</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-value">{{ stats.approval_rate.toFixed(1) }}%</div>
            <div class="stat-label">通过率</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 筛选器 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="任务">
          <el-select v-model="filters.task_id" placeholder="选择任务" clearable>
            <el-option
              v-for="task in tasks"
              :key="task.id"
              :label="task.title"
              :value="task.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="标注员">
          <el-select v-model="filters.annotator_id" placeholder="选择标注员" clearable>
            <el-option
              v-for="annotator in annotators"
              :key="annotator.id"
              :label="annotator.full_name"
              :value="annotator.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="选择状态" clearable>
            <el-option label="待审核" value="submitted" />
            <el-option label="已通过" value="approved" />
            <el-option label="已拒绝" value="rejected" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="searchReviews">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 待审核列表 -->
    <el-card class="reviews-card">
      <template #header>
        <div class="card-header">
          <span>待审核标注</span>
          <div class="header-actions">
            <el-button 
              type="success" 
              :disabled="selectedReviews.length === 0"
              @click="batchApprove"
              :loading="batchProcessing"
            >
              批量通过 ({{ selectedReviews.length }})
            </el-button>
            <el-button @click="fetchPendingReviews">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table 
        :data="pendingReviews" 
        style="width: 100%" 
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="image_filename" label="图像" width="200">
          <template #default="{ row }">
            <el-image
              :src="getImageUrl(row.image_id)"
              :preview-src-list="[getImageUrl(row.image_id)]"
              fit="cover"
              style="width: 60px; height: 60px; border-radius: 4px;"
            />
            <div style="margin-top: 4px; font-size: 12px;">{{ row.image_filename }}</div>
          </template>
        </el-table-column>
        
        <el-table-column prop="annotator_name" label="标注员" width="120" />
        
        <el-table-column prop="annotation_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getAnnotationTypeTag(row.annotation_type)">
              {{ getAnnotationTypeName(row.annotation_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="label" label="标签" width="120" />
        
        <el-table-column prop="data" label="数据" width="200">
          <template #default="{ row }">
            <el-tooltip :content="JSON.stringify(row.data)" placement="top">
              <span class="data-preview">{{ JSON.stringify(row.data).substring(0, 50) }}...</span>
            </el-tooltip>
          </template>
        </el-table-column>
        
        <el-table-column prop="notes" label="备注" width="150">
          <template #default="{ row }">
            <span v-if="row.notes">{{ row.notes.substring(0, 30) }}...</span>
            <span v-else class="text-muted">无</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button
              type="success"
              size="small"
              @click="approveAnnotation(row)"
              :loading="reviewing"
            >
              通过
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="rejectAnnotation(row)"
              :loading="reviewing"
            >
              拒绝
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="showReviewDialogFunc(row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 审核对话框 -->
    <el-dialog
      v-model="showReviewDialog"
      title="标注审核"
      width="800px"
    >
      <div v-if="currentReview" class="review-dialog">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="image-section">
              <h4>图像预览</h4>
              <el-image
                :src="getImageUrl(currentReview.image_id)"
                fit="contain"
                style="width: 100%; max-height: 400px;"
              />
            </div>
          </el-col>
          <el-col :span="12">
            <div class="annotation-section">
              <h4>标注信息</h4>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="标注员">
                  {{ currentReview.annotator_name }}
                </el-descriptions-item>
                <el-descriptions-item label="类型">
                  {{ getAnnotationTypeName(currentReview.annotation_type) }}
                </el-descriptions-item>
                <el-descriptions-item label="标签">
                  {{ currentReview.label }}
                </el-descriptions-item>
                <el-descriptions-item label="数据">
                  <pre>{{ JSON.stringify(currentReview.data, null, 2) }}</pre>
                </el-descriptions-item>
                <el-descriptions-item label="备注" v-if="currentReview.notes">
                  {{ currentReview.notes }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>
        </el-row>
        
        <div class="review-form" style="margin-top: 20px;">
          <el-form :model="reviewForm" label-width="80px">
            <el-form-item label="审核结果">
              <el-radio-group v-model="reviewForm.status">
                <el-radio label="approved">通过</el-radio>
                <el-radio label="rejected">拒绝</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="审核备注">
              <el-input
                v-model="reviewForm.review_notes"
                type="textarea"
                :rows="3"
                placeholder="请输入审核备注（可选）"
              />
            </el-form-item>
          </el-form>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitReview"
          :loading="reviewing"
        >
          提交审核
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const authStore = useAuthStore()

// 数据状态
const loading = ref(false)
const reviewing = ref(false)
const batchProcessing = ref(false)
const selectedReviews = ref([])
const pendingReviews = ref([])
const tasks = ref([])
const annotators = ref([])
const stats = ref({
  total_reviews: 0,
  approved_reviews: 0,
  rejected_reviews: 0,
  approval_rate: 0
})

// 筛选器
const filters = reactive({
  task_id: null,
  annotator_id: null,
  status: null
})

// 审核对话框
const showReviewDialog = ref(false)
const currentReview = ref(null)
const reviewForm = reactive({
  status: 'approved',
  review_notes: ''
})

// 获取图像URL
const getImageUrl = (imageId) => {
  return `/api/files/images/${imageId}`
}

// 获取标注类型名称
const getAnnotationTypeName = (type) => {
  const typeMap = {
    'bbox': '边界框',
    'polygon': '多边形',
    'keypoint': '关键点',
    'classification': '分类',
    'regression': '回归'
  }
  return typeMap[type] || type
}

// 获取标注类型标签
const getAnnotationTypeTag = (type) => {
  const tagMap = {
    'bbox': 'success',
    'polygon': 'warning',
    'keypoint': 'info',
    'classification': 'primary',
    'regression': 'danger'
  }
  return tagMap[type] || ''
}

// 格式化日期
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 获取待审核列表
const fetchPendingReviews = async () => {
  try {
    loading.value = true
    const params = {}
    if (filters.task_id) params.task_id = filters.task_id
    if (filters.annotator_id) params.annotator_id = filters.annotator_id
    if (filters.status) params.status = filters.status
    
    const response = await api.get('/quality/pending-reviews', { params })
    pendingReviews.value = response.data
  } catch (error) {
    console.error('获取待审核列表失败:', error)
    ElMessage.error('获取待审核列表失败')
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

// 获取标注员列表
const fetchAnnotators = async () => {
  try {
    const response = await api.get('/users')
    // 只获取标注员角色的用户
    annotators.value = response.data.filter(user => user.role === 'annotator')
  } catch (error) {
    console.error('获取标注员列表失败:', error)
  }
}

// 获取统计信息
const fetchStats = async () => {
  try {
    if (filters.task_id) {
      // 如果有选中的任务，获取该任务的质量统计
      const response = await api.get(`/quality/metrics/${filters.task_id}`)
      stats.value = {
        total_reviews: response.data.total_annotations,
        approved_reviews: response.data.approved_annotations,
        rejected_reviews: response.data.rejected_annotations,
        approval_rate: response.data.approval_rate
      }
    } else {
      // 如果没有选中任务，获取个人审核统计
      const response = await api.get('/quality/review-stats')
      stats.value = response.data
    }
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

// 通过标注
const approveAnnotation = async (review) => {
  try {
    reviewing.value = true
    await api.post('/quality/review', {
      annotation_id: review.id,
      status: 'approved'
    })
    
    ElMessage.success('标注已通过')
    await fetchPendingReviews()
    await fetchStats()
  } catch (error) {
    console.error('审核失败:', error)
    ElMessage.error('审核失败')
  } finally {
    reviewing.value = false
  }
}

// 拒绝标注
const rejectAnnotation = async (review) => {
  try {
    reviewing.value = true
    await api.post('/quality/review', {
      annotation_id: review.id,
      status: 'rejected'
    })
    
    ElMessage.success('标注已拒绝')
    await fetchPendingReviews()
    await fetchStats()
  } catch (error) {
    console.error('审核失败:', error)
    ElMessage.error('审核失败')
  } finally {
    reviewing.value = false
  }
}

// 显示审核对话框
const showReviewDialogFunc = (review) => {
  currentReview.value = review
  reviewForm.status = 'approved'
  reviewForm.review_notes = ''
  showReviewDialog.value = true
}

// 提交审核
const submitReview = async () => {
  try {
    reviewing.value = true
    await api.post('/quality/review', {
      annotation_id: currentReview.value.id,
      status: reviewForm.status,
      review_notes: reviewForm.review_notes
    })
    
    ElMessage.success('审核完成')
    showReviewDialog.value = false
    await fetchPendingReviews()
    await fetchStats()
  } catch (error) {
    console.error('审核失败:', error)
    ElMessage.error('审核失败')
  } finally {
    reviewing.value = false
  }
}

// 重置筛选器
const searchReviews = async () => {
  await fetchPendingReviews()
  await fetchStats()
}

const resetFilters = () => {
  filters.task_id = null
  filters.annotator_id = null
  filters.status = null
  fetchPendingReviews()
  fetchStats()
}

// 刷新数据
const refreshData = () => {
  fetchPendingReviews()
  fetchStats()
}

// 处理选择变化
const handleSelectionChange = (selection) => {
  selectedReviews.value = selection
}

// 批量审核通过
const batchApprove = async () => {
  if (selectedReviews.value.length === 0) {
    ElMessage.warning('请选择要审核的标注')
    return
  }
  
  try {
    batchProcessing.value = true
    
    // 并行处理所有选中的标注
    const promises = selectedReviews.value.map(review => 
      api.post('/quality/review', {
        annotation_id: review.id,
        status: 'approved'
      })
    )
    
    await Promise.all(promises)
    
    ElMessage.success(`批量审核通过 ${selectedReviews.value.length} 个标注`)
    selectedReviews.value = []
    await fetchPendingReviews()
    await fetchStats()
  } catch (error) {
    console.error('批量审核失败:', error)
    ElMessage.error('批量审核失败')
  } finally {
    batchProcessing.value = false
  }
}

onMounted(() => {
  fetchPendingReviews()
  fetchTasks()
  fetchAnnotators()
  fetchStats()
})
</script>

<style scoped>
.quality-control {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-content {
  padding: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.filter-card {
  margin-bottom: 20px;
}

.reviews-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.data-preview {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}

.text-muted {
  color: #999;
}

.review-dialog .image-section,
.review-dialog .annotation-section {
  margin-bottom: 20px;
}

.review-dialog h4 {
  margin-bottom: 10px;
  color: #333;
}

.review-dialog pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  max-height: 200px;
  overflow-y: auto;
}
</style>
