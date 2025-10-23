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
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>任务信息</span>
              <el-button
                v-if="canEditTask"
                type="primary"
                size="small"
                @click="openEditDialog"
              >
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
            </div>
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
            <el-descriptions-item label="标注类型">
              <el-tag 
                v-for="type in getAnnotationTypes(task)" 
                :key="type"
                style="margin-right: 8px"
              >
                {{ getAnnotationTypeLabel(type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="每张图片标注人数">
              {{ task?.required_annotations_per_image || 1 }} 人
            </el-descriptions-item>
            <el-descriptions-item label="分配给" :span="2">
              <div v-if="task?.assignees && task.assignees.length > 0">
                <el-tag
                  v-for="assignee in task.assignees"
                  :key="assignee.user_id"
                  style="margin-right: 8px; margin-bottom: 4px"
                >
                  {{ assignee.full_name }} ({{ assignee.username }})
                  <el-badge
                    v-if="assignee.completed_images > 0"
                    :value="assignee.completed_images"
                    style="margin-left: 8px"
                    type="success"
                  />
                </el-tag>
              </div>
              <div v-else-if="task?.assignee_id">
                <el-tag>{{ getUserName(task.assignee_id) }}</el-tag>
              </div>
              <span v-else style="color: #999;">未分配</span>
            </el-descriptions-item>
            <el-descriptions-item label="审核人">
              <span v-if="task?.reviewer_id">
                {{ getUserName(task.reviewer_id) }}
              </span>
              <span v-else style="color: #999;">未指定</span>
            </el-descriptions-item>
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
              <div style="display: flex; gap: 10px;">
                <el-button
                  v-if="canReview && selectedImages.length > 0"
                  type="success"
                  size="small"
                  @click="batchReview('approved')"
                >
                  批量通过 ({{ selectedImages.length }})
                </el-button>
                <el-button
                  v-if="canReview && selectedImages.length > 0"
                  type="danger"
                  size="small"
                  @click="batchReview('rejected')"
                >
                  批量拒绝 ({{ selectedImages.length }})
                </el-button>
                <el-button
                  v-if="canUpload"
                  type="primary"
                  @click="showUploadDialog = true"
                >
                  上传图像
                </el-button>
              </div>
            </div>
          </template>
          
          <el-table 
            :data="images" 
            style="width: 100%" 
            v-loading="imagesLoading"
            @selection-change="handleSelectionChange"
          >
            <el-table-column 
              v-if="canReview"
              type="selection" 
              width="55"
              :selectable="isImageSelectable"
            />
            <el-table-column prop="filename" label="文件名" width="200" />
            <el-table-column prop="width" label="宽度" width="80" />
            <el-table-column prop="height" label="高度" width="80" />
            <el-table-column label="标注进度" width="150">
              <template #default="{ row }">
                <div>
                  <el-tag :type="row.is_annotated ? 'success' : 'info'" size="small">
                    {{ row.annotation_count || 0 }} / {{ row.required_annotation_count || 1 }}
                  </el-tag>
                  <div style="font-size: 11px; color: #999; margin-top: 2px">
                    {{ row.is_annotated ? '已完成' : '未完成' }}
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="审核状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_reviewed ? 'success' : 'warning'" size="small">
                  {{ row.is_reviewed ? '已审核' : '待审核' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="300">
              <template #default="{ row }">
                <!-- 标注按钮：只对非管理员显示 -->
                <el-button
                  v-if="canAnnotate"
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
                <!-- 审核按钮：只对管理员显示，且图像已标注未审核 -->
                <el-button
                  v-if="canReview && row.is_annotated && !row.is_reviewed"
                  type="success"
                  size="small"
                  @click="openReviewDialog(row)"
                >
                  审核
                </el-button>
                <!-- 查看按钮：所有人都可以查看已标注的图像 -->
                <el-button
                  v-if="row.is_annotated"
                  type="warning"
                  size="small"
                  @click="viewAnnotations(row)"
                >
                  查看
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
              v-if="canAssignTask"
              type="primary"
              @click="openAssignDialog"
              style="width: 100%; margin-bottom: 10px"
            >
              <el-icon><User /></el-icon>
              分配任务
            </el-button>
            
            <el-button
              v-if="canAnnotate"
              type="success"
              @click="startAnnotating"
              style="width: 100%; margin-bottom: 10px"
            >
              <el-icon><Edit /></el-icon>
              开始标注
            </el-button>
            
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
    
    <!-- 任务分配对话框 -->
    <el-dialog
      v-model="showAssignDialog"
      title="分配任务"
      width="500px"
    >
      <el-form label-width="100px">
        <el-form-item label="当前分配">
          <div v-if="task?.assignees && task.assignees.length > 0">
            <el-tag
              v-for="assignee in task.assignees"
              :key="assignee.user_id"
              style="margin-right: 8px; margin-bottom: 4px"
              closable
              @close="removeAssignee(assignee.user_id)"
            >
              {{ assignee.full_name }} - 已完成 {{ assignee.completed_images }} 张
            </el-tag>
          </div>
          <span v-else style="color: #999;">未分配</span>
        </el-form-item>
        
        <el-form-item label="分配给">
          <el-select
            v-model="selectedAssignees"
            placeholder="请选择用户（可多选）"
            style="width: 100%"
            filterable
            multiple
            collapse-tags
            collapse-tags-tooltip
          >
            <el-option
              v-for="user in annotators"
              :key="user.id"
              :label="`${user.full_name} (${user.username}) - ${getRoleText(user.role)}`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="每张图片标注人数">
          <el-input-number
            v-model="requiredAnnotationsPerImage"
            :min="1"
            :max="selectedAssignees.length || 1"
            style="width: 100%"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px;">
            每张图片需要 {{ requiredAnnotationsPerImage }} 个人标注
          </div>
        </el-form-item>
        
        <el-form-item label="审核人员">
          <el-select
            v-model="selectedReviewer"
            placeholder="请选择审核人员（可选）"
            style="width: 100%"
            filterable
            clearable
          >
            <el-option
              v-for="user in reviewers"
              :key="user.id"
              :label="`${user.full_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleAssignTask"
          :loading="assigning"
          :disabled="!selectedAssignees || selectedAssignees.length === 0"
        >
          确定分配
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 编辑任务对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑任务"
      width="600px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="140px"
      >
        <el-form-item label="任务名称" prop="title">
          <el-input v-model="editForm.title" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="任务描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入任务描述"
          />
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-select v-model="editForm.priority" style="width: 100%">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option label="待分配" value="pending" />
            <el-option label="已分配" value="assigned" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
            <el-option label="已审核" value="reviewed" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="标注类型" prop="annotation_types">
          <el-select
            v-model="editForm.annotation_types"
            placeholder="选择标注类型（可多选）"
            multiple
            collapse-tags
            style="width: 100%"
          >
            <el-option label="分类" value="classification" />
            <el-option label="回归" value="regression" />
            <el-option label="边界框" value="bbox" />
            <el-option label="多边形" value="polygon" />
            <el-option label="关键点" value="keypoint" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="每张图片标注人数">
          <el-input-number
            v-model="editForm.required_annotations_per_image"
            :min="1"
            :max="10"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="标签列表">
          <div>
            <el-tag
              v-for="(label, index) in editForm.labels"
              :key="index"
              closable
              @close="removeLabelFromEdit(index)"
              style="margin-right: 8px; margin-bottom: 8px"
            >
              {{ label }}
            </el-tag>
            <el-input
              v-model="newLabel"
              placeholder="输入新标签按回车添加"
              style="width: 200px"
              @keyup.enter="addLabelToEdit"
            />
          </div>
        </el-form-item>
        
        <el-form-item label="标注说明">
          <el-input
            v-model="editForm.instructions"
            type="textarea"
            :rows="4"
            placeholder="请输入标注说明"
          />
        </el-form-item>
        
        <el-form-item label="截止日期">
          <el-date-picker
            v-model="editForm.deadline"
            type="datetime"
            placeholder="选择截止日期"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="handleUpdateTask"
          :loading="updating"
        >
          保存修改
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 审核对话框 -->
    <el-dialog
      v-model="showReviewDialog"
      title="审核标注"
      width="800px"
    >
      <div v-if="currentImage">
        <h4>图像信息</h4>
        <p>文件名：{{ currentImage.filename }}</p>
        <p>标注数量：{{ currentImageAnnotations.length }} 个</p>
        
        <el-divider />
        
        <h4>标注详情</h4>
        <el-table :data="currentImageAnnotations" style="width: 100%; margin-bottom: 20px">
          <el-table-column label="标注类型" width="100">
            <template #default="{ row }">
              {{ getAnnotationTypeLabel(row.annotation_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="label" label="标签" width="120" />
          <el-table-column label="标注数据">
            <template #default="{ row }">
              <pre style="font-size: 12px; margin: 0">{{ JSON.stringify(row.data, null, 2) }}</pre>
            </template>
          </el-table-column>
          <el-table-column label="标注人" width="100">
            <template #default="{ row }">
              {{ getUserName(row.annotator_id) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <el-form label-width="100px">
          <el-form-item label="审核意见">
            <el-input
              v-model="reviewNotes"
              type="textarea"
              :rows="3"
              placeholder="请输入审核意见（可选）"
            />
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button
          type="danger"
          @click="handleReview('rejected')"
          :loading="reviewing"
        >
          拒绝
        </el-button>
        <el-button
          type="success"
          @click="handleReview('approved')"
          :loading="reviewing"
        >
          通过
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 查看标注对话框 -->
    <el-dialog
      v-model="showViewDialog"
      title="查看标注"
      width="900px"
    >
      <div v-if="currentImage">
        <el-row :gutter="20">
          <el-col :span="14">
            <div style="text-align: center; background: #f5f5f5; padding: 20px; border-radius: 4px;">
              <img :src="previewImageUrl" style="max-width: 100%; max-height: 500px;" />
            </div>
          </el-col>
          <el-col :span="10">
            <h4>标注列表</h4>
            <el-table :data="currentImageAnnotations" style="width: 100%" max-height="500">
              <el-table-column label="类型" width="80">
                <template #default="{ row }">
                  {{ getAnnotationTypeLabel(row.annotation_type) }}
                </template>
              </el-table-column>
              <el-table-column prop="label" label="标签" />
              <el-table-column label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="getStatusTagType(row.status)" size="small">
                    {{ getStatusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
            
            <div v-if="currentImage.is_reviewed" style="margin-top: 20px;">
              <el-alert
                title="该图像已通过审核"
                type="success"
                :closable="false"
              />
            </div>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
    
    <!-- 图像预览对话框 -->
    <el-dialog
      v-model="showPreviewDialog"
      title="图像预览"
      width="80%"
    >
      <div style="text-align: center;">
        <img :src="previewImageUrl" style="max-width: 100%; max-height: 70vh;" />
      </div>
    </el-dialog>
    
    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传图像"
      width="600px"
    >
      <el-upload
        ref="uploadRef"
        name="files"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :data="uploadData"
        :file-list="fileList"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        accept="image/*"
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const authStore = useAuthStore()

const taskId = route.params.id
const task = ref(null)
const images = ref([])
const imagesLoading = ref(false)
const showUploadDialog = ref(false)
const showPreviewDialog = ref(false)
const showAssignDialog = ref(false)
const showEditDialog = ref(false)
const showReviewDialog = ref(false)
const showViewDialog = ref(false)
const previewImageUrl = ref('')
const fileList = ref([])
const users = ref([])
const annotators = ref([])
const reviewers = ref([])
const selectedAssignees = ref([])
const selectedReviewer = ref(null)
const requiredAnnotationsPerImage = ref(1)
const assigning = ref(false)
const updating = ref(false)
const reviewing = ref(false)
const newLabel = ref('')
const editFormRef = ref()
const currentImage = ref(null)
const currentImageAnnotations = ref([])
const reviewNotes = ref('')
const selectedImages = ref([])  // 选中的图像列表

const editForm = reactive({
  title: '',
  description: '',
  status: '',
  priority: '',
  annotation_types: [],
  labels: [],
  instructions: '',
  deadline: null,
  required_annotations_per_image: 1
})

const editRules = {
  title: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  annotation_types: [{
    required: true,
    message: '请至少选择一种标注类型',
    trigger: 'change',
    type: 'array',
    min: 1
  }]
}

const uploadUrl = computed(() => {
  // 使用完整的 URL，因为 el-upload 不会自动添加 baseURL
  return `${window.location.origin}/api/files/upload`
})

const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${authStore.token}`
}))

const uploadData = computed(() => ({
  task_id: parseInt(taskId)
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

const canAssignTask = computed(() => {
  return authStore.hasRole(['admin', 'engineer'])
})

const canEditTask = computed(() => {
  return authStore.hasRole(['admin'])
})

const canReview = computed(() => {
  // 只有管理员可以审核
  return authStore.hasRole(['admin'])
})

const canAnnotate = computed(() => {
  // 检查是否有权限标注
  if (!task.value) return false
  
  // 管理员不能参与标注
  if (authStore.hasRole(['admin'])) return false
  
  // 工程师可以标注
  if (authStore.hasRole(['engineer'])) return true
  
  // 检查是否在分配列表中（标注员和审核员）
  if (task.value.assignees && task.value.assignees.length > 0) {
    return task.value.assignees.some(a => a.user_id === authStore.user?.id)
  }
  
  // 检查旧的单一分配
  return task.value.assignee_id === authStore.user?.id
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

const getAnnotationTypes = (task) => {
  if (!task) return []
  
  // 优先使用新的 annotation_types 字段
  if (task.annotation_types && task.annotation_types.length > 0) {
    return task.annotation_types
  }
  
  // 兼容旧的 annotation_type 字段
  return task.annotation_type ? [task.annotation_type] : []
}

const getAnnotationTypeLabel = (type) => {
  const typeMap = {
    'bbox': '边界框',
    'polygon': '多边形',
    'keypoint': '关键点',
    'classification': '分类',
    'regression': '回归'
  }
  return typeMap[type] || type
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

const getRoleText = (role) => {
  const roleMap = {
    admin: '管理员',
    engineer: '算法工程师',
    annotator: '标注员',
    reviewer: '审核员'
  }
  return roleMap[role] || role
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

const getUserName = (userId) => {
  if (!userId) return '未知用户'
  const user = users.value.find(u => u.id === userId)
  return user ? `${user.full_name} (${user.username})` : `用户 ID: ${userId}`
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

const fetchUsers = async () => {
  try {
    const response = await api.get('/users')
    users.value = response.data
    
    // 筛选出标注员
    annotators.value = response.data.filter(user => 
      user.role === 'annotator' || user.role === 'admin'
    )
    
    // 筛选出审核员
    reviewers.value = response.data.filter(user => 
      user.role === 'reviewer' || user.role === 'admin'
    )
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

const openAssignDialog = () => {
  // 预设当前的分配值
  if (task.value?.assignees && task.value.assignees.length > 0) {
    selectedAssignees.value = task.value.assignees.map(a => a.user_id)
  } else if (task.value?.assignee_id) {
    selectedAssignees.value = [task.value.assignee_id]
  } else {
    selectedAssignees.value = []
  }
  
  selectedReviewer.value = task.value?.reviewer_id || null
  requiredAnnotationsPerImage.value = task.value?.required_annotations_per_image || 1
  showAssignDialog.value = true
}

const removeAssignee = async (userId) => {
  // 这里可以实现移除分配的逻辑
  ElMessage.info('移除分配功能开发中')
}

const handleAssignTask = async () => {
  if (!selectedAssignees.value || selectedAssignees.value.length === 0) {
    ElMessage.warning('请至少选择一个用户')
    return
  }
  
  assigning.value = true
  try {
    // 批量分配任务
    await api.post(`/tasks/${taskId}/assign-multiple`, selectedAssignees.value)
    
    // 更新任务配置
    await api.put(`/tasks/${taskId}`, {
      required_annotations_per_image: requiredAnnotationsPerImage.value,
      reviewer_id: selectedReviewer.value
    })
    
    ElMessage.success(`任务已分配给 ${selectedAssignees.value.length} 个用户`)
    showAssignDialog.value = false
    
    // 刷新任务信息
    await fetchTask()
  } catch (error) {
    console.error('任务分配失败:', error)
    ElMessage.error(error.response?.data?.detail || '任务分配失败')
  } finally {
    assigning.value = false
  }
}

const openEditDialog = () => {
  if (!task.value) return
  
  // 填充编辑表单
  Object.assign(editForm, {
    title: task.value.title || '',
    description: task.value.description || '',
    status: task.value.status || 'pending',
    priority: task.value.priority || 'medium',
    annotation_types: task.value.annotation_types && task.value.annotation_types.length > 0 
      ? task.value.annotation_types 
      : (task.value.annotation_type ? [task.value.annotation_type] : []),
    labels: task.value.labels ? [...task.value.labels] : [],
    instructions: task.value.instructions || '',
    deadline: task.value.deadline ? new Date(task.value.deadline) : null,
    required_annotations_per_image: task.value.required_annotations_per_image || 1
  })
  
  showEditDialog.value = true
}

const addLabelToEdit = () => {
  if (newLabel.value && !editForm.labels.includes(newLabel.value)) {
    editForm.labels.push(newLabel.value)
    newLabel.value = ''
  }
}

const removeLabelFromEdit = (index) => {
  editForm.labels.splice(index, 1)
}

const handleUpdateTask = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    updating.value = true
    
    // 构建更新数据
    const updateData = {
      ...editForm,
      annotation_type: editForm.annotation_types[0] || 'bbox' // 兼容旧字段
    }
    
    await api.put(`/tasks/${taskId}`, updateData)
    
    ElMessage.success('任务更新成功')
    showEditDialog.value = false
    
    // 刷新任务信息
    await fetchTask()
  } catch (error) {
    console.error('更新任务失败:', error)
    if (error.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else {
      ElMessage.error('更新任务失败')
    }
  } finally {
    updating.value = false
  }
}

const startAnnotating = async () => {
  try {
    // 获取下一张未标注的图像
    const response = await api.get(`/files/task/${taskId}/next-unannotated`)
    
    if (response.data) {
      // 跳转到标注页面
      window.open(`/annotate/${taskId}/${response.data.id}`, '_blank')
    } else {
      ElMessage.info('所有图像都已标注完成')
    }
  } catch (error) {
    console.error('获取下一张图像失败:', error)
    ElMessage.error('获取下一张图像失败')
  }
}

const startAnnotate = (imageId) => {
  window.open(`/annotate/${taskId}/${imageId}`, '_blank')
}

const previewImage = async (image) => {
  try {
    const response = await api.get(`/files/${image.id}`)
    // 构建完整的图像 URL
    const imagePath = response.data.file_path
    console.log('图像路径:', imagePath)
    
    // 如果路径已经是完整URL，直接使用；否则添加后端基础URL
    if (imagePath.startsWith('http')) {
      previewImageUrl.value = imagePath
    } else {
      // 使用当前页面的协议和主机，端口改为8000（后端端口）
      const protocol = window.location.protocol
      const hostname = window.location.hostname
      previewImageUrl.value = `${protocol}//${hostname}:8000${imagePath}`
    }
    
    console.log('完整图像URL:', previewImageUrl.value)
    showPreviewDialog.value = true
  } catch (error) {
    console.error('预览图像失败:', error)
    ElMessage.error('预览图像失败')
  }
}

const openReviewDialog = async (image) => {
  try {
    currentImage.value = image
    reviewNotes.value = ''
    
    // 获取图像的所有标注
    const response = await api.get(`/annotations/image/${image.id}`)
    currentImageAnnotations.value = response.data.annotations || []
    
    showReviewDialog.value = true
  } catch (error) {
    console.error('获取标注失败:', error)
    ElMessage.error('获取标注失败')
  }
}

const viewAnnotations = async (image) => {
  try {
    currentImage.value = image
    
    // 获取图像的所有标注
    const response = await api.get(`/annotations/image/${image.id}`)
    currentImageAnnotations.value = response.data.annotations || []
    
    // 获取图像URL但不显示预览弹窗
    const imageResponse = await api.get(`/files/${image.id}`)
    const imagePath = imageResponse.data.file_path
    
    // 如果路径已经是完整URL，直接使用；否则添加后端基础URL
    if (imagePath.startsWith('http')) {
      previewImageUrl.value = imagePath
    } else {
      const protocol = window.location.protocol
      const hostname = window.location.hostname
      previewImageUrl.value = `${protocol}//${hostname}:8000${imagePath}`
    }
    
    // 只显示查看标注对话框
    showViewDialog.value = true
  } catch (error) {
    console.error('获取标注失败:', error)
    ElMessage.error('获取标注失败')
  }
}

const handleReview = async (reviewStatus) => {
  if (!currentImage.value) return
  
  reviewing.value = true
  try {
    // 批量审核图像的所有标注
    await api.post(`/annotations/image/${currentImage.value.id}/review`, null, {
      params: {
        status: reviewStatus,
        review_notes: reviewNotes.value || undefined
      }
    })
    
    ElMessage.success(reviewStatus === 'approved' ? '标注已通过审核' : '标注已拒绝')
    showReviewDialog.value = false
    
    // 刷新图像列表
    await fetchImages()
    await fetchTask()
  } catch (error) {
    console.error('审核失败:', error)
    ElMessage.error(error.response?.data?.detail || '审核失败')
  } finally {
    reviewing.value = false
  }
}

const getStatusTagType = (status) => {
  const typeMap = {
    'draft': 'info',
    'submitted': 'warning',
    'approved': 'success',
    'rejected': 'danger'
  }
  return typeMap[status] || 'info'
}

const handleSelectionChange = (selection) => {
  selectedImages.value = selection
}

const isImageSelectable = (row) => {
  // 只有已标注且未审核的图像才能被选中进行批量审核
  return row.is_annotated && !row.is_reviewed
}

const batchReview = async (reviewStatus) => {
  if (selectedImages.value.length === 0) {
    ElMessage.warning('请选择要审核的图像')
    return
  }
  
  const statusText = reviewStatus === 'approved' ? '通过' : '拒绝'
  
  try {
    const result = await ElMessageBox.confirm(
      `确定要批量${statusText} ${selectedImages.value.length} 张图像的标注吗？`,
      '批量审核确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    if (result !== 'confirm') return
    
    reviewing.value = true
    
    // 批量调用审核API
    const promises = selectedImages.value.map(image => 
      api.post(`/annotations/image/${image.id}/review`, null, {
        params: {
          status: reviewStatus
        }
      })
    )
    
    await Promise.all(promises)
    
    ElMessage.success(`已成功${statusText} ${selectedImages.value.length} 张图像的标注`)
    
    // 清空选择
    selectedImages.value = []
    
    // 刷新图像列表和任务信息
    await fetchImages()
    await fetchTask()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量审核失败:', error)
      ElMessage.error(error.response?.data?.detail || '批量审核失败')
    }
  } finally {
    reviewing.value = false
  }
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
  
  // 如果是管理员或工程师，获取用户列表
  if (authStore.hasRole(['admin', 'engineer'])) {
    fetchUsers()
  }
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
