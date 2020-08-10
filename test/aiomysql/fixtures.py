from typing import Callable

import pytest

from migri.elements import Query
from test.aiomysql import create_db_conn

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
def get_mysql_conn() -> Callable:
    return create_db_conn


@pytest.yield_fixture
async def mysql_conn_factory(get_mysql_conn):
    try:
        yield get_mysql_conn
    finally:
        conn = get_mysql_conn()

        async with conn:
            await conn.execute(Query(CLEANUP_QUERY))
