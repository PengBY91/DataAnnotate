import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/annotate/:taskId/:imageId',
    name: 'Annotate',
    component: () => import('@/views/Annotate.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: '/tasks',
        name: 'Tasks',
        component: () => import('@/views/Tasks.vue')
      },
      {
        path: '/tasks/:id',
        name: 'TaskDetail',
        component: () => import('@/views/TaskDetail.vue')
      },
      {
        path: '/users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { requiresRole: ['admin'] }
      },
      {
        path: '/profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue')
      },
      {
        path: '/quality',
        name: 'QualityControl',
        component: () => import('@/views/QualityControl.vue'),
        meta: { requiresRole: ['admin', 'reviewer'] }
      },
      {
        path: '/export',
        name: 'Export',
        component: () => import('@/views/Export.vue'),
        meta: { requiresRole: ['admin', 'engineer', 'reviewer'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  console.log('路由守卫检查:', {
    to: to.path,
    requiresAuth: to.meta.requiresAuth,
    requiresRole: to.meta.requiresRole,
    hasToken: !!authStore.token,
    hasUser: !!authStore.user,
    userRole: authStore.user?.role
  })
  
  // 如果路由需要认证
  if (to.meta.requiresAuth) {
    // 检查是否有token
    if (!authStore.token) {
      console.log('没有token，跳转到登录页')
      next('/login')
      return
    }
    
    // 检查用户信息是否已加载
    if (!authStore.user) {
      try {
        console.log('获取用户信息...')
        await authStore.fetchUser()
        console.log('用户信息获取成功:', authStore.user)
      } catch (error) {
        console.error('获取用户信息失败:', error)
        authStore.logout()
        next('/login')
        return
      }
    }
    
    // 检查角色权限
    if (to.meta.requiresRole && !authStore.hasRole(to.meta.requiresRole)) {
      console.log('权限不足，跳转到首页')
      next('/')
      return
    }
  }
  
  console.log('路由守卫通过，继续导航')
  next()
})

export default router
