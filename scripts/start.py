"""从任意工作目录启动项目；默认演示模式，--dev 启动前后端开发服务。"""

import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND = PROJECT_ROOT / "backend"
FRONTEND = PROJECT_ROOT / "frontend"


class StartupError(Exception):
    pass


def find_node(explicit: str | None = None) -> str:
    candidates = [explicit] if explicit else [
        os.environ.get("NODE_EXE"),
        shutil.which("node"),
        str(Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            result = subprocess.run(
                [candidate, "--version"], capture_output=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if result.returncode == 0 and result.stdout.startswith(b"v"):
                return candidate
        except (OSError, subprocess.TimeoutExpired):
            continue
    raise StartupError("未找到可运行的 Node.js；请设置 NODE_EXE 或使用 --node 指定路径")


def check_port(host: str, port: int):
    try:
        with socket.socket(socket.AF_INET6 if ":" in host else socket.AF_INET) as listener:
            if os.name == "nt":
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            listener.bind((host, port))
    except OSError:
        raise StartupError(f"端口 {port} 不可用；请使用已有服务或自行停止占用进程后重试") from None


def check_database():
    # 直接执行此文件时也能导入 backend/app；数据库仅做只读检查。
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    try:
        from sqlalchemy import text
        from app.core.config import Settings
        from app.db.session import create_session_factory
        import uvicorn  # noqa: F401
    except ImportError:
        raise StartupError("缺少后端依赖；请使用 backend/.venv 中的 Python，并按 backend/README.md 安装依赖") from None
    engine = None
    try:
        settings = Settings.from_env()
        engine, _ = create_session_factory(settings.database_url)
        with engine.connect() as connection:
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        if revision != "0001_auth":
            raise StartupError("数据库迁移版本不匹配；请先在 backend 目录执行 python -m alembic upgrade head")
    except StartupError:
        raise
    except Exception:
        raise StartupError("数据库检查失败；请确认 PostgreSQL 已启动、backend/.env 连接正确且已执行迁移") from None
    finally:
        if engine is not None:
            engine.dispose()


def commands(dev: bool, node: str | None = None):
    backend = ([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"], BACKEND)
    if not dev:
        if not (FRONTEND / "dist/index.html").is_file():
            raise StartupError("缺少前端构建产物；请先在 frontend 目录执行 pnpm build，或使用 --dev")
        return [backend]
    vite = FRONTEND / "node_modules/vite/bin/vite.js"
    if not vite.is_file():
        raise StartupError("缺少前端依赖；请先在 frontend 目录执行 pnpm install --frozen-lockfile")
    return [backend, ([find_node(node), str(vite), "--host", "localhost", "--port", "5173", "--strictPort"], FRONTEND)]


def spawn(command: list[str], cwd: Path):
    options = {"cwd": cwd}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    return subprocess.Popen(command, **options)


def wait_ready(processes, urls, timeout: float = 20):
    opener = build_opener(ProxyHandler({}))
    pending = set(urls)
    deadline = time.monotonic() + timeout
    while pending and time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            raise StartupError("启动进程已退出，请检查上方输出")
        for url in tuple(pending):
            try:
                with opener.open(url, timeout=1) as response:
                    if response.status == 200:
                        pending.remove(url)
            except (OSError, URLError):
                pass
        if pending:
            time.sleep(.2)
    if pending:
        raise StartupError("服务未在预期时间内就绪，请检查上方输出")


def stop(processes):
    # 只操作当前调用创建的 Popen 实例，不按端口或名称批量结束进程。
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
    for process in reversed(processes):
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="启动智游北京（读取现有 backend/.env，不修改数据库或账号）")
    parser.add_argument("--dev", action="store_true", help="同时启动前端开发服务，访问 5173；默认演示模式访问 8000")
    parser.add_argument("--check", action="store_true", help="只检查依赖、构建产物、数据库和端口，不启动服务")
    parser.add_argument("--node", help="开发模式使用的 Node.js 可执行文件路径")
    args = parser.parse_args(argv)
    processes = []
    try:
        targets = commands(args.dev, args.node)
        check_database()
        check_port("127.0.0.1", 8000)
        if args.dev:
            check_port("127.0.0.1", 5173)
            if socket.has_ipv6:
                check_port("::1", 5173)
        if args.check:
            print("启动检查通过；没有启动进程或修改数据库。")
            return 0
        for command, cwd in targets:
            processes.append(spawn(command, cwd))
        urls = ["http://localhost:8000/health/ready"]
        if args.dev:
            urls.append("http://localhost:5173")
        wait_ready(processes, urls)
        port = 5173 if args.dev else 8000
        print(f"项目已就绪：http://localhost:{port}/#/login", flush=True)
        print("按 Ctrl+C 退出；只关闭本脚本启动的应用进程，保留数据库。", flush=True)
        while True:
            if any(process.poll() is not None for process in processes):
                raise StartupError("应用进程已退出，正在关闭本次启动的其他进程")
            time.sleep(.5)
    except KeyboardInterrupt:
        print("\n正在关闭本次启动的服务…")
        return 0
    except (StartupError, OSError) as error:
        print(f"启动失败：{error}", file=sys.stderr)
        return 1
    finally:
        stop(processes)


if __name__ == "__main__":
    raise SystemExit(main())
