from alembic import context

from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_session_factory
from app.modules.auth import models  # noqa: F401

config = context.config
target_metadata = Base.metadata
url = Settings.from_env().database_url

if context.is_offline_mode():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine, _ = create_session_factory(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
