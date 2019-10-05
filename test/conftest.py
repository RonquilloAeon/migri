import asyncio
import asyncpg
import pytest
from contextlib import asynccontextmanager


@asynccontextmanager
async def db_conn(dbname='migritestdb'):
    try:
        conn = await asyncpg.connect(f'postgresql://migrator:passpass@localhost/{dbname}')
        yield conn
    finally:
        await conn.close()


@pytest.yield_fixture
async def conn():
    async with db_conn() as conn:
        yield conn


async def execute(command: str, dbname: str) -> str:
    async with db_conn(dbname) as conn:
        return await conn.execute(command)


def pytest_configure(config):
    asyncio.run(execute('CREATE DATABASE migritestdb', 'postgres'))


def pytest_unconfigure(config):
    asyncio.run(execute('DROP DATABASE migritestdb', 'postgres'))
