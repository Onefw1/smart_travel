import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

START_SCRIPT = Path(__file__).resolve().parents[3] / "scripts/start.py"
spec = importlib.util.spec_from_file_location("project_start", START_SCRIPT)
start = importlib.util.module_from_spec(spec)
spec.loader.exec_module(start)


def test_repository_paths_do_not_depend_on_current_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    root = Path(__file__).resolve().parents[3]
    assert start.PROJECT_ROOT == root
    assert start.BACKEND == root / "backend"
    assert start.FRONTEND == root / "frontend"


def test_script_help_runs_from_another_directory(tmp_path):
    result = start.subprocess.run(
        [start.sys.executable, str(START_SCRIPT), "--help"],
        cwd=tmp_path, capture_output=True, timeout=5,
        creationflags=start.subprocess.CREATE_NO_WINDOW if start.os.name == "nt" else 0,
    )
    assert result.returncode == 0
    assert b"--dev" in result.stdout and b"--check" in result.stdout


def test_demo_requires_built_frontend(tmp_path, monkeypatch):
    monkeypatch.setattr(start, "FRONTEND", tmp_path)
    with pytest.raises(start.StartupError, match="pnpm build"):
        start.commands(False)
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/index.html").write_text("test", encoding="utf-8")
    command, cwd = start.commands(False)[0]
    assert command[:4] == [start.sys.executable, "-m", "uvicorn", "app.main:app"]
    assert cwd == start.BACKEND


def test_dev_requires_dependencies_and_uses_explicit_node(tmp_path, monkeypatch):
    monkeypatch.setattr(start, "FRONTEND", tmp_path)
    with pytest.raises(start.StartupError, match="pnpm install"):
        start.commands(True)
    vite = tmp_path / "node_modules/vite/bin/vite.js"
    vite.parent.mkdir(parents=True)
    vite.touch()
    find = Mock(return_value="C:/Program Files/Node/node.exe")
    monkeypatch.setattr(start, "find_node", find)
    result = start.commands(True, "custom-node")
    find.assert_called_once_with("custom-node")
    assert result[1][0][:2] == ["C:/Program Files/Node/node.exe", str(vite)]
    assert "--strictPort" in result[1][0]


def test_node_falls_back_after_broken_path_shim(monkeypatch):
    monkeypatch.delenv("NODE_EXE", raising=False)
    monkeypatch.setattr(start.shutil, "which", lambda _: "broken-node")
    execute = Mock(side_effect=[OSError("shim failed"), Mock(returncode=0, stdout=b"v24.19.0")])
    monkeypatch.setattr(start.subprocess, "run", execute)
    assert "codex-primary-runtime" in start.find_node()


def test_explicit_broken_node_is_reported(monkeypatch):
    monkeypatch.setattr(start.subprocess, "run", Mock(side_effect=OSError("missing")))
    with pytest.raises(start.StartupError, match="Node.js"):
        start.find_node("missing")


def test_busy_port_is_reported_without_process_changes(monkeypatch):
    listener = Mock()
    listener.__enter__ = Mock(return_value=listener)
    listener.__exit__ = Mock(return_value=False)
    listener.bind.side_effect = OSError("busy")
    monkeypatch.setattr(start.socket, "socket", Mock(return_value=listener))
    with pytest.raises(start.StartupError, match="8000"):
        start.check_port("127.0.0.1", 8000)


def test_check_only_does_not_spawn(monkeypatch):
    monkeypatch.setattr(start, "commands", lambda *_: [])
    monkeypatch.setattr(start, "check_database", Mock())
    monkeypatch.setattr(start, "check_port", Mock())
    spawn = Mock()
    monkeypatch.setattr(start, "spawn", spawn)
    assert start.main(["--check"]) == 0
    spawn.assert_not_called()


def test_failed_second_process_cleans_up_only_first(monkeypatch):
    first = Mock()
    first.poll.return_value = None
    monkeypatch.setattr(start, "commands", lambda *_: [(["backend"], Path(".")), (["frontend"], Path("."))])
    monkeypatch.setattr(start, "check_database", Mock())
    monkeypatch.setattr(start, "check_port", Mock())
    monkeypatch.setattr(start, "spawn", Mock(side_effect=[first, OSError("failed")]))
    assert start.main(["--dev"]) == 1
    first.terminate.assert_called_once()
    first.wait.assert_called_once()


def test_ctrl_c_stops_owned_process(monkeypatch):
    process = Mock()
    process.poll.return_value = None
    monkeypatch.setattr(start, "commands", lambda *_: [(["backend"], Path("."))])
    monkeypatch.setattr(start, "check_database", Mock())
    monkeypatch.setattr(start, "check_port", Mock())
    monkeypatch.setattr(start, "spawn", Mock(return_value=process))
    monkeypatch.setattr(start, "wait_ready", Mock(side_effect=KeyboardInterrupt))
    assert start.main([]) == 0
    process.terminate.assert_called_once()


def test_already_exited_process_is_not_terminated():
    process = Mock()
    process.poll.return_value = 0
    start.stop([process])
    process.terminate.assert_not_called()


def test_real_owned_subprocess_is_stopped():
    process = start.spawn([start.sys.executable, "-c", "import time; time.sleep(30)"], start.BACKEND)
    try:
        assert process.poll() is None
    finally:
        start.stop([process])
    assert process.poll() is not None


@pytest.mark.parametrize("revision,success", [("0001_auth", True), ("old_revision", False)])
def test_database_revision_is_checked_read_only(monkeypatch, revision, success):
    from app.db import session
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.scalar.return_value = revision
    monkeypatch.setattr(session, "create_session_factory", Mock(return_value=(engine, None)))
    if success:
        start.check_database()
    else:
        with pytest.raises(start.StartupError, match="迁移版本"):
            start.check_database()
    statement = connection.scalar.call_args.args[0]
    assert str(statement) == "SELECT version_num FROM alembic_version"
    engine.dispose.assert_called_once()


def test_database_failure_does_not_expose_connection_secret(monkeypatch):
    from app.core.config import Settings
    from app.db import session
    monkeypatch.setattr(Settings, "from_env", lambda: SimpleNamespace(database_url="private-connection"))
    monkeypatch.setattr(session, "create_session_factory", Mock(side_effect=RuntimeError("private-connection")))
    with pytest.raises(start.StartupError) as error:
        start.check_database()
    assert "private-connection" not in str(error.value)
