from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError

from app.core.clock import now_utc
from app.core.errors import AppError
from app.core.security import SESSION_TTL_SECONDS, hash_password, new_token, token_digest, verify_password
from app.db.uow import UnitOfWork
from app.modules.auth.models import AuthSession, User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import Credentials, SessionView, UserView


@dataclass(frozen=True)
class Principal:
    session_id: UUID
    user: UserView
    csrf_token: str
    expires_at: datetime

    @property
    def user_id(self):
        return self.user.id

    @property
    def role(self):
        return self.user.role

    def view(self):
        return SessionView(user=self.user, csrf_token=self.csrf_token, expires_at=self.expires_at)


class AuthService:
    def __init__(self, session_factory, clock=now_utc):
        self.session_factory = session_factory
        self.clock = clock

    def register(self, command: Credentials) -> UserView:
        return self._create_account(command, "user")

    def seed_admin(self, command: Credentials) -> UserView:
        # 仅供独立命令使用，公开注册不能选择角色，也不会提升现有普通账号。
        return self._create_account(command, "admin")

    def _create_account(self, command: Credentials, role: str) -> UserView:
        user = User(
            id=uuid4(), username=command.username,
            username_normalized=command.username.lower(),
            password_hash=hash_password(command.password), role=role, created_at=self.clock(),
        )
        try:
            with UnitOfWork(self.session_factory) as uow:
                AuthRepository(uow.session).add(user)
                view = UserView.model_validate(user)
        except IntegrityError as exc:
            if getattr(getattr(exc.orig, "diag", None), "constraint_name", None) == "uq_users_username_normalized":
                raise AppError(409, "USERNAME_TAKEN", "用户名已被使用", [
                    {"field": "username", "message": "用户名已被使用"}
                ]) from None
            raise
        return view

    def login(self, command: Credentials) -> tuple[SessionView, str]:
        now = self.clock()
        raw_token = new_token()
        with UnitOfWork(self.session_factory) as uow:
            repository = AuthRepository(uow.session)
            user = repository.find_user(command.username.lower())
            if not verify_password(command.password, user.password_hash if user else None):
                raise AppError(401, "INVALID_CREDENTIALS", "用户名或密码错误")
            session = AuthSession(
                id=uuid4(), user_id=user.id, token_hash=token_digest(raw_token),
                csrf_token=new_token(), created_at=now,
                expires_at=now + timedelta(seconds=SESSION_TTL_SECONDS),
            )
            repository.add(session)
            view = SessionView(user=UserView.model_validate(user), csrf_token=session.csrf_token, expires_at=session.expires_at)
        return view, raw_token

    def resolve(self, raw_token: str | None) -> Principal | None:
        if not raw_token or len(raw_token) > 128:
            return None
        # 身份只读事务在业务服务打开写事务前关闭。
        with self.session_factory() as session:
            result = AuthRepository(session).resolve(token_digest(raw_token), self.clock())
            if result is None:
                return None
            record, user = result
            return Principal(record.id, UserView.model_validate(user), record.csrf_token, record.expires_at)

    def logout(self, principal: Principal):
        with UnitOfWork(self.session_factory) as uow:
            AuthRepository(uow.session).delete_session(principal.session_id)
