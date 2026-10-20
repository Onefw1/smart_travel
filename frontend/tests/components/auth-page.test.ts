import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AuthPage from '../../src/features/auth/pages/AuthPage.vue'
import { authApi } from '../../src/features/auth/api'
import { ApiError } from '../../src/shared/api/client'

vi.mock('../../src/features/auth/api', () => ({ authApi: { register: vi.fn(), login: vi.fn(), me: vi.fn(), logout: vi.fn() } }))

async function render(mode: 'register' | 'login') {
  const router = createRouter({ history: createMemoryHistory(), routes: [
    { path: '/register', component: { template: '<div />' } },
    { path: '/login', component: { template: '<div />' } },
    { path: '/account', component: { template: '<div />' } },
  ] })
  await router.push(`/${mode}`)
  const wrapper = mount(AuthPage, { props: { mode }, global: { plugins: [createPinia(), router] } })
  return { wrapper, router }
}

describe('账号表单', () => {
  beforeEach(() => { vi.resetAllMocks() })

  it('错误字段就地提示且不提交', async () => {
    const { wrapper } = await render('register')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.find('#username-error').text()).toContain('3～20')
    expect(wrapper.find('#password-error').text()).toContain('8～64')
    expect(authApi.register).not.toHaveBeenCalled()
  })

  it('注册成功进入登录页，保留显示名并清空密码，不自动登录', async () => {
    vi.mocked(authApi.register).mockResolvedValue({ id: 'id', username: '旅行同学', role: 'user', created_at: '' })
    const { wrapper, router } = await render('register')
    await wrapper.find('#username').setValue('旅行同学')
    await wrapper.find('#password').setValue('  abcdef')
    await wrapper.find('#confirm-password').setValue('  abcdef')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/login')
    expect(router.currentRoute.value.query.registered).toBe('1')
    expect((wrapper.find('#password').element as HTMLInputElement).value).toBe('')
    expect((wrapper.find('#confirm-password').element as HTMLInputElement).value).toBe('')
    expect(authApi.login).not.toHaveBeenCalled()
    expect(authApi.register).toHaveBeenCalledWith({ username: '旅行同学', password: '  abcdef' })
  })

  it('重复提交只发一次请求，错误显示在用户名附近并保留输入', async () => {
    let reject!: (reason: unknown) => void
    vi.mocked(authApi.register).mockImplementation(() => new Promise((_, failure) => { reject = failure }))
    const { wrapper } = await render('register')
    await wrapper.find('#username').setValue('test_user')
    await wrapper.find('#password').setValue('password')
    await wrapper.find('#confirm-password').setValue('password')
    await wrapper.find('form').trigger('submit')
    await wrapper.find('form').trigger('submit')
    expect(authApi.register).toHaveBeenCalledOnce()
    expect(wrapper.find('button[type=submit]').attributes('disabled')).toBeDefined()
    reject(new ApiError(409, 'USERNAME_TAKEN', '用户名已被使用', [{ field: 'username', message: '用户名已被使用' }]))
    await flushPromises()
    expect(wrapper.find('#username-error').text()).toBe('用户名已被使用')
    expect((wrapper.find('#username').element as HTMLInputElement).value).toBe('test_user')
    expect(wrapper.find('button[type=submit]').attributes('disabled')).toBeUndefined()
  })

  it('登录失败显示统一提示，网络重试后能继续提交', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new ApiError(401, 'INVALID_CREDENTIALS', '用户名或密码错误'))
    const { wrapper } = await render('login')
    expect(wrapper.find('#confirm-password').exists()).toBe(false)
    await wrapper.find('#username').setValue('test_user')
    await wrapper.find('#password').setValue('password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('用户名或密码错误')
    expect(wrapper.find('button[type=submit]').attributes('disabled')).toBeUndefined()
  })

  it.each([
    ['', '请再次输入密码'],
    ['different-password', '两次输入的密码不一致'],
    ['abcdef  ', '两次输入的密码不一致'],
  ])('确认密码为空或与密码原值不同，阻止注册：%s', async (confirmation, reason) => {
    const { wrapper } = await render('register')
    await wrapper.find('#username').setValue('test_user')
    await wrapper.find('#password').setValue('  abcdef')
    await wrapper.find('#confirm-password').setValue(confirmation)
    await wrapper.find('form').trigger('submit')
    expect(wrapper.find('#confirm-password-error').text()).toBe(reason)
    expect(wrapper.find('#confirm-password').attributes('aria-invalid')).toBe('true')
    expect(authApi.register).not.toHaveBeenCalled()
  })

  it('再次修改密码后重新比较确认值，修正后正常提交', async () => {
    vi.mocked(authApi.register).mockResolvedValue({ id: 'id', username: 'test_user', role: 'user', created_at: '' })
    const { wrapper } = await render('register')
    await wrapper.find('#username').setValue('test_user')
    await wrapper.find('#password').setValue('password')
    await wrapper.find('#confirm-password').setValue('password')
    await wrapper.find('#password').setValue('new-password')
    await wrapper.find('form').trigger('submit')
    expect(wrapper.find('#confirm-password-error').text()).toBe('两次输入的密码不一致')
    expect(authApi.register).not.toHaveBeenCalled()
    await wrapper.find('#confirm-password').setValue('new-password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(authApi.register).toHaveBeenCalledWith({ username: 'test_user', password: 'new-password' })
    expect(wrapper.find('#confirm-password-error').exists()).toBe(false)
  })
})
