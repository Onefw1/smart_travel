import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useSessionStore } from '../../src/features/auth/session-store'
import { authApi } from '../../src/features/auth/api'
import { ApiError } from '../../src/shared/api/client'

vi.mock('../../src/features/auth/api', () => ({ authApi: { me: vi.fn(), login: vi.fn(), logout: vi.fn() } }))
const session = {
  user: { id: 'test-id', username: 'tester', role: 'user' as const, created_at: '2026-10-20T00:00:00Z' },
  csrf_token: 'csrf', expires_at: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
}

describe('内存会话状态', () => {
  beforeEach(() => { setActivePinia(createPinia()); vi.resetAllMocks() })

  it('刷新时从服务器恢复身份，合并并发恢复请求', async () => {
    vi.mocked(authApi.me).mockResolvedValue(session)
    const store = useSessionStore()
    await Promise.all([store.ensureInitialized(), store.ensureInitialized()])
    expect(authApi.me).toHaveBeenCalledOnce()
    expect(store.user?.username).toBe('tester')
  })

  it('未登录 401 是游客状态', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new ApiError(401, 'AUTH_REQUIRED', '请先登录'))
    const store = useSessionStore()
    await store.restore()
    expect(store.user).toBeNull()
    expect(store.initialized).toBe(true)
    expect(store.restoreError).toBe('')
  })

  it('恢复时网络失败可重试，不能伪装成成功', async () => {
    vi.mocked(authApi.me).mockRejectedValueOnce(new ApiError(0, 'NETWORK_ERROR', '网络异常')).mockResolvedValueOnce(session)
    const store = useSessionStore()
    await expect(store.ensureInitialized()).rejects.toThrow('网络异常')
    expect(store.initialized).toBe(false)
    await store.ensureInitialized()
    expect(store.user?.role).toBe('user')
    expect(store.restoreError).toBe('')
  })

  it('退出成功清理状态，退出失败保留状态以便重试', async () => {
    const store = useSessionStore()
    vi.mocked(authApi.login).mockResolvedValue(session)
    await store.login({ username: 'tester', password: 'password' })
    vi.mocked(authApi.logout).mockRejectedValueOnce(new Error('网络异常')).mockResolvedValueOnce(undefined)
    await expect(store.logout()).rejects.toThrow('网络异常')
    expect(store.isAuthenticated).toBe(true)
    await store.logout()
    expect(store.user).toBeNull()
    expect(store.expiresAt).toBeNull()
  })

  it('到期时清理内存身份，不续期', async () => {
    vi.useFakeTimers()
    try {
      vi.mocked(authApi.login).mockResolvedValue({ ...session, expires_at: new Date(Date.now() + 1000).toISOString() })
      const store = useSessionStore()
      await store.login({ username: 'tester', password: 'password' })
      await vi.advanceTimersByTimeAsync(999)
      expect(store.isAuthenticated).toBe(true)
      await vi.advanceTimersByTimeAsync(1)
      expect(store.isAuthenticated).toBe(false)
      expect(store.expiresAt).toBeNull()
    } finally { vi.useRealTimers() }
  })
})
