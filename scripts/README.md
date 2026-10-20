# 项目级脚本

此目录放置开发启动、统一检查、数据库备份与恢复等项目级脚本。需要导入后端应用的种子脚本仍放在 `backend/app/scripts/`，避免维护重复入口。

## 启动项目

在项目根目录的 PowerShell 执行（使用项目虚拟环境，不依赖系统 Python 别名）：

```powershell
# 默认演示模式：后端提供已构建页面，访问 http://localhost:8000/#/login
.\backend\.venv\Scripts\python.exe .\scripts\start.py

# 开发模式：同时启动后端和 Vite，访问 http://localhost:5173/#/login
.\backend\.venv\Scripts\python.exe .\scripts\start.py --dev

# 只检查，不启动服务
.\backend\.venv\Scripts\python.exe .\scripts\start.py --check
```

在 `backend/` 目录运行时，使用 `.\.venv\Scripts\python.exe ..\scripts\start.py`，选项相同。脚本根据自身位置定位前后端目录，也支持从其他目录使用绝对路径调用。

启动前需安装两端依赖、配置现有 `backend/.env`，确保 PostgreSQL 已启动并完成迁移。默认模式需先在 `frontend/` 执行 `pnpm build`。开发模式直接运行本地 Vite，不需要运行 pnpm；Node 不在 PATH 时可用 `--node "实际的 node.exe 路径"` 或 `NODE_EXE` 指定。本机 Codex 自带 Node 可作为自动回退选项。

脚本检查数据库迁移及 8000（开发模式另含 5173）端口；占用时退出，不停止已有服务。启动失败或按 Ctrl+C 时只关闭本次创建的应用进程。它不自动安装依赖、重建数据库、执行迁移、初始化账号或停止 PostgreSQL。数据库地址与密码均从现有配置读取，不在脚本中写死。
