# 运行与部署说明

当前已实现 F001 账号闭环，其他业务仍为骨架。安装、启动和验证命令见 [后端说明](../../backend/README.md) 与 [前端说明](../../frontend/README.md)。运行步骤如下：

1. 安装 Node.js、pnpm、Python 与本机 PostgreSQL，具体已验证版本见两端说明。
2. 在本机 PostgreSQL 管理工具中创建自己的开发登录角色和数据库，并配置 `backend/.env` 的 `DATABASE_URL`；文件及口令不提交。
3. 在 `backend/` 安装锁定依赖，使用项目虚拟环境执行 `python -m alembic upgrade head`；启动不会自动建表。
4. 按需设置 `ADMIN_USERNAME`、`ADMIN_PASSWORD`，执行 `python -m app.scripts.seed_admin`；没有默认口令。
5. 在 `backend/` 执行 `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`。
6. 开发时在 `frontend/` 执行 `pnpm dev`，访问 `http://localhost:5173/#/register`。
7. 演示时在 `frontend/` 执行 `pnpm build`，重启后端，访问 `http://localhost:8000/#/login`。
8. `/health/live` 应为 200，`/health/ready` 应为 200 且返回迁移 `0001_auth`。

开发数据库创建示例（在你自己的 PostgreSQL 管理会话执行，并替换口令）：

```sql
CREATE ROLE zhiyou LOGIN PASSWORD '请替换为你自己的本机口令';
CREATE DATABASE zhiyou OWNER zhiyou;
```

连接必须使用 `postgresql+psycopg`，密码中特殊字符需 URL 编码。本机浏览器固定使用 localhost，不混用 127.0.0.1。更改端口或 HTTPS 时，同步配置允许的 `FRONTEND_ORIGIN` 与 `COOKIE_SECURE`。

最初的功能验证使用另外启动的 PostgreSQL 18.6（127.0.0.1:55432）；账号/API、浏览器和迁移检查使用各自独立测试库，真实结果见 [测试报告](../testing/reports/F001-auth.md)。后续按用户指定配置了同一实例内的 `zhiyou_dev` 开发库，当前配置见下节。

## 当前本机开发配置

- 数据库：`127.0.0.1:55432/zhiyou_dev`，连接角色为该本机实例已有的 `auth_test_runner`。
- 配置文件：`backend/.env`，已确认被 Git 忽略；只保留数据库连接、允许的 Origin 与本机 Cookie 设置，不保存管理员明文密码。
- 数据库已有 `users`、`sessions`、`alembic_version`；本次确认版本为 `0001_auth`，没有重建表或清空现有数据。
- 已初始化管理员 `admin`，密码由用户指定，仅将 Argon2id 摘要存入数据库，口令不记入本文档。
- 登录地址：`http://localhost:8000/#/login`，使用现有项目后端与已构建前端；8000 已运行，未重复启动或重启。
- 已实际验证健康检查、页面入口、管理员登录、身份恢复及退出；已核对运行中的后端账号 ID 与 `zhiyou_dev` 中新建账号一致，验证会话均已退出。

55432 当前由项目内 `data/local/auth-test-pg` 实例提供，已复用为开发用途；开发库与 `*_test` 测试库的数据相互独立。该实例现在包含开发账号，后续测试完成后不要自动停止或清理整个实例。未改动本机另一个 5432 PostgreSQL 服务。

若重启电脑后 55432 未运行，可在项目根目录执行（启动日志放在数据目录外）：

```powershell
& 'C:/Program Files/PostgreSQL/18/bin/pg_ctl.exe' -D 'data/local/auth-test-pg' -l 'data/local/zhiyou-postgres.log' -o '-h 127.0.0.1 -p 55432' -w start
```

随后按前文命令启动后端。开发库文件与本地配置均未纳入 Git，不要删除 `data/local/auth-test-pg`。

自己的开发数据使用 PostgreSQL 工具备份，升级前先备份。`alembic downgrade base` 会删除账号与会话，只在明确可清空的测试库上用于迁移验证；本次未实现自动备份恢复脚本。

部署配置放在根目录 `deploy/`，项目级操作脚本放在根目录 `scripts/`。具体运行布局参见已有总体架构文档。
