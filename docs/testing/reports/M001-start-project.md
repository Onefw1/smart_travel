# M001：启动脚本验证

日期：2026-10-20。测试对象为 `scripts/start.py`（按用户要求迁移到根目录），不是重新验收整个登录功能；代码对应本报告所在的启动脚本提交。

工作目录：`D:\Documents\lecture homework\travel`。使用既有 `backend/.venv/Scripts/python.exe`（Python 3.12.14、pytest 9.1.1），未新增依赖。

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend/tests/unit/test_start_script.py -q --tb=short --basetemp=data/local/start-script-move-pytest-temp -o cache_dir=data/local/start-script-pytest-cache
.\backend\.venv\Scripts\python.exe scripts/start.py --help
git diff --check
```

迁移后结果：15 passed，2 warnings；帮助输出正常；已有受版本控制文件的 diff 检查通过，仅有行尾转换提示。两条 warning 来自项目既有 TestClient 的 httpx/anyio 弃用提示。

覆盖：构建缺失、前端依赖缺失、Node 路径失效后的回退、显式 Node 路径错误、端口占用、只检查不启动、第二个进程启动失败时清理首个进程、Ctrl+C 清理、已退出进程不终止、真实测试子进程启动关闭、数据库版本正确/错误、连接异常不输出凭据。

迁移新增验证：从其他工作目录调用根目录脚本时，前后端定位正确；从其他目录实际执行新入口的 `--help` 成功。原入口与对应启动说明已移除，种子初始化脚本保持原位置。

首轮未指定工作区临时目录，2 个 tmp_path 夹具因系统临时目录权限失败，另 7 项通过；改用本任务专用目录后最终全部通过。

没有执行整个应用的现场启动，避免干扰主对话已有服务；未向开发或测试数据库写入数据。就绪轮询与完整前后端现场联调尚未在本次任务中验证。
