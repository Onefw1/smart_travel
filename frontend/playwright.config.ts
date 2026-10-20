import { defineConfig, devices } from '@playwright/test'

const databaseUrl = process.env.E2E_DATABASE_URL
if (!databaseUrl || !new URL(databaseUrl).pathname.endsWith('_test')) {
  throw new Error('浏览器测试必须显式设置 E2E_DATABASE_URL，数据库名以 _test 结尾；不得使用开发库')
}
const python = process.env.E2E_PYTHON ?? (process.platform === 'win32'
  ? '../backend/.venv/Scripts/python.exe' : '../backend/.venv/bin/python')

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list'], ['json', { outputFile: '../docs/testing/evidence/F001-auth-e2e.json' }]],
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    // 避免把包含会话和表单输入的 trace/HAR 作为交付材料。
    trace: 'off',
  },
  projects: [
    { name: 'chrome', use: { ...devices['Desktop Chrome'], channel: 'chrome' } },
    { name: 'edge', use: { ...devices['Desktop Edge'], channel: 'msedge' } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'], defaultBrowserType: 'chromium', channel: 'chrome' } },
    { name: 'demo-chrome', use: { ...devices['Desktop Chrome'], channel: 'chrome', baseURL: 'http://localhost:8000' } },
  ],
  webServer: [
    {
      command: `"${python}" -m uvicorn app.main:app --app-dir ../backend --host 127.0.0.1 --port 8000 --no-access-log`,
      url: 'http://localhost:8000/health/ready',
      env: { DATABASE_URL: databaseUrl, FRONTEND_ORIGIN: 'http://localhost:5173,http://localhost:8000' },
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: 'node node_modules/vite/bin/vite.js --host localhost --port 5173 --strictPort',
      url: 'http://localhost:5173',
      reuseExistingServer: false,
      timeout: 30000,
    },
  ],
})
