from pathlib import Path

import pytest

from migri import get_connection

DB_NAME = "test.db"


@pytest.fixture
def get_sqlite_conn():
    def _wrapped():
        return get_connection(DB_NAME)

    return _wrapped


@pytest.yield_fixture
async def sqlite_conn_factory(get_sqlite_conn):
    db = Path(DB_NAME)

    try:
        yield get_sqlite_conn
    finally:
        if db.exists():
            db.unlink()
