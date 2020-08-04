import asyncio
from copy import deepcopy
from typing import Callable

import pytest

from migri import get_connection
from migri.elements import Query
from migri.interfaces import ConnectionBackend

TEST_DB_CREDS = {
    "db_user": "root",
    "db_pass": "passpass",
    "db_name": "migritestdb",
    "db_host": "127.0.0.1",
    "db_port": 3306,
}

CLEANUP_QUERY = """
SET FOREIGN_KEY_CHECKS = 0;
SET GROUP_CONCAT_MAX_LEN=32768;
SET @tables = NULL;
SELECT GROUP_CONCAT('`', table_name, '`') INTO @tables
  FROM information_schema.tables
  WHERE table_schema = (SELECT DATABASE());
SELECT IFNULL(@tables,'dummy') INTO @tables;

SET @tables = CONCAT('DROP TABLE IF EXISTS ', @tables);
PREPARE stmt FROM @tables;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
SET FOREIGN_KEY_CHECKS = 1;
"""


@pytest.fixture
def db_creds() -> dict:
    return deepcopy(TEST_DB_CREDS)


def _create_conn(db_name: str = None) -> ConnectionBackend:
    creds = deepcopy(TEST_DB_CREDS)

    # Use db name if provided, else grab from credentials
    if db_name:
        creds.pop("db_name")
    else:
        db_name = creds.pop("db_name")

    return get_connection(db_name, **creds)


@pytest.fixture
def get_mysql_conn() -> Callable:
    return _create_conn


@pytest.yield_fixture
async def mysql_conn_factory(get_mysql_conn):
    try:
        yield get_mysql_conn
    finally:
        conn = get_mysql_conn()

        async with conn:
            await conn.execute(Query(CLEANUP_QUERY))


async def execute(query: str):
    conn = _create_conn("mysql")

    async with conn:
        cursor = await conn.database.cursor()
        await cursor.execute(query)


def create_test_db_coroutine_factory():
    return execute(f"CREATE DATABASE {TEST_DB_CREDS['db_name']}")


def drop_test_db_coroutine_factory():
    return execute(f"DROP DATABASE {TEST_DB_CREDS['db_name']}")


def pytest_configure(config):
    asyncio.run(create_test_db_coroutine_factory())


def pytest_unconfigure(config):
    asyncio.run(drop_test_db_coroutine_factory())
