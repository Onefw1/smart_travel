<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError } from '../../../shared/api/client'
import { authApi } from '../api'
import { useSessionStore } from '../session-store'
import { safeDestination } from '../../../app/router'
import { validateCredentials } from '../validation'

const props = defineProps<{ mode: 'login' | 'register' }>()
const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const registering = computed(() => props.mode === 'register')
const form = reactive({ username: typeof route.query.username === 'string' ? route.query.username : '', password: '' })
const errors = ref<Record<string, string>>({})
const message = ref('')
const pending = ref(false)
const showPassword = ref(false)
const confirmPassword = ref('')
const showConfirmPassword = ref(false)

async function submit() {
  if (pending.value) return
  errors.value = validateCredentials(form)
  if (registering.value) {
    if (!confirmPassword.value) {
      errors.value.confirm_password = '请再次输入密码'
    } else if (confirmPassword.value !== form.password) {
      errors.value.confirm_password = '两次输入的密码不一致'
    }
  }
  message.value = ''
  if (Object.keys(errors.value).length) return
  pending.value = true
  try {
    if (registering.value) {
      const user = await authApi.register({ ...form })
      form.password = ''
      confirmPassword.value = ''
      await router.replace({ path: '/login', query: { registered: '1', username: user.username } })
    } else {
      await session.login({ ...form })
      form.password = ''
      await router.replace(safeDestination(route.query.redirect, session.user!.role))
    }
  } catch (error) {
    message.value = error instanceof Error ? error.message : '请求失败，请稍后重试'
    if (error instanceof ApiError) {
      for (const detail of error.details) errors.value[detail.field] = detail.message
    }
  } finally {
    pending.value = false
  }
}

async function retrySession() {
  pending.value = true
  message.value = ''
  try {
    await session.restore()
    if (session.user) await router.replace(safeDestination(null, session.user.role))
  } catch (error) {
    message.value = error instanceof Error ? error.message : '暂时无法恢复登录状态'
  } finally { pending.value = false }
}
</script>

<template>
  <section class="auth-layout" aria-labelledby="auth-title">
    <aside class="journey-panel">
      <span class="eyebrow">发现京城的另一面</span>
      <h1>让每一次出发，<br />都合你心意。</h1>
      <p>从红墙古韵到胡同烟火，<br />你的北京之旅，从这里开始。</p>
      <div class="city-art" aria-hidden="true">
        <div class="sun"></div>
        <svg viewBox="0 0 500 220" fill="none">
          <path d="M0 195H500M18 165H98V195H18V165ZM402 155H478V195H402V155Z" stroke="currentColor" />
          <path d="M98 195V136H402V195M115 136L148 114H352L385 136H115ZM143 114V91H357V114M126 91C163 88 169 71 177 61H323C331 71 337 88 374 91H126Z" fill="currentColor" fill-opacity=".28" stroke="currentColor" stroke-width="2" />
          <path d="M176 61V52H324V61M169 52C198 48 207 33 213 26H287C293 33 302 48 331 52H169ZM250 26V12M180 195V145M218 195V145M282 195V145M320 195V145M240 195V164C240 150 260 150 260 164V195" stroke="currentColor" stroke-width="3" />
          <path d="M38 165L57 145L78 165M424 155L440 136L457 155" stroke="currentColor" stroke-width="2" />
        </svg>
      </div>
      <span class="journey-caption">BEIJING · 39°54′ N, 116°24′ E</span>
    </aside>

    <div class="auth-form-panel">
      <span class="eyebrow dark">{{ registering ? '开启新的旅程' : '很高兴，再次见到你' }}</span>
      <h2 id="auth-title">{{ registering ? '创建你的账号' : '登录智游北京' }}</h2>
      <p class="form-intro">{{ registering ? '设置用户名和密码，再次输入密码以确认。' : '登录账号，为下一段京城时光做好准备。' }}</p>

      <div v-if="!registering && route.query.registered === '1'" role="status" class="notice success">注册成功，请使用新账号登录。</div>
      <div v-if="route.query.expired === '1'" role="status" class="notice">登录状态已失效，请重新登录。</div>
      <div v-if="session.restoreError" class="notice" role="alert">
        {{ session.restoreError }}
        <button type="button" class="text-button" :disabled="pending" @click="retrySession">重试恢复登录</button>
      </div>

      <form novalidate :aria-busy="pending" @submit.prevent="submit">
        <div class="field">
          <label for="username">用户名</label>
          <input id="username" v-model="form.username" name="username" autocomplete="username" placeholder="请输入用户名" :disabled="pending" :aria-invalid="!!errors.username" :aria-describedby="errors.username ? 'username-error' : 'username-hint'" />
          <p v-if="errors.username" id="username-error" class="field-error" role="alert">{{ errors.username }}</p>
          <p v-else id="username-hint" class="field-hint">3～20 个中文、英文字母、数字或下划线</p>
        </div>
        <div class="field">
          <label for="password">密码</label>
          <div class="password-control">
            <input id="password" v-model="form.password" name="password" :type="showPassword ? 'text' : 'password'" :autocomplete="registering ? 'new-password' : 'current-password'" placeholder="请输入密码" :disabled="pending" :aria-invalid="!!errors.password" :aria-describedby="errors.password ? 'password-error' : 'password-hint'" />
            <button type="button" :disabled="pending" :aria-label="showPassword ? '隐藏密码' : '显示密码'" :aria-pressed="showPassword" @click="showPassword = !showPassword">{{ showPassword ? '隐藏' : '显示' }}</button>
          </div>
          <p v-if="errors.password" id="password-error" class="field-error" role="alert">{{ errors.password }}</p>
          <p v-else id="password-hint" class="field-hint">8～64 个字符，区分大小写，请保留原有空格</p>
        </div>
        <div v-if="registering" class="field">
          <label for="confirm-password">确认密码</label>
          <div class="password-control">
            <input id="confirm-password" v-model="confirmPassword" name="confirm_password" :type="showConfirmPassword ? 'text' : 'password'" autocomplete="new-password" placeholder="请再次输入密码" :disabled="pending" :aria-invalid="!!errors.confirm_password" :aria-describedby="errors.confirm_password ? 'confirm-password-error' : 'confirm-password-hint'" />
            <button type="button" :disabled="pending" :aria-label="showConfirmPassword ? '隐藏确认密码' : '显示确认密码'" :aria-pressed="showConfirmPassword" @click="showConfirmPassword = !showConfirmPassword">{{ showConfirmPassword ? '隐藏' : '显示' }}</button>
          </div>
          <p v-if="errors.confirm_password" id="confirm-password-error" class="field-error" role="alert">{{ errors.confirm_password }}</p>
          <p v-else id="confirm-password-hint" class="field-hint">请与上方密码保持一致，包括空格和大小写</p>
        </div>
        <p v-if="message" class="notice error" role="alert">{{ message }}</p>
        <button class="primary-button" type="submit" :disabled="pending">{{ pending ? '正在提交…' : registering ? '创建账号' : '登录' }}<span v-if="!pending" aria-hidden="true">↗</span></button>
      </form>

      <p class="switch-auth">{{ registering ? '已有账号？' : '还没有账号？' }}<RouterLink :to="registering ? '/login' : '/register'">{{ registering ? '返回登录' : '立即注册' }}</RouterLink></p>
      <p class="privacy-note">{{ registering ? '无需邮箱或手机号。注册成功后，请前往登录。' : '使用安全会话登录，8 小时后需重新验证身份。' }}</p>
    </div>
  </section>
</template>
