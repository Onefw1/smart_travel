# 前端目录

技术栈：Vue 3、TypeScript、Vite、Vue Router、Pinia。已实现注册、登录、账号页、管理员身份入口和访问受限页；其他业务页面尚未开发。以下表格描述目录职责。

| 路径 | 放置内容 |
| --- | --- |
| `src/app/` | 已有 `main.ts`、`App.vue`、`router.ts` |
| `src/features/<模块>/pages/` | 业务页面 |
| `src/features/<模块>/components/` | 业务专属组件 |
| `src/features/<模块>/` | auth 已有 `api.ts`、`types.ts`、校验与会话状态；其他模块按需实现 |
| `src/shared/api/` | 统一客户端、错误解析和接口公共类型 |
| `src/shared/components/` | 分页、加载、空状态等通用组件 |
| `src/shared/adapters/` | 地图等适配器 |
| `src/shared/styles/` | 全局样式 |
| `src/assets/` | 构建时处理的图片和图标 |
| `public/` | 原样发布的公开静态资源，不放敏感信息 |
| `tests/unit/` | 工具与状态逻辑测试 |
| `tests/components/` | 组件交互测试 |
| `tests/e2e/` | 完整用户流程测试 |
| `tests/fixtures/` | 测试专用输入与模拟响应 |

## 环境与运行

本次验证使用 Node.js 24.19.0、pnpm 11.25.0、Vue 3.5.44、Vite 8.3.4、TypeScript 5.9.3。精确依赖见 `package.json` 与 `pnpm-lock.yaml`；需先确保 Node 与 pnpm 可运行。

所有命令在 `frontend/` 执行：

```powershell
pnpm install --frozen-lockfile
pnpm dev
pnpm test       # Vitest 单元与组件测试，无需数据库
pnpm build      # Vue/TypeScript 类型检查及生产构建
pnpm audit      # 已知漏洞查询，需要网络
```

先按 [后端说明](../backend/README.md) 完成迁移并在 8000 端口启动后端。开发浏览器地址为 `http://localhost:5173/#/login`；Vite 将 `/api`、`/health` 代理到后端，保留浏览器 Origin，不依赖宽泛 CORS。

构建结果为 `dist/`，后端启动时会自动挂载，可在 `http://localhost:8000/#/login` 同源演示。`pnpm preview` 仅提供静态预览，没有接口代理，账号联调用上述开发或演示地址。

## 账号行为

- 注册只创建普通用户，不收集邮箱、手机号，不自动登录。
- 用户名去首尾空格、ASCII 大小写不敏感；密码保留原始空格与大小写。
- 注册页面要求确认密码，未填写或与密码原值不一致时就地提示并阻止提交；确认值只在页面内比较，成功后清空，不发送给后端。登录页面仍只输入用户名和密码。
- 用户与 CSRF 只保存在内存，Cookie 为 HttpOnly；刷新经 `/auth/me` 恢复身份。退出、401 或到期清理身份。
- 路由分别保护 `/account` 与 `/admin`；登录回跳限定为当前角色的站内入口。服务端角色依赖独立校验权限。
- 表单处理提交中、字段错误、凭据失败、网络失败和会话恢复重试。

## 浏览器测试

需安装 Chrome、Edge，并准备另外的、名为 `*_test` 的独立 PostgreSQL 库。测试自动启动前后端，不复用已占用 5173/8000 的服务。以下值须替换为自己的测试连接与测试账号，不用真实用户：

```powershell
$env:E2E_DATABASE_URL = 'postgresql+psycopg://测试用户名:测试密码@localhost:5432/zhiyou_e2e_test'
# 先在 backend/ 用该连接执行 alembic upgrade head，并用 seed_admin 创建测试管理员。
$env:E2E_ADMIN_USERNAME = '你创建的测试管理员'
$env:E2E_ADMIN_PASSWORD = '你设置的测试口令'
pnpm test:e2e
```

后端 Python 默认使用项目 `.venv`，可用 `E2E_PYTHON` 指定其他实际可执行文件。未提供测试管理员时，对应场景明确跳过。测试覆盖开发模式的 Chrome、Edge、手机视口，以及后端托管构建产物的 Chrome 演示模式；运行前先执行 `pnpm build`。手机视口不等于真机验收。结果和截图在 `docs/testing/evidence/F001-auth-*`，禁用可能包含凭据的 trace/HAR。

已有开发服务运行时，可设置 `E2E_BACKEND_PORT=8001`、`E2E_FRONTEND_PORT=5174` 使用备用测试端口；测试仍单独启动服务并连接显式指定的测试库。代理目标通过仅服务端使用的 `API_PROXY_TARGET` 传递，正常开发默认仍连接 8000。本轮最终 JSON 报告为 `docs/testing/evidence/F001-auth-submission-e2e.json`。

界面建筑图由项目内 SVG/CSS 绘制，无外部图片或字体依赖。真实验证见 [测试报告](../docs/testing/reports/F001-auth.md)。
