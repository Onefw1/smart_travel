class UnitOfWork:
    """事务边界由 Service 使用；仓储只能 flush，不能 commit。"""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.transaction = self.session.begin()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return self.transaction.__exit__(exc_type, exc_value, traceback)
        finally:
            self.session.close()
