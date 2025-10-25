<template>
  <div class="tasks">
    <div class="page-header">
      <h1>任务管理</h1>
      <el-button
        v-if="authStore.hasRole(['admin', 'engineer'])"
        type="primary"
        @click="showCreateDialog = true"
      >
        创建任务
      </el-button>
    </div>
    
    <!-- 筛选器 -->
    <el-card class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="选择状态" clearable>
            <el-option label="待分配" value="pending" />
            <el-option label="已分配" value="assigned" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" placeholder="选择优先级" clearable>
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="fetchTasks">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 任务列表 -->
    <el-card class="tasks-card">
      <el-table :data="tasks" style="width: 100%" v-loading="loading">
        <el-table-column prop="title" label="任务名称" />
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="annotation_type" label="标注类型" />
        <el-table-column prop="total_images" label="图像数量" />
        <el-table-column prop="annotated_images" label="已标注" />
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作" width="250">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="$router.push(`/tasks/${row.id}`)"
            >
              查看
            </el-button>
            <el-button
              v-if="canStartTask(row)"
              type="success"
              size="small"
              @click="startTask(row.id)"
            >
              开始
            </el-button>
            <el-button
              v-if="canCompleteTask(row)"
              type="warning"
              size="small"
              @click="completeTask(row.id)"
            >
              完成
            </el-button>
            <el-button
              v-if="canDeleteTask"
              type="danger"
              size="small"
              @click="deleteTask(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchTasks"
        @current-change="fetchTasks"
        style="margin-top: 20px; text-align: right"
      />
    </el-card>
    
    <!-- 创建任务对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建任务"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="任务名称" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入任务名称" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            placeholder="请输入任务描述"
          />
        </el-form-item>
        
        <el-form-item label="标注类型" prop="annotation_types">
          <el-select
            v-model="createForm.annotation_types"
            placeholder="选择标注类型（可多选）"
            multiple
            collapse-tags
          >
            <el-option label="分类" value="classification" />
            <el-option label="回归" value="regression" />
            <el-option label="边界框" value="bbox" />
            <el-option label="排序" value="ranking" />
          </el-select>
          <div style="color: #999; font-size: 12px; margin-top: 4px;">
            可同时选择多种标注类型
          </div>
        </el-form-item>
        
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="createForm.priority" placeholder="选择优先级">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        
        <!-- 排序类型配置 -->
        <el-form-item 
          v-if="createForm.annotation_types && createForm.annotation_types.includes('ranking')"
          label="排序最大范围"
          prop="ranking_max"
        >
          <el-input-number
            v-model="createForm.ranking_max"
            :min="2"
            :max="20"
            placeholder="最大范围"
            style="width: 100%"
            controls-position="right"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px;">
            设置排序的最大范围，例如设为3，则标注时可以输入1、2、3的排列（如"213"）
          </div>
        </el-form-item>
        
        <!-- 非排序类型的标签配置 -->
        <el-form-item 
          v-if="!createForm.annotation_types || !createForm.annotation_types.includes('ranking') || createForm.annotation_types.length > 1"
          label="标签"
        >
          <el-input
            v-model="labelInput"
            placeholder="输入标签后按回车添加"
            @keyup.enter="addLabel"
          />
          <div class="labels-display">
            <el-tag
              v-for="(label, index) in createForm.labels"
              :key="index"
              closable
              @close="removeLabel(index)"
              style="margin-right: 8px; margin-top: 8px"
            >
              {{ label }}
            </el-tag>
          </div>
          <div v-if="createForm.annotation_types && createForm.annotation_types.includes('ranking')" style="color: #999; font-size: 12px; margin-top: 4px;">
            排序类型使用"排序最大范围"，其他类型使用标签列表
          </div>
        </el-form-item>
        
        <el-form-item label="说明">
          <el-input
            v-model="createForm.instructions"
            type="textarea"
            placeholder="请输入标注说明"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreateTask" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import '@/styles/views/Tasks.css'

const authStore = useAuthStore()

const tasks = ref([])
const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)

const filters = reactive({
  status: '',
  priority: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const createFormRef = ref()
const createForm = reactive({
  title: '',
  description: '',
  annotation_type: 'bbox',  // 兼容旧字段，默认值
  annotation_types: [],  // 新字段：多选标注类型
  priority: 'medium',
  labels: [],
  instructions: '',
  ranking_max: 3  // 排序类型的最大范围，默认3
})

const labelInput = ref('')

const createRules = {
  title: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  annotation_types: [{ 
    required: true, 
    message: '请至少选择一种标注类型', 
    trigger: 'change',
    type: 'array',
    min: 1
  }]
}

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

const canStartTask = (task) => {
  if (!authStore.user?.id || task.status !== 'assigned') return false
  
  // 检查旧的分配方式
  if (task.assignee_id === authStore.user.id) return true
  
  // 检查新的分配方式
  if (task.assignees && task.assignees.length > 0) {
    return task.assignees.some(a => a.user_id === authStore.user.id)
  }
  
  return false
}

const canCompleteTask = (task) => {
  if (!authStore.user?.id || task.status !== 'in_progress') return false
  
  // 检查旧的分配方式
  if (task.assignee_id === authStore.user.id) return true
  
  // 检查新的分配方式
  if (task.assignees && task.assignees.length > 0) {
    return task.assignees.some(a => a.user_id === authStore.user.id)
  }
  
  return false
}

const canDeleteTask = computed(() => {
  return authStore.hasRole(['admin'])
})

const fetchTasks = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size
    }
    
    // 只添加非空的过滤参数
    if (filters.status) {
      params.status = filters.status
    }
    if (filters.priority) {
      params.priority = filters.priority
    }
    
    const response = await api.get('/tasks', { params })
    tasks.value = response.data
  } catch (error) {
    console.error('获取任务列表失败:', error)
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  Object.assign(filters, {
    status: '',
    priority: ''
  })
  fetchTasks()
}

const startTask = async (taskId) => {
  try {
    await api.post(`/tasks/${taskId}/start`)
    ElMessage.success('任务已开始')
    fetchTasks()
  } catch (error) {
    console.error('开始任务失败:', error)
  }
}

const completeTask = async (taskId) => {
  try {
    await api.post(`/tasks/${taskId}/complete`)
    ElMessage.success('任务已完成')
    fetchTasks()
  } catch (error) {
    console.error('完成任务失败:', error)
  }
}

const deleteTask = async (task) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除任务"${task.title}"吗？这将同时删除任务下的所有图像和标注数据，此操作不可恢复！`,
      '删除任务',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    await api.delete(`/tasks/${task.id}`)
    ElMessage.success('任务删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除任务失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除任务失败')
    }
  }
}

const addLabel = () => {
  if (labelInput.value.trim()) {
    createForm.labels.push(labelInput.value.trim())
    labelInput.value = ''
  }
}

const removeLabel = (index) => {
  createForm.labels.splice(index, 1)
}

const resetCreateForm = () => {
  Object.assign(createForm, {
    title: '',
    description: '',
    annotation_type: 'bbox',
    annotation_types: [],
    priority: 'medium',
    labels: [],
    instructions: ''
  })
  labelInput.value = ''
}

const handleCreateTask = async () => {
  if (!createFormRef.value) return
  
  try {
    await createFormRef.value.validate()
    creating.value = true
    
    // 确保 annotation_type 有默认值（向后兼容）
    const taskData = {
      ...createForm,
      annotation_type: createForm.annotation_types[0] || 'bbox'
    }
    
    await api.post('/tasks', taskData)
    ElMessage.success('任务创建成功')
    showCreateDialog.value = false
    fetchTasks()
  } catch (error) {
    console.error('创建任务失败:', error)
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  fetchTasks()
})
</script>
