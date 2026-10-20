<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '../session-store'

const session = useSessionStore()
const router = useRouter()
const pending = ref(false)
const message = ref('')

async function logout() {
  if (pending.value) return
  pending.value = true
  message.value = ''
  try {
    await session.logout()
    await router.replace('/login')
  } catch (error) {
    message.value = error instanceof Error ? error.message : '退出失败，请重试'
  } finally { pending.value = false }
}
</script>

<template>
  <section class="account-card" aria-labelledby="account-title">
    <span class="eyebrow dark">{{ session.user?.role === 'admin' ? '管理员入口' : '我的账号' }}</span>
    <span class="status-pill">已登录</span>
    <h1 id="account-title">你好，{{ session.user?.username }}</h1>
    <p>{{ session.user?.role === 'admin' ? '管理员身份验证成功。景点、预约及评价管理将在后续功能中提供。' : '你的账号已准备就绪。景点发现、行程规划等功能将在后续开放。' }}</p>
    <dl class="account-details">
      <div><dt>当前身份</dt><dd>{{ session.user?.role === 'admin' ? '管理员' : '普通用户' }}</dd></div>
      <div><dt>会话到期时间</dt><dd>{{ session.expiresAt ? new Date(session.expiresAt).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', hour12: false }) : '—' }}（北京时间）</dd></div>
    </dl>
    <p v-if="message" role="alert" class="notice error">{{ message }}</p>
    <button class="primary-button" :disabled="pending" @click="logout">{{ pending ? '正在退出…' : '退出登录' }}</button>
  </section>
</template>
