from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.core.security import SESSION_TTL_SECONDS
from app.modules.auth.dependencies import get_auth_service, optional_principal, require_authenticated, require_csrf
from app.modules.auth.schemas import Credentials, EmptyBody, SessionView, UserView
from app.modules.auth.service import AuthService, Principal

router = APIRouter(prefix="/api/v1/auth", tags=["账号"])
Service = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/register", response_model=UserView, status_code=201)
def register(command: Credentials, service: Service):
    return service.register(command)


@router.post("/login", response_model=SessionView)
def login(command: Credentials, response: Response, request: Request, service: Service):
    view, token = service.login(command)
    response.set_cookie(
        "session_id", token, max_age=SESSION_TTL_SECONDS, expires=view.expires_at,
        httponly=True, secure=request.app.state.settings.cookie_secure, samesite="lax", path="/",
    )
    return view


@router.get("/me", response_model=SessionView)
def me(principal: Annotated[Principal, Depends(require_authenticated)]):
    return principal.view()


@router.post("/logout", status_code=204)
def logout(body: EmptyBody, request: Request, service: Service,
           principal: Annotated[Principal | None, Depends(optional_principal)]):
    if principal is not None:
        require_csrf(request, principal)
        service.logout(principal)
    response = Response(status_code=204)
    response.delete_cookie("session_id", path="/", httponly=True,
                           secure=request.app.state.settings.cookie_secure, samesite="lax")
    return response
