# 后端目录

规划技术栈：FastAPI、Pydantic 2、同步 SQLAlchemy 2、psycopg 3、Alembic、PostgreSQL。当前只创建目录，尚无应用入口或依赖配置。

| 路径 | 放置内容 |
| --- | --- |
| `app/` | 后续的 `main.py`，注册路由与应用级处理 |
| `app/core/` | 配置、规则、时钟、安全、校验和错误处理 |
| `app/db/` | 模型基类、Session 与 UnitOfWork |
| `app/modules/<模块>/` | 按需新增 `router.py`、`schemas.py`、`models.py`、`repository.py`、`service.py` |
| `app/modules/plans/domain/` | 可独立测试的推荐、交通和排程逻辑 |
| `app/scripts/` | 需要导入应用的初始化与种子导入脚本 |
| `migrations/versions/` | Alembic 迁移文件 |
| `tests/unit/` | 业务规则和纯逻辑单元测试 |
| `tests/integration/` | API、数据库与事务集成测试 |
| `tests/fixtures/` | 测试数据；共用夹具后续写入 `tests/conftest.py` |

管理模块负责鉴权、请求编排和只读统计，业务写入复用相应模块的服务。数据库并发和约束行为使用隔离的 PostgreSQL 测试库验证，测试不得连接开发或演示数据库。

具体依赖版本、迁移配置与启动命令在初始化应用时确认。
