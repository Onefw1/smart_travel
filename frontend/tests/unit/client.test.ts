import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, onUnauthorized, request, setCsrfToken } from '../../src/shared/api/client'

describe('公共请求客户端', () => {
  const fetchMock = vi.fn()
  beforeEach(() => { vi.stubGlobal('fetch', fetchMock); setCsrfToken(null); onUnauthorized(() => {}) })
  afterEach(() => { vi.unstubAllGlobals(); fetchMock.mockReset() })

  it('发送同源 Cookie 和内存 CSRF，退出提交空对象', async () => {
    setCsrfToken('session-csrf')
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))
    await request('/auth/logout', {})
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/auth/logout', expect.objectContaining({
      credentials: 'same-origin', method: 'POST', body: '{}',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': 'session-csrf' },
    }))
  })

  it('未登录注册不要求已有 CSRF', async () => {
    fetchMock.mockResolvedValue(new Response('{}', { status: 201 }))
    await request('/auth/register', { username: 'tester', password: 'password' })
    expect(fetchMock.mock.calls[0][1].headers).toEqual({ 'Content-Type': 'application/json' })
  })

  it('401 清理登录状态并保留统一错误信息', async () => {
    const expired = vi.fn()
    onUnauthorized(expired)
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ error: {
      code: 'AUTH_REQUIRED', message: '请先登录或重新登录', details: [],
    } }), { status: 401 }))
    await expect(request('/auth/me')).rejects.toMatchObject({ status: 401, code: 'AUTH_REQUIRED' })
    expect(expired).toHaveBeenCalledOnce()
  })

  it('网络失败给出中文提示且不重试写请求', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(request('/auth/login', {})).rejects.toBeInstanceOf(ApiError)
    expect(fetchMock).toHaveBeenCalledOnce()
  })
})
