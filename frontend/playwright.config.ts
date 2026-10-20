import { defineConfig, devices } from '@playwright/test'

const databaseUrl = process.env.E2E_DATABASE_URL
if (!databaseUrl || !new URL(databaseUrl).pathname.endsWith('_test')) {
  throw new Error('浏览器测试必须显式设置 E2E_DATABASE_URL，数据库名以 _test 结尾；不得使用开发库')
}
const python = process.env.E2E_PYTHON ?? (process.platform === 'win32'
  ? '../backend/.venv/Scripts/python.exe' : '../backend/.venv/bin/python')

function portFromEnv(name: string, fallback: number) {
  const port = Number(process.env[name] ?? fallback)
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error(`${name} 必须为有效端口`)
  return port
}
const backendPort = portFromEnv('E2E_BACKEND_PORT', 8000)
const frontendPort = portFromEnv('E2E_FRONTEND_PORT', 5173)
if (backendPort === frontendPort) throw new Error('浏览器测试前后端端口不能相同')
const backendOrigin = `http://localhost:${backendPort}`
const frontendOrigin = `http://localhost:${frontendPort}`

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['json', { outputFile: '../docs/testing/evidence/F001-auth-submission-e2e.json' }]],
  use: {
    baseURL: frontendOrigin,
    screenshot: 'only-on-failure',
    // 避免把包含会话和表单输入的 trace/HAR 作为交付材料。
    trace: 'off',
  },
  projects: [
    { name: 'chrome', use: { ...devices['Desktop Chrome'], channel: 'chrome' } },
    { name: 'edge', use: { ...devices['Desktop Edge'], channel: 'msedge' } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'], defaultBrowserType: 'chromium', channel: 'chrome' } },
    { name: 'demo-chrome', use: { ...devices['Desktop Chrome'], channel: 'chrome', baseURL: backendOrigin } },
  ],
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port ${backendPort} --no-access-log`,
      url: `${backendOrigin}/health/ready`,
      env: { DATABASE_URL: databaseUrl, FRONTEND_ORIGIN: `${frontendOrigin},${backendOrigin}` },
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: `node node_modules/vite/bin/vite.js --host localhost --port ${frontendPort} --strictPort`,
      url: frontendOrigin,
      env: { API_PROXY_TARGET: backendOrigin },
      reuseExistingServer: false,
      timeout: 30000,
    },
  ],
})
