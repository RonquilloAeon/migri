import pytest

from test.constants import MIGRATIONS_BASE, MYSQL, POSTGRESQL, SQLITE

pytest_plugins = [
    "test.aiomysql.fixtures",
    "test.aiosqlite.fixtures",
    "test.asyncpg.fixtures",
]


@pytest.fixture
def migrations() -> dict:
    return {
        # OK
        "mysql_a": f"{MIGRATIONS_BASE}/mysql_a",
        # OK
        "postgresql_a": f"{MIGRATIONS_BASE}/postgresql_a",
        "postgresql_b": f"{MIGRATIONS_BASE}/postgresql_b",
        # Empty directory
        "postgresql_c": f"{MIGRATIONS_BASE}/postgresql_c",
        # Has an empty SQL migration file
        "postgresql_d": f"{MIGRATIONS_BASE}/postgresql_d",
        # Has an empty Python migration file
        "postgresql_e": f"{MIGRATIONS_BASE}/postgresql_e",
        # Python migration file has a sync migrate() function
        "postgresql_f": f"{MIGRATIONS_BASE}/postgresql_f",
        # OK
        "sqlite_a": f"{MIGRATIONS_BASE}/sqlite_a",
    }


@pytest.fixture
def mysql_connection_details() -> dict:
    return MYSQL


@pytest.fixture
def postgresql_connection_details() -> dict:
    return POSTGRESQL


@pytest.fixture
def sqlite_connection_details() -> dict:
    return SQLITE
