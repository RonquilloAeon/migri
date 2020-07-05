import glob
import importlib.util
import itertools
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from inspect import iscoroutinefunction
from typing import AsyncGenerator, Iterable, List, Optional, Union

import sqlparse

from migri.elements import Query
from migri.interfaces import Task

__all__ = ["Initialize", "Migrate"]
logger = logging.getLogger(__name__)

MIGRATION_TABLE_NAME = "applied_migration"


@dataclass
class Migration:
    abspath: str
    name: Union[str, None] = None
    file_ext: Union[str, None] = None

    def __post_init__(self):
        name = os.path.basename(self.abspath)
        self.name, self.file_ext = os.path.splitext(name)


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
            raise ImportError(f"Module '{path}' has no function migrate()")
        else:
            if iscoroutinefunction(migrate_func):
                return await migrate_func(self._connection.database)
            else:
                raise RuntimeError("migrate() expected to be an async function")

    async def _apply_migration_from_sql_file(self, path: str) -> bool:
        with open(path, "r") as f:
            contents = f.read()
            statements = filter(lambda s: s != "", sqlparse.split(contents))

        try:
            for statement in statements:
                await self._connection.execute(Query(statement))
        except Exception as e:
            logger.warning("Error running migration %s: %s", path, e)
            raise MigrationFailed from e

        return True


class Initialize(MigrationApplyMixin, MigrationFilesMixin, Task):
    async def run(self):
        """Create 'applied_migration' table"""
        migration_table_file_path = os.path.join(
            os.path.dirname(__file__), "sql/applied_migration.sql"
        )

        # Create table
        transaction = await self._connection.transaction()

        async with transaction:
            await self._apply_migration_from_sql_file(migration_table_file_path)
            await transaction.commit()


class Migrate(MigrationApplyMixin, MigrationFilesMixin, Task):
    async def _apply_migrations(
        self, migrations: List[Migration]
    ) -> AsyncGenerator[str, None]:
        """Apply migrations and return list of migrations that were applied"""
        for migration in migrations:
            # Apply migrations
            if migration.file_ext == ".py":
                migration_status = await self._apply_migration_from_module(
                    migration.abspath
                )
            elif migration.file_ext == ".sql":
                migration_status = await self._apply_migration_from_sql_file(
                    migration.abspath
                )
            else:
                migration_status = False

            # Update migration record
            if migration_status is True:
                await self._record_migration(migration)

                yield migration.name

    def _pre_migration_checks(self, migrations: List[Migration]) -> bool:
        """Check migrations before applying"""
        if len(migrations) == 0:
            raise MigrationOk("All synced! No new migrations to apply! 🥳")

        return True

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

    async def _apply(self, migrations: List[Migration], dry_run: bool):
        transaction = await self._connection.transaction()
        await transaction.start()

        try:
            async for migration in self._apply_migrations(migrations):
                self.echo.info(f"Applied migration: {migration}")
        except Exception:
            logger.exception("Rolled back migration due to an error.")
            await transaction.rollback()
            raise
        else:
            # Roll back transaction if dry run mode
            # Otherwise, commit
            if dry_run:
                await transaction.rollback()
                self.echo.info("Successfully applied migrations in dry run mode.")
            else:
                await transaction.commit()

    async def run(
        self, migrations_dir: str, dry_run: Optional[bool] = False,
    ):
        migrations = self.get_migrations(migrations_dir)

        if not migrations:
            self.echo.info("No migrations to apply. Migrations directory is empty.")
            return

        migrations = await self._migrations_to_apply(migrations)

        # Apply migrations
        try:
            self._pre_migration_checks(migrations)
        except MigrationOk as e:
            self.echo.info(e)
        else:
            await self._apply(migrations, dry_run)
