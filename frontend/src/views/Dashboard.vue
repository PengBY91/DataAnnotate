<template>
  <div class="dashboard">
    <h1>仪表盘</h1>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.total_tasks }}</div>
            <div class="stat-label">总任务数</div>
          </div>
          <el-icon class="stat-icon"><List /></el-icon>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.pending_tasks }}</div>
            <div class="stat-label">待处理</div>
          </div>
          <el-icon class="stat-icon"><Clock /></el-icon>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.in_progress_tasks }}</div>
            <div class="stat-label">进行中</div>
          </div>
          <el-icon class="stat-icon"><Loading /></el-icon>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-number">{{ stats.completed_tasks }}</div>
            <div class="stat-label">已完成</div>
          </div>
          <el-icon class="stat-icon"><Check /></el-icon>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 最近任务 -->
    <el-card class="recent-tasks">
      <template #header>
        <div class="card-header">
          <span>最近任务</span>
          <el-button type="primary" @click="$router.push('/tasks')">
            查看全部
          </el-button>
        </div>
      </template>
      
      <el-table :data="recentTasks" style="width: 100%">
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
        <el-table-column prop="created_at" label="创建时间" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="$router.push(`/tasks/${row.id}`)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/utils/api'

const stats = ref({
  total_tasks: 0,
  pending_tasks: 0,
  in_progress_tasks: 0,
  completed_tasks: 0
})

const recentTasks = ref([])

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

const fetchStats = async () => {
  try {
    const response = await api.get('/tasks/stats')
    stats.value = response.data
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

const fetchRecentTasks = async () => {
  try {
    const response = await api.get('/tasks?limit=5')
    recentTasks.value = response.data
  } catch (error) {
    console.error('获取最近任务失败:', error)
  }
}

onMounted(() => {
  fetchStats()
  fetchRecentTasks()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.stat-icon {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 40px;
  color: #e6f7ff;
}

.recent-tasks {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
