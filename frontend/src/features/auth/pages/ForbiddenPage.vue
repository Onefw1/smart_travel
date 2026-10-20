<script setup lang="ts">
import { homeForRole } from '../../../app/router'
import { useSessionStore } from '../session-store'
const session = useSessionStore()
</script>

<template>
  <section class="account-card">
    <span class="eyebrow dark">403 · 访问受限</span>
    <h1>当前账号无权访问此页面</h1>
    <p>请返回你的账号页面继续使用。</p>
    <RouterLink class="primary-button" :to="session.user ? homeForRole(session.user.role) : '/login'">返回{{ session.user ? '账号页面' : '登录' }}</RouterLink>
  </section>
</template>
