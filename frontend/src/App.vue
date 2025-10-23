<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // 初始化时检查用户登录状态
  authStore.checkAuth()
})
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
}
</style>
