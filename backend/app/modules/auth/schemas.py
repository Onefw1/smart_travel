import re
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Credentials(StrictModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def valid_username(cls, value: str) -> str:
        value = value.strip()
        if not 3 <= len(value) <= 20 or not re.fullmatch(r"[\u3400-\u4dbf\u4e00-\u9fffA-Za-z0-9_]+", value):
            raise ValueError("用户名需为 3～20 个中文、英文字母、数字或下划线")
        return value

    @field_validator("password")
    @classmethod
    def valid_password(cls, value: str) -> str:
        if not 8 <= len(value) <= 64:
            raise ValueError("密码需为 8～64 个字符")
        return value


class EmptyBody(StrictModel):
    pass


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    username: str
    role: Literal["user", "admin"]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def utc_created_at(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)


class SessionView(BaseModel):
    user: UserView
    csrf_token: str
    expires_at: datetime

    @field_validator("expires_at")
    @classmethod
    def utc_expires_at(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)
