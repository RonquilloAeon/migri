from pathlib import Path

import pytest

from migri import get_connection


@pytest.fixture
def get_sqlite_conn(sqlite_connection_details):
    def _wrapped():
        return get_connection(sqlite_connection_details["db_name"])

    return _wrapped


@pytest.yield_fixture
async def sqlite_conn_factory(get_sqlite_conn, sqlite_connection_details):
    db = Path(sqlite_connection_details["db_name"])

    try:
        yield get_sqlite_conn
    finally:
        if db.exists():
            db.unlink()
