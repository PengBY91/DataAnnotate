<template>
  <div class="profile">
    <h1>个人资料</h1>
    
    <el-card>
      <el-form
        ref="profileFormRef"
        :model="profileForm"
        :rules="profileRules"
        label-width="100px"
        @submit.prevent="handleUpdate"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="profileForm.username" disabled />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="profileForm.email" />
        </el-form-item>
        
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="profileForm.full_name" />
        </el-form-item>
        
        <el-form-item label="角色">
          <el-tag :type="getRoleType(profileForm.role)">
            {{ getRoleText(profileForm.role) }}
          </el-tag>
        </el-form-item>
        
        <el-form-item label="创建时间">
          <span>{{ formatDate(profileForm.created_at) }}</span>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleUpdate" :loading="updating">
            更新资料
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()

const profileFormRef = ref()
const updating = ref(false)

const profileForm = reactive({
  username: '',
  email: '',
  full_name: '',
  role: '',
  created_at: ''
})

const profileRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  full_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }]
}

const getRoleType = (role) => {
  const roleMap = {
    admin: 'danger',
    engineer: 'warning',
    reviewer: 'warning',
    annotator: 'info'
  }
  return roleMap[role] || 'info'
}

const getRoleText = (role) => {
  const roleMap = {
    admin: '管理员',
    engineer: '算法工程师',
    reviewer: '审核员',
    annotator: '标注员'
  }
  return roleMap[role] || role
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleString('zh-CN')
}

const loadProfile = () => {
  if (authStore.user) {
    Object.assign(profileForm, {
      username: authStore.user.username,
      email: authStore.user.email,
      full_name: authStore.user.full_name,
      role: authStore.user.role,
      created_at: authStore.user.created_at
    })
  }
}

const handleUpdate = async () => {
  if (!profileFormRef.value) return
  
  try {
    await profileFormRef.value.validate()
    updating.value = true
    
    await api.put(`/users/${authStore.user.id}`, {
      email: profileForm.email,
      full_name: profileForm.full_name
    })
    
    ElMessage.success('资料更新成功')
    await authStore.fetchUser()
  } catch (error) {
    console.error('更新资料失败:', error)
  } finally {
    updating.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile {
  padding: 20px;
  max-width: 600px;
}
</style>
