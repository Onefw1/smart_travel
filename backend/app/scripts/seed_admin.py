import os

from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import AppError
from app.db.session import create_session_factory
from app.modules.auth.schemas import Credentials
from app.modules.auth.service import AuthService


def main():
    settings = Settings.from_env()
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        raise SystemExit("请设置 ADMIN_USERNAME 和 ADMIN_PASSWORD；不会创建默认口令")
    try:
        command = Credentials(username=username, password=password)
    except ValidationError:
        raise SystemExit("管理员账号不符合用户名 3～20 字符或密码 8～64 字符规则") from None
    engine, factory = create_session_factory(settings.database_url)
    try:
        AuthService(factory).seed_admin(command)
    except AppError as exc:
        raise SystemExit(f"初始化未执行：{exc.message}；不会修改现有账号或重置密码") from None
    finally:
        engine.dispose()
    print("管理员账号已创建")


if __name__ == "__main__":
    main()
