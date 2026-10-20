# F001 最终提交验收报告

本报告是课程提交入口，历史实现和历次反馈见 [原始报告](F001-auth.md)。目标只包含账号 Feature，包含最终确认密码改动。

## 版本与环境

- 功能基线提交：`39b26758c67bec9708821ff36fc6a88c7cb9426f`，实际消息 `feat(auth): implement account flow and project startup`。本轮补充测试端口配置、真实确认密码端到端用例和提交材料，以实际 Git 提交归档。
- 最终源文件 SHA-256：[提交版本清单](../evidence/F001-auth-submission-manifest.sha256)，按 Git 暂存区中待归档的原始文件字节计算，避免 Windows 工作区行尾转换引起误差。历史清单保留为历史状态，包含后来迁移的启动入口，不用于校验本轮最终版本。
- Windows；Python 3.12.14、Node 24.19.0、pnpm 11.25.0；PostgreSQL 18.6。FastAPI 0.153.0、Starlette 1.3.1、pytest 9.1.1、Vue 3.5.44、Vitest 5.0.5、Vite 8.3.4、Playwright 1.56.0；完整版本见两端锁文件。
- 本轮执行日期：2026-10-20（Asia/Shanghai），后端/前端约 23:55；浏览器从 23:55:36 起运行 23.4 秒。
- 数据库先只读核对：账号测试只用 `zhiyou_auth_test`，浏览器只用 `zhiyou_e2e_test`，同为本机 55432 上的独立测试库；合成管理员只在浏览器测试库准备。未对 `zhiyou_dev` 运行测试或清理数据。
- 本轮使用测试端口 **8001 / 5174**，测试进程运行后自行退出；用户现有 8000 服务与 PostgreSQL 实例保持运行。默认开发端口仍为 8000 / 5173。

## 执行命令和真实结果

| 工作目录 | 命令 | 结果 | 证据 |
| --- | --- | --- | --- |
| `backend/` | `python -m pytest tests/unit/test_auth_rules.py tests/integration/test_auth_api.py -q --tb=short --basetemp=../data/local/submission-pytest-temp --junitxml=../docs/testing/evidence/F001-auth-submission-backend.xml` | **71 passed，0 skipped，2 warnings** | [文本](../evidence/F001-auth-submission-backend.txt)、[JUnit](../evidence/F001-auth-submission-backend.xml) |
| `frontend/` | `pnpm test` | **26 passed，4 files** | [文本](../evidence/F001-auth-submission-frontend.txt) |
| `frontend/` | `pnpm build` | 类型检查与生产构建通过 | [文本](../evidence/F001-auth-submission-build.txt) |
| `frontend/` | `pnpm test:e2e` | **20 passed，0 skipped，0 flaky** | [JSON](../evidence/F001-auth-submission-e2e.json)、[文本](../evidence/F001-auth-submission-e2e.txt) |

Python 使用项目 `.venv/Scripts/python.exe`。当前机器 PATH 的 Python/Node 别名不可用，Node 与 pnpm 实际绝对路径见 [原始报告的复现细节](F001-auth.md)。本轮在当前进程 PATH 中前置该 Node，未修改系统环境。`TEMP`/`TMP` 指向工作区 `data/local/tmp`。

后端设置 `TEST_DATABASE_URL` 指向 `zhiyou_auth_test`。浏览器设置 `E2E_DATABASE_URL` 指向 `zhiyou_e2e_test`，并设置专用合成管理员的 `E2E_ADMIN_USERNAME`、`E2E_ADMIN_PASSWORD`；口令不记录在报告。端口设置如下：

```powershell
$env:E2E_BACKEND_PORT = '8001'
$env:E2E_FRONTEND_PORT = '5174'
pnpm test:e2e
```

测试配置把这些端口传递给前后端进程、代理及 Origin 白名单，不复用已有开发服务；仍拒绝未提供的测试库连接和非 `_test` 库名。JSON 报告记录实际配置与每个测试结果。

## 验收范围

- 后端：用户名/密码边界、中文用户名、规范化与并发判重、Argon2id、普通/管理员登录、固定 8 小时到期、凭据错误统一反馈、会话摘要、退出撤销、Origin/JSON/CSRF、角色依赖和故障回滚。
- 前端：字段错误、防重复提交、网络错误与恢复、内存会话与到期清理、角色跳转、安全回跳、确认密码为空/不一致/原密码变动后的复核与修正。
- 浏览器为 5 个场景 × 4 个项目：Chrome、Edge、手机 Chrome 视口、后端同源托管的 Chrome 演示。包括真实注册、失败登录、成功登录、刷新、角色拒绝、退出、重复注册、管理员登录、键盘与布局，以及确认密码失败不发请求、匹配后在测试库真实注册。
- 本轮确认密码的端到端成功由真实 API 返回，补上此前仅用拦截响应检查页面的证据缺口；不是把 Mock 结果当作真实后端通过。
- 2 条后端 warning 为已有第三方 httpx/anyio 弃用提示，未过滤。M001 启动脚本有独立历史 15 项测试记录，本报告的 71 项仅统计 F001 账号测试，未混入其数量。

## 作业要求核对

真实 Feature、已提交代码、有意义的测试、真实通过记录、Agent Development Log 和 Trajectory 均有对应文件；[提交清单](../../submission/README.md) 可直接作为阅读入口。实际功能提交由 Git 验证，文档里的旧“未提交”描述已更新，历史步骤仍保留当时事实。

参与人数按用户明确反馈记录为 **1 人**，不声称多人团队协作或团队评审。课程截图的“团队协同”是否允许单人完成人机协作，须由教师确认；本报告不能替代该课程规则。

人工验收未被用户确认，未证明全旅行系统完成、全系统性能指标或真实手机硬件兼容。没有推送远程或代用户上传课程平台。
