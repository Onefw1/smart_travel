import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import type { RouteLocationNormalized } from 'vue-router'
import { authGuard, safeDestination } from '../../src/app/router'
import { useSessionStore } from '../../src/features/auth/session-store'

describe('页面角色守卫与跳转', () => {
  beforeEach(() => { setActivePinia(createPinia()) })
  const target = (path: string, meta: Record<string, unknown>) => ({ path, meta }) as RouteLocationNormalized

  it('游客访问受保护页面跳转登录', async () => {
    useSessionStore().initialized = true
    expect(await authGuard(target('/admin', { role: 'admin' }))).toEqual({ path: '/login', query: { redirect: '/admin' } })
  })
  it('普通用户访问后台被拒绝', async () => {
    const store = useSessionStore()
    store.initialized = true
    store.user = { id: 'id', username: 'tester', role: 'user', created_at: '' }
    expect(await authGuard(target('/admin', { role: 'admin' }))).toEqual({ path: '/forbidden' })
  })
  it('管理员登录后进入对应入口', async () => {
    const store = useSessionStore()
    store.initialized = true
    store.user = { id: 'id', username: 'admin', role: 'admin', created_at: '' }
    expect(await authGuard(target('/login', { guest: true }))).toBe('/admin')
  })
  it('服务不可用时不放行受保护页面', async () => {
    vi.spyOn(useSessionStore(), 'ensureInitialized').mockRejectedValue(new Error('network'))
    expect(await authGuard(target('/account', { role: 'user' }))).toEqual({ path: '/login' })
  })
  it.each(['https://evil.example', '//evil.example', '/admin', ['/account'], undefined])('拒绝外部或不符合角色的回跳 %s', (redirect) => {
    expect(safeDestination(redirect, 'user')).toBe('/account')
  })
})
