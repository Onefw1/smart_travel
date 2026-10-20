from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_session_factory(database_url: str):
    engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
    return engine, sessionmaker(engine, expire_on_commit=False)
