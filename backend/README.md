# 后端目录

技术栈：FastAPI、Pydantic 2、同步 SQLAlchemy 2、psycopg 3、Alembic、PostgreSQL。已实现账号模块及运行基础，其他业务目录仍为骨架。以下表格描述目录职责，不代表各模块均已实现。

| 路径 | 放置内容 |
| --- | --- |
| `app/` | `main.py`，注册路由、异常处理、健康检查与前端静态托管 |
| `app/core/` | 配置、规则、时钟、安全、校验和错误处理 |
| `app/db/` | 模型基类、Session 与 UnitOfWork |
| `app/modules/<模块>/` | 按需新增 `router.py`、`schemas.py`、`models.py`、`repository.py`、`service.py` |
| `app/modules/plans/domain/` | 可独立测试的推荐、交通和排程逻辑 |
| `app/scripts/` | 已有 `seed_admin.py`；后续按功能添加其他种子脚本 |
| `migrations/versions/` | Alembic 迁移文件 |
| `tests/unit/` | 业务规则和纯逻辑单元测试 |
| `tests/integration/` | API、数据库与事务集成测试 |
| `tests/fixtures/` | 测试数据；共用夹具后续写入 `tests/conftest.py` |

管理模块负责鉴权、请求编排和只读统计，业务写入复用相应模块的服务。数据库并发和约束行为使用隔离的 PostgreSQL 测试库验证，测试不得连接开发或演示数据库。

## 环境、安装与启动

本次验证：Windows、Python 3.12.14、PostgreSQL 18.6。依赖声明为 `pyproject.toml`，包括测试依赖的完整锁定为 `requirements.lock`。以下命令均在 `backend/` 执行，使用 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock -e ".[test]"
Copy-Item .env.example .env
```

编辑 `.env` 的 `DATABASE_URL`，填写自己的 PostgreSQL 开发账号与数据库。环境变量优先于 `.env`；该文件已被 Git 忽略。

| 变量 | 用途 |
| --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://用户名:URL编码后的密码@localhost:5432/zhiyou`；默认无口令连接本机 zhiyou，建议显式配置 |
| `FRONTEND_ORIGIN` | 逗号分隔的精确 Origin 列表，默认 `http://localhost:5173,http://localhost:8000` |
| `COOKIE_SECURE` | 本机 HTTP 为 `false`；HTTPS 可设为 `true` |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | 仅用于管理员初始化；没有内置管理员口令 |

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
# 设置管理员环境变量或在未提交的 .env 内填写，再按需执行：
.\.venv\Scripts\python.exe -m app.scripts.seed_admin
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

管理员初始化只创建新账号，重名时拒绝，不提升普通账号或重置密码。启动不会自动创建表；普通用户通过前端注册，不自动登录。

开发浏览器地址为 `http://localhost:5173/#/login`；构建前端后重启后端，可用 `http://localhost:8000/#/login` 演示。使用 hash 路由支持静态托管刷新。不要混用 localhost 与 127.0.0.1 的浏览器访问地址。

## 便捷启动

需要便捷启动时，可在项目根目录执行：

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\start.py
# 同时启动前端开发服务：在上一条命令末尾加 --dev
```

默认使用已构建页面；前置条件、`--check` 和 Node 路径选项见 [启动脚本说明](../scripts/README.md)。已有端口被占用时脚本退出，不停止现有服务。

## 已实现接口

| 接口 | 行为 |
| --- | --- |
| `POST /api/v1/auth/register` | 201，创建普通账号，不建立会话 |
| `POST /api/v1/auth/login` | 固定 8 小时会话，返回用户、CSRF、到期时间 |
| `GET /api/v1/auth/me` | 恢复当前身份与 CSRF，不延长到期时间 |
| `POST /api/v1/auth/logout` | 请求体 `{}`；有有效会话时验证 CSRF，撤销当前会话并清 Cookie |
| `GET /health/live` / `GET /health/ready` | 进程检查 / 数据库与迁移版本检查 |

`/docs` 提供接口文档。写请求必须提供允许的 Origin 与 JSON；后续业务使用 `require_user`、`require_admin` 或 `require_authenticated_write` 实施服务端角色与 CSRF 校验。测试用权限路由不会注册到生产应用。

## 验证

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -q
# 完整测试先准备独立 PostgreSQL 测试库，库名以 _test 结尾：
$env:TEST_DATABASE_URL = 'postgresql+psycopg://测试用户名:测试密码@localhost:5432/zhiyou_auth_test'
.\.venv\Scripts\python.exe -m pytest -q
```

集成测试会执行迁移，并在每个测试前清理专用测试库的账号和会话。测试库不能与开发库相同，也不能包含其他模块的表。未设置测试连接时，集成测试显示跳过，不能视为通过。并发判重、BYTEA 约束与事务回滚均用真实 PostgreSQL 验证。

若 Windows 默认临时目录受限，可把 `TEMP`、`TMP` 指向自己的可写临时目录。真实命令、环境与结果见 [F001 测试报告](../docs/testing/reports/F001-auth.md)。
