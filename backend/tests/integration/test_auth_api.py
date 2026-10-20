from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import base64

import pytest
from fastapi import Depends
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.core.errors import AppError
from app.core.security import token_digest
from app.modules.auth.dependencies import require_admin, require_authenticated_write, require_user
from app.modules.auth.models import AuthSession, User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import Credentials

pytestmark = pytest.mark.integration
AUTH = "/api/v1/auth"
CREDS = {"username": "旅行Test_01", "password": "  test-password  "}


def register_and_login(client, origin, credentials=None):
    credentials = credentials or CREDS
    assert client.post(f"{AUTH}/register", json=credentials, headers=origin).status_code == 201
    result = client.post(f"{AUTH}/login", json=credentials, headers=origin)
    assert result.status_code == 200
    return result


def test_register_does_not_login_and_stores_argon2id(client, app, origin):
    result = client.post(f"{AUTH}/register", json={**CREDS, "username": "  旅行Test_01  "}, headers=origin)
    assert result.status_code == 201
    user = result.json()
    assert set(user) == {"id", "username", "role", "created_at"}
    assert user["username"] == CREDS["username"]
    assert user["role"] == "user"
    assert "session_id" not in client.cookies
    assert client.get(f"{AUTH}/me").status_code == 401
    with app.state.auth_service.session_factory() as db:
        stored = db.scalar(select(User))
        assert stored.password_hash.startswith("$argon2id$")
        assert stored.password_hash != CREDS["password"]
        assert stored.username_normalized == "旅行test_01"


@pytest.mark.parametrize("name", ["旅行TEST_01", "  旅行test_01  "])
def test_duplicate_username(client, origin, name):
    client.post(f"{AUTH}/register", json=CREDS, headers=origin)
    result = client.post(f"{AUTH}/register", json={**CREDS, "username": name}, headers=origin)
    assert result.status_code == 409
    assert result.json()["error"]["code"] == "USERNAME_TAKEN"


def test_concurrent_registration_database_unique_constraint(app):
    command = Credentials(**CREDS)
    def attempt():
        try:
            app.state.auth_service.register(command)
            return 201
        except AppError as error:
            return error.status
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: attempt(), range(2))) == [201, 409]
    with app.state.auth_service.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1


@pytest.mark.parametrize("payload,field", [
    ({**CREDS, "role": "admin"}, "role"), ({**CREDS, "username": "a@b"}, "username"),
    ({**CREDS, "password": "short"}, "password"), ({"username": "tester"}, "password"),
    ({**CREDS, "username": True}, "username"), ({**CREDS, "password": 12345678}, "password"),
    ({**CREDS, "user_id": "spoofed"}, "user_id"),
])
def test_validation_error_contract(client, app, origin, payload, field):
    result = client.post(f"{AUTH}/register", json=payload, headers=origin)
    assert result.status_code == 422
    error = result.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["request_id"] == result.headers["X-Request-ID"]
    assert any(detail["field"] == field for detail in error["details"])
    assert "password_hash" not in result.text
    with app.state.auth_service.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 0


def test_login_cookie_and_digest_and_identity(client, app, origin):
    now = datetime.now(UTC)
    app.state.auth_service.clock = lambda: now
    result = register_and_login(client, origin)
    view = result.json()
    cookie = result.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/" in cookie
    assert "Max-Age=28800" in cookie and "Secure" not in cookie and "Domain=" not in cookie
    assert result.headers["cache-control"] == "no-store"
    raw = client.cookies["session_id"]
    assert len(base64.urlsafe_b64decode(raw + "=")) == 32
    assert set(view) == {"user", "csrf_token", "expires_at"}
    with app.state.auth_service.session_factory() as db:
        stored = db.scalar(select(AuthSession))
        assert stored.token_hash == token_digest(raw)
        assert stored.expires_at - stored.created_at == timedelta(hours=8)
    app.state.auth_service.clock = lambda: now + timedelta(hours=2)
    assert client.get(f"{AUTH}/me").json() == view
    result = client.post(f"{AUTH}/login", json={**CREDS, "username": "  旅行TEST_01  "}, headers=origin)
    assert result.status_code == 200
    assert client.cookies["session_id"] != raw
    assert result.json()["csrf_token"] != view["csrf_token"]


def test_wrong_credentials_same_message_and_no_session(client, app, origin):
    client.post(f"{AUTH}/register", json=CREDS, headers=origin)
    errors = []
    for credentials in [{**CREDS, "password": "bad-password"}, {**CREDS, "username": "不存在的用户"},
                        {**CREDS, "password": CREDS["password"].strip()}]:
        result = client.post(f"{AUTH}/login", json=credentials, headers=origin)
        assert result.status_code == 401
        assert "set-cookie" not in result.headers
        errors.append((result.json()["error"]["code"], result.json()["error"]["message"]))
    assert len(set(errors)) == 1
    assert errors[0] == ("INVALID_CREDENTIALS", "用户名或密码错误")
    with app.state.auth_service.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_expiry_at_exact_eight_hours(client, app, origin):
    now = datetime.now(UTC)
    app.state.auth_service.clock = lambda: now
    register_and_login(client, origin)
    app.state.auth_service.clock = lambda: now + timedelta(hours=8) - timedelta(microseconds=1)
    assert client.get(f"{AUTH}/me").status_code == 200
    app.state.auth_service.clock = lambda: now + timedelta(hours=8)
    assert client.get(f"{AUTH}/me").status_code == 401
    # 已过期会话退出无需 CSRF，仍要求 Origin 和 JSON。
    assert client.post(f"{AUTH}/logout", json={}, headers=origin).status_code == 204


def test_logout_revokes_current_session_only(client, app, origin):
    first = register_and_login(client, origin)
    first_token = client.cookies["session_id"]
    second = client.post(f"{AUTH}/login", json=CREDS, headers=origin)
    second_token = client.cookies["session_id"]
    result = client.post(f"{AUTH}/logout", json={}, headers={**origin, "X-CSRF-Token": second.json()["csrf_token"]})
    assert result.status_code == 204 and result.content == b""
    assert "Max-Age=0" in result.headers["set-cookie"]
    assert "session_id" not in client.cookies
    assert app.state.auth_service.resolve(second_token) is None
    assert app.state.auth_service.resolve(first_token) is not None
    assert client.get(f"{AUTH}/me").status_code == 401
    assert client.post(f"{AUTH}/logout", json={}, headers=origin).status_code == 204
    assert first.json()["csrf_token"] != second.json()["csrf_token"]


@pytest.mark.parametrize("csrf", [None, "forged", "伪造令牌"])
def test_logout_csrf_rejected_without_revocation(client, origin, csrf):
    register_and_login(client, origin)
    headers = dict(origin)
    if csrf is not None:
        # HTTP 头按协议为 ASCII；UTF-8 字节模拟非标准攻击输入。
        headers["X-CSRF-Token"] = csrf.encode() if csrf == "伪造令牌" else csrf
    result = client.post(f"{AUTH}/logout", json={}, headers=headers)
    assert result.status_code == 403
    assert result.json()["error"]["code"] == "CSRF_INVALID"
    assert client.get(f"{AUTH}/me").status_code == 200


def test_csrf_is_bound_to_session(client, origin):
    first = register_and_login(client, origin)
    client.post(f"{AUTH}/login", json=CREDS, headers=origin)
    result = client.post(f"{AUTH}/logout", json={}, headers={**origin, "X-CSRF-Token": first.json()["csrf_token"]})
    assert result.status_code == 403


@pytest.mark.parametrize("path", ["register", "login", "logout"])
@pytest.mark.parametrize("origin", [None, "null", "https://evil.example", "http://localhost:5173.evil.example"])
def test_origin_exact_allowlist(client, path, origin):
    headers = {} if origin is None else {"Origin": origin}
    response = client.post(f"{AUTH}/{path}", json={}, headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ORIGIN_NOT_ALLOWED"


@pytest.mark.parametrize("content_type", [None, "text/plain", "application/x-www-form-urlencoded"])
def test_json_media_type_required(client, origin, content_type):
    headers = dict(origin)
    if content_type:
        headers["Content-Type"] = content_type
    assert client.post(f"{AUTH}/logout", content="{}", headers=headers).status_code == 415


def test_logout_requires_empty_object_and_json_malformed(client, origin):
    for payload in [{"user_id": "fake"}, [], None]:
        result = client.post(f"{AUTH}/logout", content=__import__('json').dumps(payload), headers={**origin, "Content-Type": "application/json"})
        assert result.status_code == 422
    assert client.post(f"{AUTH}/login", content="{", headers={**origin, "Content-Type": "application/json"}).status_code == 422


def test_invalid_cookie_and_error_contract(client):
    client.cookies.set("session_id", "forged-token")
    response = client.get(f"{AUTH}/me")
    assert response.status_code == 401
    error = response.json()["error"]
    assert error["details"] == []
    assert error["request_id"] == response.headers["x-request-id"]


def test_server_role_dependencies_and_write_csrf(client, app, origin):
    @app.get("/test/admin")
    def admin_route(principal=Depends(require_admin)):
        return {"role": principal.role}

    @app.post("/test/user")
    def user_route(principal=Depends(require_user)):
        return {"user_id": str(principal.user_id)}

    @app.post("/test/authenticated")
    def authenticated_route(principal=Depends(require_authenticated_write)):
        return {"user_id": str(principal.user_id)}

    assert client.get("/test/admin").status_code == 401
    login = register_and_login(client, origin).json()
    assert client.get("/test/admin").status_code == 403
    assert client.post("/test/user", json={}, headers=origin).status_code == 403
    valid_headers = {**origin, "X-CSRF-Token": login["csrf_token"]}
    assert client.post("/test/user", json={}, headers=valid_headers).json()["user_id"] == login["user"]["id"]
    assert client.post("/test/authenticated", json={}, headers=valid_headers).status_code == 200
    app.state.auth_service.seed_admin(Credentials(username="测试管理员", password="test-admin-only"))
    admin = client.post(f"{AUTH}/login", json={"username": "测试管理员", "password": "test-admin-only"}, headers=origin).json()
    assert client.get("/test/admin").status_code == 200
    assert client.post("/test/user", json={}, headers={**origin, "X-CSRF-Token": admin["csrf_token"]}).status_code == 403
    # /test/* 路由仅在此测试内注册，生产应用没有伪造业务接口。


def test_database_session_constraints_and_transaction_rollback(client, app, origin):
    register_and_login(client, origin)
    with app.state.auth_service.session_factory() as db:
        session = db.scalar(select(AuthSession))
        old_hash, session_id = session.token_hash, session.id
    with pytest.raises(IntegrityError):
        with app.state.engine.begin() as connection:
            connection.execute(text("UPDATE sessions SET token_hash = :value WHERE id = :id"), {"value": b"short", "id": session_id})
    with app.state.auth_service.session_factory() as db:
        assert db.get(AuthSession, session_id).token_hash == old_hash
    assert client.get(f"{AUTH}/me").status_code == 200


def test_seed_cannot_promote_or_reset_existing_account(client, app, origin):
    client.post(f"{AUTH}/register", json=CREDS, headers=origin)
    with pytest.raises(AppError) as error:
        app.state.auth_service.seed_admin(Credentials(**CREDS))
    assert error.value.code == "USERNAME_TAKEN"
    assert client.post(f"{AUTH}/login", json=CREDS, headers=origin).json()["user"]["role"] == "user"


def test_health_and_dependency_failure(client, app, origin, monkeypatch):
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200
    def unavailable(*args, **kwargs):
        raise OperationalError("sensitive sql", {}, Exception("sensitive connection"))
    monkeypatch.setattr(app.state.auth_service, "login", unavailable)
    result = client.post(f"{AUTH}/login", json=CREDS, headers=origin)
    assert result.status_code == 503
    assert "sensitive" not in result.text
    assert result.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"


@pytest.mark.parametrize("operation", ["register", "login"])
def test_failure_after_flush_rolls_back_transaction(client, app, origin, monkeypatch, operation):
    if operation == "login":
        assert client.post(f"{AUTH}/register", json=CREDS, headers=origin).status_code == 201
    original_add = AuthRepository.add
    def fail_after_flush(repository, entity):
        original_add(repository, entity)
        raise RuntimeError("internal failure must not leak")
    monkeypatch.setattr(AuthRepository, "add", fail_after_flush)
    response = client.post(f"{AUTH}/{operation}", json=CREDS, headers=origin)
    assert response.status_code == 500
    assert "internal failure" not in response.text
    assert "set-cookie" not in response.headers
    with app.state.auth_service.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(AuthSession)) == 0
        assert db.scalar(select(func.count()).select_from(User)) == (1 if operation == "login" else 0)
