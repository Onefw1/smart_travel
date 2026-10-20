import { computed, onScopeDispose, ref } from 'vue'
import { defineStore } from 'pinia'
import { ApiError, setCsrfToken } from '../../shared/api/client'
import { authApi } from './api'
import type { Credentials, Session, User } from './types'

export const useSessionStore = defineStore('session', () => {
  const user = ref<User | null>(null)
  const expiresAt = ref<string | null>(null)
  const initialized = ref(false)
  const restoreError = ref('')
  const isAuthenticated = computed(() => user.value !== null)
  let restoring: Promise<void> | null = null
  let expiryTimer: ReturnType<typeof setTimeout> | undefined
  onScopeDispose(() => clearTimeout(expiryTimer))

  function clear() {
    clearTimeout(expiryTimer)
    user.value = null
    expiresAt.value = null
    setCsrfToken(null)
  }

  function apply(session: Session) {
    clearTimeout(expiryTimer)
    user.value = session.user
    expiresAt.value = session.expires_at
    setCsrfToken(session.csrf_token)
    initialized.value = true
    restoreError.value = ''
    expiryTimer = setTimeout(() => {
      clear()
      initialized.value = true
    }, Math.max(0, new Date(session.expires_at).getTime() - Date.now()))
  }

  async function restore() {
    if (restoring) return restoring
    restoring = (async () => {
      try {
        apply(await authApi.me())
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          clear()
          initialized.value = true
          restoreError.value = ''
        } else {
          restoreError.value = error instanceof Error ? error.message : '暂时无法恢复登录状态'
          throw error
        }
      } finally {
        restoring = null
      }
    })()
    return restoring
  }

  async function ensureInitialized() {
    if (user.value && expiresAt.value && new Date(expiresAt.value).getTime() <= Date.now()) {
      clear()
      initialized.value = false
    }
    if (!initialized.value) await restore()
  }
  async function login(credentials: Credentials) { apply(await authApi.login(credentials)) }
  async function logout() {
    await authApi.logout()
    clear()
    initialized.value = true
  }

  return { user, expiresAt, initialized, restoreError, isAuthenticated, clear, restore,
    ensureInitialized, login, logout }
})
