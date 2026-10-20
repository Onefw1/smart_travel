from typing import Annotated

from fastapi import Depends, Request

from app.core.errors import AppError
from app.core.security import csrf_matches
from app.modules.auth.service import AuthService, Principal


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def optional_principal(request: Request, service: Annotated[AuthService, Depends(get_auth_service)]):
    return service.resolve(request.cookies.get("session_id"))


def require_authenticated(principal: Annotated[Principal | None, Depends(optional_principal)]) -> Principal:
    if principal is None:
        raise AppError(401, "AUTH_REQUIRED", "请先登录或重新登录")
    return principal


def require_csrf(request: Request, principal: Principal):
    if not csrf_matches(request.headers.get("X-CSRF-Token"), principal.csrf_token):
        raise AppError(403, "CSRF_INVALID", "安全校验失败，请刷新页面后重试")


def require_authenticated_write(request: Request, principal: Annotated[Principal, Depends(require_authenticated)]):
    require_csrf(request, principal)
    return principal


def require_role(role: str):
    def dependency(request: Request, principal: Annotated[Principal, Depends(require_authenticated)]):
        if principal.role != role:
            raise AppError(403, "FORBIDDEN", "当前账号无权执行此操作")
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            require_csrf(request, principal)
        return principal
    return dependency


require_user = require_role("user")
require_admin = require_role("admin")
