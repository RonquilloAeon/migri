import glob
import importlib.util
import itertools
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from inspect import iscoroutinefunction
from pathlib import Path
from typing import AsyncGenerator, Iterable, List, Optional, Union

import sqlparse

from migri.elements import Query
from migri.interfaces import Task

__all__ = ["Initialize", "Migrate"]
logger = logging.getLogger(__name__)

MIGRATION_TABLE_NAME = "applied_migration"
APPLICATION_SQL_PATH = Path(os.path.dirname(__file__), "sql")
APPLIED_MIGRATION_SQL_FILE = {
    "mysql": "mysql_applied_migration.sql",
    "postgresql": "default_applied_migration.sql",
    "sqlite": "default_applied_migration.sql",
}


@dataclass
class Migration:
    abspath: str
    name: Union[str, None] = None
    file_ext: Union[str, None] = None

    def __post_init__(self):
        name = os.path.basename(self.abspath)
        self.name, self.file_ext = os.path.splitext(name)


class MigrationStatus(Enum):
    FAILURE = "fail"
    SUCCESS = "ok"


@dataclass(frozen=True)
class MigrationResult:
    migration_name: str
    message: str
    status: MigrationStatus


class MigrationFailed(Exception):
    ...


class MigrationOk(Exception):
    ...


class MigrationFilesMixin(object):
    MIGRATION_FILE_EXTENSIONS = ["py", "sql"]

    def _find_migrations(self, migrations_path: str) -> Iterable[str]:
        return itertools.chain(
            *(
                glob.iglob(f"{migrations_path}/*.{ext}")
                for ext in self.MIGRATION_FILE_EXTENSIONS
            )
        )

    def get_migrations(self, migrations_dir: str) -> List[Migration]:
        path = os.path.abspath(migrations_dir)

        if not os.path.isdir(path):
            raise NotADirectoryError(f"Migrations dir not found: {path}")

        return [Migration(abspath=p) for p in sorted(self._find_migrations(path))]


class MigrationApplyMixin(object):
    async def _apply_migration_from_module(self, path: str) -> bool:
        spec = importlib.util.spec_from_file_location("migration", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        migrate_func = getattr(module, "migrate", None)

        if not migrate_func:
            raise ImportError("module missing migrate()")
        else:
            if iscoroutinefunction(migrate_func):
                return await migrate_func(self._connection.database)
            else:
                raise RuntimeError("migrate() expected to be an async function")

    async def _apply_migration_from_sql_file(self, path: str) -> bool:
        with open(path, "r") as f:
            contents = f.read()
            statements = [s for s in sqlparse.split(contents) if s != ""]

        if not statements:
            raise ValueError("empty migration")

        try:
            for statement in statements:
                await self._connection.execute(Query(statement))
        except Exception as e:
            logger.warning("Error running migration %s: %s", path, e)
            raise MigrationFailed from e

        return True

    async def apply_migration(self, migration: Migration) -> bool:
        if migration.file_ext == ".py":
            return await self._apply_migration_from_module(migration.abspath)
        elif migration.file_ext == ".sql":
            return await self._apply_migration_from_sql_file(migration.abspath)

        return False


class Initialize(MigrationApplyMixin, Task):
    async def run(self):
        """Create 'applied_migration' table"""
        transaction = self._connection.transaction()
        migration_file = APPLIED_MIGRATION_SQL_FILE[self._connection.dialect]

        async with transaction:
            await self._apply_migration_from_sql_file(
                APPLICATION_SQL_PATH / migration_file
            )
            await transaction.commit()


class Migrate(MigrationApplyMixin, MigrationFilesMixin, Task):
    class RollbackTransaction(Exception):
        ...

    async def _apply(self, migration: Migration) -> MigrationResult:
        migration_message = "unknown error"
        status = MigrationStatus.FAILURE

        try:
            # Apply migrations
            migrate_success = await self.apply_migration(migration)
        except (ImportError, RuntimeError, ValueError) as e:
            migration_message = str(e)
        except Exception as e:
            logger.exception("Rolled back migration due to an error.")
            migration_message = str(e)
        else:
            # Update migration record
            if migrate_success:
                await self._record_migration(migration)
                migration_message = "ok"
                status = MigrationStatus.SUCCESS

        return MigrationResult(
            migration_name=migration.name, message=migration_message, status=status
        )

    @asynccontextmanager
    async def _optional_transaction(self, create_transaction: bool):
        transaction = None

        if create_transaction:
            transaction = self._connection.transaction()
            await transaction.start()

        try:
            yield

            if transaction:
                await transaction.commit()
        except self.RollbackTransaction:
            if transaction:
                await transaction.rollback()

    async def _apply_migrations(
        self, migrations: List[Migration], dry_run: bool
    ) -> AsyncGenerator[MigrationResult, None]:
        """Apply migrations and yield names of migrations that were applied"""

        # If a migration fails, fail subsequent ones automatically w/out applying them
        migration_failed = False

        async with self._optional_transaction(dry_run):
            for migration in migrations:
                if migration_failed:
                    yield MigrationResult(
                        migration_name=migration.name,
                        message="previous migration failed",
                        status=MigrationStatus.FAILURE,
                    )
                else:
                    async with self._optional_transaction(not dry_run):
                        result = await self._apply(migration)
                        migration_failed = (
                            True if result.status == MigrationStatus.FAILURE else False
                        )

                        if migration_failed:
                            raise self.RollbackTransaction

                    yield result

            raise self.RollbackTransaction

        if dry_run:
            self.echo.info("Successfully applied migrations in dry run mode.")

    async def _migrations_to_apply(
        self, migrations: List[Migration]
    ) -> List[Migration]:
        """Takes migration paths and uses migration file names to search for entries in
        'applied_migration' table
        """
        to_apply = []

        for migration in migrations:
            query = Query(
                f"SELECT id FROM {MIGRATION_TABLE_NAME} WHERE name = $migration_name",
                values={"migration_name": migration.name},
            )
            applied_migration = await self._connection.fetch_all(query)

            if not applied_migration:
                to_apply.append(migration)

        return to_apply

    async def _record_migration(self, migration: Migration):
        query = Query(
            f"INSERT INTO {MIGRATION_TABLE_NAME} (date_applied, name) "
            f"VALUES ($date, $migration_name)",
            values={
                "date": datetime.now(tz=timezone.utc),
                "migration_name": migration.name,
            },
        )

        await self._connection.execute(query)

    async def run(
        self,
        migrations_dir: str,
        dry_run: Optional[bool] = False,
    ):
        # Check if trying to run dry run mode w/ sqlite or mysql
        # Not currently supported due to a transaction issue
        if self._connection.dialect == "sqlite" and dry_run:
            self.echo.error("Dry run mode is not currently supported with SQLite.")
            return
        if self._connection.dialect == "mysql" and dry_run:
            self.echo.error("Dry run mode is not supported with MySQL.")
            return

        migrations = self.get_migrations(migrations_dir)

        if not migrations:
            self.echo.info("No migrations to apply. Migrations directory is empty.")
            return

        migrations = await self._migrations_to_apply(migrations)

        # Check if there are migrations to apply
        # If so, apply them
        if len(migrations) == 0:
            self.echo.info("All synced! No new migrations to apply! 🥳")
        else:
            self.echo.info("Applying migrations")

            async for result in self._apply_migrations(migrations, dry_run):
                message = (
                    f" [{result.message}]"
                    if result.status == MigrationStatus.FAILURE
                    else ""
                )

                self.echo.info(
                    f"{result.migration_name}...{result.status.value}{message}"
                )
