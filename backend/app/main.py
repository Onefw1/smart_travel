import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException

from app.core.config import Settings
from app.core.errors import AppError
from app.db.session import create_session_factory
from app.modules.auth.router import router
from app.modules.auth.service import AuthService

logger = logging.getLogger("zhiyou")


def error_response(request: Request, status: int, code: str, message: str, details=None):
    request_id = getattr(request.state, "request_id", str(uuid4()))
    return JSONResponse(status_code=status, content={"error": {
        "code": code, "message": message, "details": details or [], "request_id": request_id,
    }}, headers={"X-Request-ID": request_id, "Cache-Control": "no-store"})


def create_app(settings: Settings | None = None, *, serve_frontend: bool = True) -> FastAPI:
    settings = settings or Settings.from_env()
    engine, session_factory = create_session_factory(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()

    app = FastAPI(title="智游北京", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.auth_service = AuthService(session_factory)

    @app.middleware("http")
    async def protocol_guard(request: Request, call_next):
        request.state.request_id = str(uuid4())
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            if request.headers.get("origin") not in settings.allowed_origins:
                return error_response(request, 403, "ORIGIN_NOT_ALLOWED", "请求来源不被允许")
            bodyless_delete = request.method == "DELETE" and not await request.body()
            if not bodyless_delete and request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
                return error_response(request, 415, "UNSUPPORTED_MEDIA_TYPE", "请使用 application/json 请求")
        try:
            response = await call_next(request)
        except Exception as exc:
            # 仅记录分类与请求标识；不记录 SQL 参数、Cookie、密码或 CSRF token。
            logger.error("request_id=%s failure=%s", request.state.request_id, type(exc).__name__)
            return error_response(request, 500, "INTERNAL_ERROR", "服务暂时异常，请稍后重试")
        response.headers["X-Request-ID"] = request.state.request_id
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(AppError)
    def business_error(request, exc):
        return error_response(request, exc.status, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    def validation_error(request, exc):
        messages = {"missing": "此字段为必填项", "extra_forbidden": "不允许提交此字段",
                    "string_type": "此字段必须为文本", "json_invalid": "请求 JSON 格式无效"}
        details = []
        for error in exc.errors():
            message = messages.get(error["type"], "字段格式不符合要求")
            if error["type"] == "value_error":
                message = str(error.get("ctx", {}).get("error", message))
            details.append({"field": ".".join(str(p) for p in error["loc"] if p != "body"), "message": message})
        return error_response(request, 422, "VALIDATION_ERROR", "请求参数不符合要求", details)

    @app.exception_handler(SQLAlchemyError)
    def database_error(request, exc):
        logger.error("request_id=%s database_failure=%s", request.state.request_id, type(exc).__name__)
        return error_response(request, 503, "DEPENDENCY_UNAVAILABLE", "数据库暂不可用，请稍后重试")

    @app.exception_handler(HTTPException)
    def http_error(request, exc):
        return error_response(request, exc.status_code, "RESOURCE_NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR",
                              "资源不存在" if exc.status_code == 404 else "请求无法处理")

    app.include_router(router)

    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready():
        with engine.connect() as connection:
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != "0001_auth":
                raise AppError(503, "DEPENDENCY_UNAVAILABLE", "数据库迁移版本不匹配")
        return {"status": "ok", "migration": revision}

    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if serve_frontend and dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
