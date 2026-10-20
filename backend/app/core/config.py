import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url


@dataclass(frozen=True)
class Settings:
    database_url: str
    allowed_origins: tuple[str, ...] = ("http://localhost:5173", "http://localhost:8000")
    cookie_secure: bool = False

    def __post_init__(self):
        if make_url(self.database_url).drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL 必须使用 postgresql+psycopg")

    @classmethod
    def from_env(cls):
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        return cls(
            database_url=os.getenv("DATABASE_URL", "postgresql+psycopg://localhost/zhiyou"),
            allowed_origins=tuple(
                value.strip() for value in os.getenv(
                    "FRONTEND_ORIGIN", "http://localhost:5173,http://localhost:8000"
                ).split(",") if value.strip()
            ),
            cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        )
