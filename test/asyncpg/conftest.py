import asyncio
from contextlib import asynccontextmanager
from typing import Generator

import asyncpg
import pytest
from asyncpg.exceptions import DuplicateDatabaseError

from migri import get_connection
from migri.elements import Query
from test.constants import POSTGRESQL


@asynccontextmanager
async def db_conn(
    db_user: str, db_pass: str, db_name: str, db_host: str, db_port: str
) -> Generator[asyncpg.Connection, None, None]:
    conn = await asyncpg.connect(
        f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    )

    try:
        yield conn
    finally:
        await conn.close()


@pytest.yield_fixture
async def conn(
    postgresql_connection_details,
) -> Generator[asyncpg.connection.Connection, None, None]:
    async with db_conn(**postgresql_connection_details) as conn:
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


async def execute(command: str, dbname: str) -> str:
    async with db_conn(**{**POSTGRESQL, "db_name": dbname}) as conn:
        return await conn.execute(command)


def create_test_db_coroutine_factory():
    return execute("CREATE DATABASE migritestdb", "postgres")


def drop_test_db_coroutine_factory():
    return execute("DROP DATABASE migritestdb", "postgres")


def pytest_configure(config):
    try:
        asyncio.run(create_test_db_coroutine_factory())
    except DuplicateDatabaseError:
        asyncio.run(drop_test_db_coroutine_factory())
        asyncio.run(create_test_db_coroutine_factory())


def pytest_unconfigure(config):
    asyncio.run(drop_test_db_coroutine_factory())
