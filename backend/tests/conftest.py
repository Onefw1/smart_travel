import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url

from app.core.config import Settings
from app.db.session import create_session_factory
from app.main import create_app


@pytest.fixture(scope="session")
def database_url():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("未配置 TEST_DATABASE_URL，PostgreSQL 集成测试未运行")
    parsed = make_url(url)
    if parsed.drivername != "postgresql+psycopg" or not (parsed.database or "").endswith("_test"):
        pytest.fail("TEST_DATABASE_URL 必须为 PostgreSQL 且数据库名以 _test 结尾")
    development = make_url(Settings.from_env().database_url)
    if (parsed.host, parsed.port, parsed.database) == (development.host, development.port, development.database):
        pytest.fail("测试库不能与开发库相同")
    engine, _ = create_session_factory(url)
    with engine.connect() as connection:
        unexpected = set(inspect(connection).get_table_names()) - {"users", "sessions", "alembic_version"}
        if unexpected:
            pytest.fail("测试库存在本功能以外的数据表，请使用独立空测试库")
    engine.dispose()
    original = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        command.upgrade(Config(str(Path(__file__).parents[1] / "alembic.ini")), "head")
    finally:
        if original is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original
    return url


@pytest.fixture
def app(database_url):
    application = create_app(Settings(database_url=database_url), serve_frontend=False)
    with application.state.engine.begin() as connection:
        connection.execute(text("DELETE FROM sessions"))
        connection.execute(text("DELETE FROM users"))
    yield application
    application.state.engine.dispose()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def origin():
    return {"Origin": "http://localhost:5173"}
