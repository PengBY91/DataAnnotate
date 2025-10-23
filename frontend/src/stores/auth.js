import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  
  const isAuthenticated = computed(() => !!token.value)
  
  const hasRole = (roles) => {
    if (!user.value) return false
    return roles.includes(user.value.role)
  }
  
  const login = async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials)
      const { access_token } = response.data
      
      token.value = access_token
      localStorage.setItem('token', access_token)
      
      // 获取用户信息
      await fetchUser()
      
      return response.data
    } catch (error) {
      throw error
    }
  }
  
  const logout = () => {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }
  
  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
      return response.data
    } catch (error) {
      console.error('获取用户信息失败:', error)
      logout()
      throw error
    }
  }
  
  const checkAuth = async () => {
    if (token.value) {
      try {
        await fetchUser()
      } catch (error) {
        logout()
      }
    }
  }
  
  return {
    user,
    token,
    isAuthenticated,
    hasRole,
    login,
    logout,
    fetchUser,
    checkAuth
  }
})
