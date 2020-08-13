from pathlib import Path
from typing import Callable, ContextManager, List
import os
import sys

import pytest

from test import aiomysql, asyncpg

AUTOMATED_MIGRATIONS_PATH = Path("test/migrations/automated")

# For action type in automated_migration_manager_factory()
if sys.version_info.major == 3 and sys.version_info.minor >= 8:
    from typing import Literal

    ActionType = Literal["create", "delete"]
else:
    ActionType = str


@pytest.yield_fixture
def automated_migration_manager() -> ContextManager:
    def _wrapped(
        migration_file_name: str, action: ActionType, content: str = None,
    ):
        file = AUTOMATED_MIGRATIONS_PATH / migration_file_name

        if action == "create":
            with open(file, "w") as f:
                f.write(content or "")
        elif action == "delete":
            if file.is_file():
                file.unlink()
            else:
                raise FileNotFoundError(f"File {file} not found")

    try:
        yield _wrapped
    finally:
        for file in os.listdir(AUTOMATED_MIGRATIONS_PATH):
            if file.endswith(".sql") or file.endswith(".txt"):
                os.remove(Path(AUTOMATED_MIGRATIONS_PATH) / file)


@pytest.fixture
def generic_db_migri_command_base_args() -> Callable:
    def _wrapped(connection_details: dict) -> List[str]:
        return [
            "migri",
            "-n",
            connection_details["db_name"],
            "-u",
            connection_details["db_user"],
            "-s",
            connection_details["db_pass"],
            "-p",
            str(connection_details["db_port"]),
        ]

    return _wrapped


@pytest.fixture
def sqlite_migri_command_base_args() -> Callable:
    def _wrapped(db_name: str) -> List[str]:
        return [
            "migri",
            "-n",
            db_name,
        ]

    return _wrapped


def pytest_configure(config):
    aiomysql.configure(config)
    asyncpg.configure(config)


def pytest_unconfigure(config):
    aiomysql.unconfigure(config)
    asyncpg.unconfigure(config)
