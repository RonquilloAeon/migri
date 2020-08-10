import asyncio
from copy import deepcopy

from migri import get_connection
from migri.interfaces import ConnectionBackend
from test.constants import MYSQL


def create_db_conn(db_name: str = None) -> ConnectionBackend:
    creds = deepcopy(MYSQL)

    # Use db name if provided, else grab from credentials
    if db_name:
        creds.pop("db_name")
    else:
        db_name = creds.pop("db_name")

    return get_connection(db_name, **creds)


async def execute(query: str):
    conn = create_db_conn("mysql")

    async with conn:
        cursor = await conn.database.cursor()
        await cursor.execute(query)


def create_test_db_coroutine_factory():
    return execute(f"CREATE DATABASE {MYSQL['db_name']}")


def drop_test_db_coroutine_factory():
    return execute(f"DROP DATABASE {MYSQL['db_name']}")


def configure(config):
    asyncio.run(create_test_db_coroutine_factory())


def unconfigure(config):
    asyncio.run(drop_test_db_coroutine_factory())
