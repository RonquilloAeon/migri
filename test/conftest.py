import asyncio
import asyncpg
import pytest
from contextlib import asynccontextmanager
from typing import Generator

from migri import run_initialization

TEST_DB_CREDS = {
    'db_user': 'migrator',
    'db_pass': 'passpass',
    'db_name': 'migritestdb',
    'db_host': 'localhost',
    'db_port': '5432',
}


@asynccontextmanager
async def db_conn(
    db_user: str,
    db_pass: str,
    db_name: str,
    db_host: str,
    db_port: str
) -> Generator[asyncpg.Connection, None, None]:
    conn = await asyncpg.connect(f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}')

    try:
        yield conn
    finally:
        await conn.close()


@pytest.yield_fixture
async def conn() -> Generator[asyncpg.connection.Connection, None, None]:
    async with db_conn(**TEST_DB_CREDS) as conn:
        tr = conn.transaction()
        await tr.start()
        yield conn

        if not conn.is_closed():
            await tr.rollback()


async def execute(command: str, dbname: str) -> str:
    async with db_conn(**{**TEST_DB_CREDS, 'db_name': dbname}) as conn:
        return await conn.execute(command)


def pytest_configure(config):
    asyncio.run(execute('CREATE DATABASE migritestdb', 'postgres'))
    asyncio.run(run_initialization(**TEST_DB_CREDS))


def pytest_unconfigure(config):
    asyncio.run(execute('DROP DATABASE migritestdb', 'postgres'))
