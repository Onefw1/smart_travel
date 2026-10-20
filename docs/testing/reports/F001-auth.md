# F001：账号功能测试报告

本文保留各轮历史执行状态。当前最终代码、71/26/20 项验收与实际 Git 提交请以 [最终提交验收报告](F001-auth-submission.md) 为准；历史段落中的“未提交”“未重跑”等只描述当时状态。

日期：2026-10-20，Asia/Shanghai。状态：本次账号范围的自动化检查完成，用户人工验收待执行。Git 起始版本 `9262b87`，当前未提交；对应实现与测试文件的精确版本见 [SHA-256 清单](../evidence/F001-auth-manifest.sha256)。

## 环境与范围

- 工作区：`D:\Documents\lecture homework\travel`，Windows，Python 3.12.14、Node.js 24.19.0、pnpm 11.25.0。
- 后端：FastAPI 0.153.0、Starlette 1.3.1、Pydantic 2.11.10、SQLAlchemy 2.0.44、psycopg 3.2.10、Alembic 1.17.0、argon2-cffi 25.1.0、pytest 9.1.1、httpx 0.28.1；完整依赖见 `backend/requirements.lock`。
- 前端：Vue 3.5.44、Pinia 3.0.3、Vue Router 4.6.3、Vite 8.3.4、Vitest 5.0.5、TypeScript 5.9.3、Playwright 1.56.0；完整锁定见 `frontend/pnpm-lock.yaml`。
- 浏览器实际版本：Chrome 155.0.8059.85；Edge 155.0.4283.62。手机项目使用 Pixel 7 视口及 Chrome，未使用真实手机。
- PostgreSQL 18.6：另起的回环实例 `127.0.0.1:55432`，仅本次合成测试数据。账号/API 使用 `zhiyou_auth_test`，浏览器使用 `zhiyou_e2e_test`，迁移往返使用 `zhiyou_migration_test`。不是用户的开发库；没有连接现有真实业务数据。
- 测试前检查目标为 `_test` 库、与开发连接不同且无其他模块表；浏览器亦要求显式配置 `_test` 连接。没有用 SQLite 或 Mock 证明 PostgreSQL 的行为。

## 命令与结果

下表 `python` 代表 `backend/.venv/Scripts/python.exe`；`pnpm` 使用实际可用的绝对路径执行（见下节），并非依赖当时失效的 PATH shim。

| 工作目录 | 命令/操作 | 实际结果 | 输出 |
| --- | --- | --- | --- |
| `backend/` | `python -m pip install -e '.[test]'`，生成 `requirements.lock`；`python -m pip check` | 安装成功，无依赖冲突 | 锁文件及工具执行记录 |
| `backend/` | `python -m pytest -q --tb=short --basetemp=../data/local/pytest-temp --junitxml=../docs/testing/evidence/F001-auth-backend.xml` | **71 passed，2 warnings，0 skipped** | [文本](../evidence/F001-auth-backend.txt)、[JUnit](../evidence/F001-auth-backend.xml) |
| `frontend/` | `pnpm install --store-dir ../data/local/pnpm-store` | 安装完成，保留完整锁文件 | `pnpm-lock.yaml` |
| `frontend/` | `pnpm test` | **22 passed，4 files** | [文本](../evidence/F001-auth-frontend.txt) |
| `frontend/` | `pnpm build` | Vue/TypeScript 类型检查及生产构建成功 | [文本](../evidence/F001-auth-build.txt) |
| `frontend/` | `pnpm test:e2e` | **16 passed，0 skipped，0 flaky** | [JSON](../evidence/F001-auth-e2e.json)、[文本](../evidence/F001-auth-e2e.txt) |
| `backend/` | 新建空的 `zhiyou_migration_test`，显式设置该连接后依次 `alembic upgrade head`、`downgrade base`、`upgrade head`、`check` | 四条均成功，最终输出 `No new upgrade operations detected.` | 本次工具执行记录；仅回退专用空测试库 |
| `frontend/` | `pnpm audit` | 未发现已知漏洞 | [输出](../evidence/F001-auth-node-audit.txt) |
| 项目根目录 | 独立工具目录内的 `pip_audit -r backend/requirements.lock --no-deps --disable-pip --cache-dir data/local/audit-cache` | 未发现已知漏洞 | [输出](../evidence/F001-auth-python-audit.txt) |
| 项目根目录 | `git diff --check` | 通过；仅提示工作区 LF 后续可能由 Git 转 CRLF | 工具执行记录 |

最终后端运行约 23:10，浏览器报告起始时间为 23:11:48，耗时约 20 秒。Python 测试的两条 warning 来自第三方 TestClient 对 httpx 及 anyio 别名的弃用提示，未过滤或写成失败。依赖锁定使用精确版本，Python 审计仍提示可进一步使用哈希锁定；本次未声称已启用哈希校验安装。

## 本机复现细节

当前机器 PATH 中的 Node shim 与 Python WindowsApps 别名不可用；本次没有修改系统 PATH，而是使用已存在的运行时：

- 初始 Python：`C:\Users\fw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`，用于创建项目 `.venv`。
- Node：`C:\Users\fw\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe`。
- pnpm：`C:\Users\fw\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd`；执行前在当前进程 PATH 前置 Node 目录。
- PostgreSQL 工具：`C:\Program Files\PostgreSQL\18\bin\`。
- `TEMP`/`TMP` 指向工作区 `data/local/tmp`；数据库、本地工具和依赖缓存均在被 Git 忽略的目录中。

后端测试设置 `TEST_DATABASE_URL` 为上述账号测试库；浏览器设置 `E2E_DATABASE_URL` 为上述浏览器测试库，并提供通过初始化命令创建的合成管理员。测试管理员口令不作为开发默认口令，也不在报告中保存。先执行迁移，再创建该测试管理员。浏览器测试自动起停 5173/8000 的应用进程。

验证结束后，使用 `pg_ctl -D` 指定项目内的 `data/local/auth-test-pg`，以 fast 模式正常关闭本次测试实例，工具确认 `server stopped`；未停止其他服务。源码清单复核为 55 个文件、0 差异。

长期本机运行仍需配置自己的 PostgreSQL 开发数据库，按 [运行说明](../../deployment/README.md) 和两端 README 操作，不把临时测试库当作已配置的开发环境。

## 覆盖与证据

| 需求 / 验收 | 已验证行为 |
| --- | --- |
| FR-AUTH-001～002 / AC-US-004 | 中文用户名、3/20 与 2/21 边界、大小写与首尾空格判重、8/64 密码边界、密码原值、随机盐 Argon2id、拒绝 role/未知字段、公开注册固定 user、不自动登录；真实 PostgreSQL 并发注册仅一个成功 |
| FR-AUTH-003～004 / AC-US-005 | 普通用户/管理员登录，凭据错误同文案，会话凭据只存摘要、固定 8 小时、到期精确边界、刷新恢复、重新登录新凭据、退出仅撤销当前会话、匿名退出幂等 |
| FR-AUTH-005 / FR-ADM-001 / AC-US-006 的角色部分 | 服务端依赖拒绝游客/错误角色，普通用户不能进入后台、管理员不能使用普通用户依赖；浏览器角色守卫与安全回跳；验证路由只在测试内注册 |
| 安全与错误 | 缺失/伪造/跨会话 CSRF，缺失/null/恶意/近似 Origin，JSON 媒体类型、非法 JSON、未知字段、统一中文错误与 request_id，数据库故障不泄露内部文本 |
| 事务与数据库 | 唯一约束、会话摘要 BYTEA 长度约束、注册/登录 flush 后故障回滚，不返回半完成会话 Cookie，管理员初始化不提升或重置已有账号 |
| 界面与状态 | 字段就地提示、防重复提交、统一错误提示、网络失败可重试、内存会话到期清理、不向 localStorage/sessionStorage 写凭据、键盘提交、无横向溢出 |
| 运行模式 | 开发 Vite 代理、FastAPI 托管 dist 同源演示，两种模式均实际完成浏览器账号闭环 |

Agent 已查看 [桌面截图](../evidence/F001-auth-chrome.png) 和 [手机视口截图](../evidence/F001-auth-mobile-chrome.png)，未见文字遮挡与横向溢出。另保留 [Edge](../evidence/F001-auth-edge.png) 与 [同源演示](../evidence/F001-auth-demo-chrome.png) 截图。图中无真实用户或口令；没有保存 trace/HAR。

## 已发生的问题与修复

首次虚拟环境安装被默认临时目录权限阻断，调整临时目录后完成。依赖安装和本机数据库连接受沙箱限制，经工具审批在可访问环境完成。测试实例经历恢复等待后可连接，首轮集成检查的 40 个初始化错误属于环境未就绪；未将其记为通过。

连接恢复后出现 2 个真实失败：从 PostgreSQL 读回的时间按数据库时区输出，以及后加的测试权限路由被静态挂载遮挡。分别在响应模型统一 UTC、测试应用禁用静态挂载后修复。前端也曾有 unknown 回跳类型错误，收窄字符串类型后通过构建。初选依赖审计发现旧版本问题，升级后重新运行全部相关验证；最终输出见上表。

## 尚未验证或未实现

用户尚未人工验收；没有验证真机兼容或全系统性能指标。其他业务未实现，故未验证收藏、行程、预约、评价的用户 A/B 所有权隔离，不能将本报告视为整个 AC-US-006 或整个 MVP 的通过证据。管理员页目前只展示身份入口，不提供尚未开发的业务管理能力。没有提交、推送或创建 PR。

## 后续本机配置验收

用户随后明确要求配置管理员，并指定开发库 `zhiyou_dev`、端口 `55432`。复查时该库和 `users`、`sessions`、`alembic_version` 已存在，迁移为 `0001_auth`；没有重建表或清空现有数据。新建被忽略的 `backend/.env`，执行 `alembic upgrade head` 后用既有种子命令创建 `admin`，用户指定口令仅哈希入库，未记入文档或配置。

8000 端口已有本项目后端，复用了该服务，未重启。使用实际 HTTP 请求验证：`/health/ready` 200、静态入口 200、管理员登录 200/角色 admin、`/auth/me` 200、退出 204、退出后身份查询 401；另核对响应账号 ID 与开发库新建管理员一致，验证后退出。此次为用户授权的开发配置验收，没有在开发库运行会清理表数据的集成测试，也未改变上述自动化测试统计。当前实例与后端保持运行，见 [当前配置](../../deployment/README.md)。

## 后续追加：注册确认密码

用户要求注册界面新增确认密码。实现只修改前端注册页：确认密码必填、与密码原值精确一致（不去空格、不忽略大小写），错误就地提示并阻止提交；修改原密码后重新比较，注册成功清空两个密码值。API 请求仍仅含 username/password，登录页面不要求确认密码。

- 在 `frontend/` 执行 `pnpm test`：**26 passed，4 files**，包含未确认、不一致、空格差异、原密码修改后复核、修正后提交，以及原有登录与状态用例。[真实输出](../evidence/F001-auth-confirm-password-frontend.txt)。
- 在 `frontend/` 执行 `pnpm build`：类型检查与生产构建通过，当前 8000 页面使用新构建。[输出](../evidence/F001-auth-confirm-password-build.txt)。
- 使用 Node/Playwright 对当前 `http://localhost:8000/#/register` 进行桌面 1280×900 和手机视口 390×844 检查：确认输入存在、空值/不一致不发请求、精确匹配后提交、请求无确认字段、转登录后隐藏确认字段、无横向溢出，均通过。[输出](../evidence/F001-auth-confirm-password-browser.txt)。执行脚本为被忽略的本地 `data/local/check-confirm-password.mjs`，从 `frontend/` 执行 `node ../data/local/check-confirm-password.mjs`。
- 浏览器注册响应被拦截为合成响应，**未向开发库写入测试账号**。这项是页面专项检查，不记作真实后端注册端到端通过。已有完整端到端测试的注册步骤已适配新字段，本轮未重跑完整套件，以免与用户当前使用的服务端口冲突。后端与数据库结构未更改，本轮未重跑后端测试。
- Agent 已查看 [桌面注册截图](../evidence/F001-auth-confirm-password-desktop.png)、[手机注册截图](../evidence/F001-auth-confirm-password-mobile.png)，未发现遮挡或溢出。用户人工验收待执行。
- 本轮源码版本见 [追加 SHA-256 清单](../evidence/F001-auth-confirm-password-manifest.sha256)；前文原始清单和完整测试记录保留为当时版本证据，尚未提交 Git。
