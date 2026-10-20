from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select

from app.modules.auth.models import AuthSession, User


class AuthRepository:
    def __init__(self, session):
        self.session = session

    def find_user(self, normalized: str):
        return self.session.scalar(select(User).where(User.username_normalized == normalized))

    def add(self, entity):
        self.session.add(entity)
        self.session.flush()

    def resolve(self, digest: bytes, now: datetime):
        return self.session.execute(
            select(AuthSession, User).join(User, User.id == AuthSession.user_id)
            .where(AuthSession.token_hash == digest, AuthSession.expires_at > now)
        ).first()

    def delete_session(self, session_id: UUID):
        self.session.execute(delete(AuthSession).where(AuthSession.id == session_id))
