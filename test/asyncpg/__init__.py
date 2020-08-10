import asyncio
from contextlib import asynccontextmanager
from typing import Generator

import asyncpg
from asyncpg.exceptions import DuplicateDatabaseError, InvalidCatalogNameError

from test.constants import POSTGRESQL


@asynccontextmanager
async def postgresql_db_conn(
    db_user: str, db_pass: str, db_name: str, db_host: str, db_port: str
) -> Generator[asyncpg.Connection, None, None]:
    conn = await asyncpg.connect(
        f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    )

    try:
        yield conn
    finally:
        await conn.close()


async def execute(command: str, dbname: str) -> str:
    async with postgresql_db_conn(**{**POSTGRESQL, "db_name": dbname}) as conn:
        return await conn.execute(command)


def create_test_db_coroutine_factory():
    return execute("CREATE DATABASE migritestdb", "postgres")


def drop_test_db_coroutine_factory():
    return execute("DROP DATABASE migritestdb", "postgres")


def configure(config):
    try:
        asyncio.run(create_test_db_coroutine_factory())
    except DuplicateDatabaseError:
        asyncio.run(drop_test_db_coroutine_factory())
        asyncio.run(create_test_db_coroutine_factory())


def unconfigure(config):
    try:
        asyncio.run(drop_test_db_coroutine_factory())
    except InvalidCatalogNameError:
        # DB has already been deleted, all good
        pass
