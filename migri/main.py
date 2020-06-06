import aiofiles
import asyncio
import asyncpg
import click
import glob
import importlib.util
import inspect
import itertools
import logging
import os
import sqlparse
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator, List, Union

MIGRATION_FILE_EXTENSIONS = ["py", "sql"]
MIGRATION_TABLE_NAME = "applied_migration"

logging.basicConfig(
    format="%(asctime)s\t%(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S%z",
    level=os.getenv("LOG_LEVEL", "error").upper(),
)
log = logging.getLogger(__name__)


@dataclass()
class Migration:
    abspath: str
    name: Union[str, None] = None
    file_ext: Union[str, None] = None

    def __post_init__(self):
        name = os.path.basename(self.abspath)
        self.name, self.file_ext = os.path.splitext(name)


def find_migrations(migrations_dir: str) -> List[Migration]:
    path = os.path.abspath(migrations_dir)

    if os.path.isdir(path):
        return [
            Migration(abspath=p)
            for p in sorted(
                itertools.chain(
                    *(
                        glob.iglob(f"{path}/*.{ext}")
                        for ext in MIGRATION_FILE_EXTENSIONS
                    )
                )
            )
        ]
    else:
        raise NotADirectoryError(f"Migrations dir not found: {path}")


async def migrations_to_apply(
    conn: asyncpg.Connection, migrations: List[Migration]
) -> Generator[Migration, None, None]:
    """Takes migration paths and uses migration file names to search for entries in
    'applied_migration' table
    """
    stmt = await conn.prepare(f"SELECT id from {MIGRATION_TABLE_NAME} WHERE name = $1")

    for migration in migrations:
        applied_migration = await stmt.fetchrow(migration.name)

        if not applied_migration:
            yield migration
        else:
            continue


async def apply_statements_from_file(conn: asyncpg.Connection, path: str) -> bool:
    async with aiofiles.open(path, "r") as f:
        contents = await f.read()
        statements = filter(lambda s: s != "", sqlparse.split(contents))

    try:
        async with conn.transaction():
            for statement in statements:
                await conn.execute(statement)
    except Exception as e:
        log.error("Error running migration %s: %s", path, e)
        raise e

    return True


async def apply_statements_from_module(conn: asyncpg.Connection, path: str) -> bool:
    spec = importlib.util.spec_from_file_location("migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    migrate_func = getattr(module, "migrate", None)

    if not migrate_func:
        raise ImportError(f"Module '{path}' has no function migrate()")
    else:
        if inspect.iscoroutinefunction(migrate_func):
            return await migrate_func(conn)
        else:
            raise RuntimeError("migrate() expected to be an async function")


async def record_migration(conn: asyncpg.Connection, migration: Migration) -> bool:
    await conn.execute(
        f"INSERT INTO {MIGRATION_TABLE_NAME} (date_applied, name) VALUES ($1, $2)",
        datetime.now(tz=timezone.utc),
        migration.name,
    )

    return True


async def run_initialization(
    conn: asyncpg.Connection = None,
    db_user: str = None,
    db_pass: str = None,
    db_name: str = None,
    db_host: str = None,
    db_port: str = None,
    force_close_conn: bool = True,
) -> None:
    """Create 'applied_migration' table"""
    migration_table_file_path = os.path.join(
        os.path.dirname(__file__), "sql/applied_migration.sql"
    )

    conn_passed_in = conn is not None

    if not conn_passed_in:
        conn = await asyncpg.connect(
            host=db_host, port=db_port, user=db_user, password=db_pass, database=db_name
        )

    # Create table
    try:
        await apply_statements_from_file(conn, migration_table_file_path)
    finally:
        # Either close connection if instantiated in this function or if it's passed in
        # and user wants it closed
        if not conn_passed_in or force_close_conn:
            await conn.close()


async def _apply_migrations(
    conn: asyncpg.Connection, migrations: AsyncGenerator[Migration, None]
) -> AsyncGenerator[str, None]:
    """Apply migrations and return list of migrations that were applied"""

    async for migration in migrations:
        # Apply migrations
        if migration.file_ext == ".py":
            migration_status = await apply_statements_from_module(
                conn, migration.abspath
            )
        elif migration.file_ext == ".sql":
            migration_status = await apply_statements_from_file(conn, migration.abspath)
        else:
            migration_status = False

        # Update migration record
        if migration_status is True:
            await record_migration(conn, migration)

            yield migration.name


async def run_migrations(
    migrations_dir: str,
    conn: asyncpg.Connection = None,
    db_user: str = None,
    db_pass: str = None,
    db_name: str = None,
    db_host: str = None,
    db_port: str = None,
    dry_run: bool = False,
    force_close_conn: bool = True,
) -> None:
    """Main migration function"""
    # Find migration files
    migrations = find_migrations(migrations_dir)
    log.debug(
        "Found %d migrations: %s",
        len(migrations),
        " ".join([m.name for m in migrations]),
    )

    # Start migration process
    conn_passed_in = conn is not None

    if not conn_passed_in:
        conn = await asyncpg.connect(
            host=db_host, port=db_port, user=db_user, password=db_pass, database=db_name
        )
        log.debug("Created db connection: %s", conn)

    try:
        # Find migrations to apply
        migrations = migrations_to_apply(conn, migrations)

        # Apply migrations
        tr = conn.transaction()
        await tr.start()

        try:
            async for applied_migration in _apply_migrations(conn, migrations):
                log.info("Applied migration: %s", applied_migration)
        except Exception:
            log.warning("Rolled back migration due to error")
            await tr.rollback()
            raise
        else:
            # Roll back transaction if dry run mode
            # Otherwise, commit
            if dry_run:
                await tr.rollback()
                log.info("Ran migrations in dry run mode, migration rolled back")
            else:
                await tr.commit()
    finally:
        # Either close connection if instantiated in this function or if it's passed in
        # and user wants it closed
        if not conn_passed_in or force_close_conn:
            await conn.close()


@click.group()
@click.option("-u", "--db-user", required=True, default=lambda: os.getenv("DB_USER"))
@click.option("-s", "--db-pass", required=True, default=lambda: os.getenv("DB_PASS"))
@click.option("-n", "--db-name", required=True, default=lambda: os.getenv("DB_NAME"))
@click.option("-h", "--db-host", default=lambda: os.getenv("DB_HOST", "localhost"))
@click.option("-p", "--db-port", default=lambda: os.getenv("DB_PORT", "5432"))
@click.option("-l", "--log-level", default=lambda: os.getenv("LOG_LEVEL", "info"))
@click.pass_context
def cli(ctx, **kwargs) -> None:
    log_level = kwargs.pop("log_level")

    log.setLevel(log_level.upper())
    log.debug("Log level set to %d", logging.getLevelName(log_level))

    # Expose db creds to commands via context
    ctx.ensure_object(dict)
    ctx.obj["db"] = kwargs


@cli.command(short_help="Create migrations table to begin using migri")
@click.pass_context
def init(ctx) -> None:
    asyncio.run(run_initialization(**ctx.obj["db"]))


@cli.command(short_help="Run all unapplied migrations in lexicographical order")
@click.option(
    "-m",
    "--migrations-dir",
    required=True,
    default=lambda: os.getenv("MIGRATIONS_DIR", "migrations"),
)
@click.option("--dry-run", default=False, is_flag=True)
@click.pass_context
def migrate(ctx, migrations_dir: str, dry_run: bool) -> None:
    asyncio.run(
        run_migrations(migrations_dir=migrations_dir, dry_run=dry_run, **ctx.obj["db"]),
    )


def main():
    try:
        cli()
    except Exception as e:
        log.error(e)
        log.debug(
            "Exited due to exception", exc_info=True
        )  # Dump stack trace if log level is debug
        sys.exit(1)
