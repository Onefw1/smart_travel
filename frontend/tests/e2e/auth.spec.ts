import { test, expect } from '@playwright/test'

test('注册、错误凭据、登录、刷新、角色拒绝与退出闭环', async ({ page, context }, testInfo) => {
  const username = `旅测_${Date.now()}_${testInfo.project.name.slice(0, 2)}`
  const password = '  browser-test-only  '
  await page.goto('/#/register')
  await page.getByLabel('用户名', { exact: true }).fill(username)
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByLabel('确认密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '创建账号', exact: true }).click()
  await expect(page.getByRole('status')).toHaveText('注册成功，请使用新账号登录。')
  expect((await context.cookies()).some(cookie => cookie.name === 'session_id')).toBe(false)

  await page.getByLabel('密码', { exact: true }).fill('wrong-password')
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await expect(page.getByRole('alert')).toHaveText('用户名或密码错误')
  await page.getByLabel('密码', { exact: true }).fill(password)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await expect(page.getByRole('heading', { name: `你好，${username}` })).toBeVisible()
  const cookie = (await context.cookies()).find(item => item.name === 'session_id')!
  expect(cookie.httpOnly).toBe(true)
  expect(cookie.sameSite).toBe('Lax')
  expect(await page.evaluate(() => document.cookie)).not.toContain('session_id')
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([])
  expect(await page.evaluate(() => Object.keys(sessionStorage))).toEqual([])

  await page.reload()
  await expect(page.getByText('普通用户', { exact: true })).toBeVisible()
  await page.goto('/#/admin')
  await expect(page.getByRole('heading', { name: '当前账号无权访问此页面' })).toBeVisible()
  await page.getByRole('link', { name: '返回账号页面' }).click()
  await page.getByRole('button', { name: '退出登录' }).click()
  await expect(page.getByRole('heading', { name: '登录智游北京' })).toBeVisible()
  expect((await context.cookies()).some(item => item.name === 'session_id')).toBe(false)
  await page.goto('/#/account')
  await expect(page.getByRole('heading', { name: '登录智游北京' })).toBeVisible()
  const me = await page.request.get('/api/v1/auth/me')
  expect(me.status()).toBe(401)
})

test('重复注册显示字段错误', async ({ page, request }, testInfo) => {
  const username = `重复_${Date.now()}_${testInfo.project.name.slice(0, 2)}`
  await request.post('/api/v1/auth/register', {
    data: { username, password: 'test-only-password' },
    headers: { Origin: new URL(testInfo.project.use.baseURL as string).origin },
  })
  await page.goto('/#/register')
  await page.getByLabel('用户名', { exact: true }).fill(`  ${username.toUpperCase()}  `)
  await page.getByLabel('密码', { exact: true }).fill('test-only-password')
  await page.getByLabel('确认密码', { exact: true }).fill('test-only-password')
  await page.getByRole('button', { name: '创建账号', exact: true }).click()
  await expect(page.locator('#username-error')).toHaveText('用户名已被使用')
})

test('管理员使用独立预置账号进入对应入口', async ({ page }) => {
  test.skip(!process.env.E2E_ADMIN_USERNAME || !process.env.E2E_ADMIN_PASSWORD, '未提供独立测试管理员；不得使用真实管理员账号')
  await page.goto('/#/login')
  await page.getByLabel('用户名', { exact: true }).fill(process.env.E2E_ADMIN_USERNAME!)
  await page.getByLabel('密码', { exact: true }).fill(process.env.E2E_ADMIN_PASSWORD!)
  await page.getByRole('button', { name: '登录', exact: true }).click()
  await expect(page.getByText('管理员入口', { exact: true })).toBeVisible()
  await expect(page).toHaveURL(/#\/admin$/)
  await page.reload()
  await expect(page.getByText('管理员入口', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: '退出登录' }).click()
  await expect(page.getByRole('heading', { name: '登录智游北京' })).toBeVisible()
})

test('账号页面没有横向溢出且可用键盘提交', async ({ page, browser }, testInfo) => {
  await page.goto('/#/login')
  await expect(page.getByRole('heading', { name: '登录智游北京' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
  testInfo.annotations.push({ type: 'browser', description: browser.version() })
  await page.screenshot({ path: `../docs/testing/evidence/F001-auth-${testInfo.project.name}.png`, fullPage: true })
  await page.getByLabel('用户名', { exact: true }).fill('test_user')
  await page.getByLabel('密码', { exact: true }).fill('test-only-password')
  await page.getByLabel('密码', { exact: true }).press('Enter')
  await expect(page.getByRole('alert')).toHaveText('用户名或密码错误')
  await page.getByLabel('密码', { exact: true }).fill('')
  await page.getByLabel('用户名', { exact: true }).fill('')
})

test('注册确认密码必须填写且精确一致，匹配后可真实注册', async ({ page, context }, testInfo) => {
  const username = `确认_${Date.now()}_${testInfo.project.name.slice(0, 2)}`
  let submissions = 0
  page.on('request', request => {
    if (request.method() === 'POST' && new URL(request.url()).pathname === '/api/v1/auth/register') submissions++
  })
  await page.goto('/#/register')
  await page.getByLabel('用户名', { exact: true }).fill(username)
  await page.getByLabel('密码', { exact: true }).fill('  abcdef')
  await page.getByRole('button', { name: '创建账号', exact: true }).click()
  await expect(page.locator('#confirm-password-error')).toHaveText('请再次输入密码')
  expect(submissions).toBe(0)
  await page.getByLabel('确认密码', { exact: true }).fill('abcdef  ')
  await page.getByRole('button', { name: '创建账号', exact: true }).click()
  await expect(page.locator('#confirm-password-error')).toHaveText('两次输入的密码不一致')
  expect(submissions).toBe(0)
  await page.getByLabel('确认密码', { exact: true }).fill('  abcdef')
  await page.getByRole('button', { name: '创建账号', exact: true }).click()
  await expect(page.getByRole('status')).toHaveText('注册成功，请使用新账号登录。')
  expect(submissions).toBe(1)
  expect((await context.cookies()).some(cookie => cookie.name === 'session_id')).toBe(false)
})
