from typing import Generator

import asyncpg
import pytest

from migri import get_connection
from migri.elements import Query
from test.asyncpg import postgresql_db_conn


@pytest.yield_fixture
async def postgresql_db(
    postgresql_connection_details,
) -> Generator[asyncpg.connection.Connection, None, None]:
    async with postgresql_db_conn(**postgresql_connection_details) as conn:
        tr = conn.transaction()
        await tr.start()
        yield conn

        if not conn.is_closed():
            await tr.rollback()


@pytest.fixture
def get_postgresql_conn(postgresql_connection_details):
    def _wrapped():
        return get_connection(**postgresql_connection_details)

    return _wrapped


@pytest.yield_fixture
async def postgresql_conn_factory(get_postgresql_conn):
    try:
        yield get_postgresql_conn
    finally:
        conn = get_postgresql_conn()

        async with conn:
            await conn.execute(Query("DROP SCHEMA public CASCADE"))
            await conn.execute(Query("CREATE SCHEMA public"))
