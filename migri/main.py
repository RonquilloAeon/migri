import asyncio
import logging
import os
import sys
from importlib import import_module
from typing import Optional, Type, TYPE_CHECKING, Union

import click

if TYPE_CHECKING:
    from asyncpg import Connection

from migri import migration
from migri.interfaces import ConnectionBackend
from migri.utils import deprecated, Echo

DEFAULT_LOG_LEVEL = "error"
LEGACY_FUNCTIONALITY_END_OF_LIFE = "1.1.0"
SUPPORTED_DIALECTS = {
    "mysql": "migri.backends.mysql::MySQL",
    "postgresql": "migri.backends.postgresql::PostgreSQL",
    "sqlite": "migri.backends.sqlite::SQLite",
}

logging.basicConfig(
    format="%(asctime)s\t%(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S%z",
    level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper(),
)
logger = logging.getLogger(__name__)


async def run_initialization(*args, **kwargs):
    """No longer supported but left here for compatibility"""
    message = (
        "Command `init` and run_initialization() are no longer supported and are now "
        "handled automatically by `migrate` and run_migrations(). See README."
    )
    deprecated(message, LEGACY_FUNCTIONALITY_END_OF_LIFE)
    Echo.info(message)


async def run_migrations(
    migrations_dir: str,
    conn: "Connection" = None,
    db_user: str = None,
    db_pass: str = None,
    db_name: str = None,
    db_host: str = None,
    db_port: str = None,
    dry_run: bool = False,
    force_close_conn: bool = True,
):
    message = (
        "run_migrations() is deprecated. Please use " "apply_migrations(). See README."
    )
    deprecated(message, LEGACY_FUNCTIONALITY_END_OF_LIFE)
    Echo.info(message)

    # Rig new functionality to provide backwards compatibility
    conn_backend = _get_backend(SUPPORTED_DIALECTS["postgresql"])

    if not conn:
        conn = conn_backend(
            db_name,
            db_user=db_user,
            db_pass=db_pass,
            db_host=db_host,
            db_port=db_port,
        )
    else:
        conn = conn_backend("postgres", db=conn)

    # Now call new migration interface 💪
    await apply_migrations(migrations_dir, conn, dry_run, force_close_conn)


async def apply_migrations(
    migrations_dir: str,
    conn: ConnectionBackend,
    dry_run: bool = False,
    force_close_conn: bool = True,  # TODO For backwards compatibility, remove in 1.1.0
):
    init_task = migration.Initialize(conn)
    migrate_task = migration.Migrate(conn)

    await conn.connect()
    await init_task.run()
    await migrate_task.run(migrations_dir, dry_run)

    if force_close_conn:
        await conn.disconnect()


def _get_backend(module_info: str) -> Type[ConnectionBackend]:
    module_name, module_class_prefix = module_info.split("::")
    module = import_module(module_name)
    return getattr(module, f"{module_class_prefix}Connection")


def get_connection(
    db_name: str,
    db_user: Optional[str] = None,
    db_pass: Optional[str] = None,
    db_host: Optional[str] = None,
    db_port: Optional[Union[int, str]] = None,
    dialect: Optional[str] = None,
) -> ConnectionBackend:
    """Infer db dialect if not provided and initialize connection to database"""
    # If no dialect, infer
    if not dialect:
        if not db_port:
            dialect = "sqlite"
        elif int(db_port) == 3306:
            dialect = "mysql"
        elif int(db_port) == 5432:
            dialect = "postgresql"
        else:
            raise RuntimeError(
                "Unable to infer database dialect, please specify dialect"
            )

    try:
        module_info = SUPPORTED_DIALECTS[dialect]
    except KeyError:
        raise RuntimeError(f"The dialect '{dialect}' is not supported")

    connection = _get_backend(module_info)

    return connection(
        db_name,
        db_user=db_user,
        db_pass=db_pass,
        db_host=db_host,
        db_port=int(db_port) if db_port else None,
    )


@click.group()
@click.option("-n", "--db-name", required=True, default=lambda: os.getenv("DB_NAME"))
@click.option("-u", "--db-user", default=lambda: os.getenv("DB_USER"))
@click.option("-s", "--db-pass", default=lambda: os.getenv("DB_PASS"))
@click.option("-h", "--db-host", default=lambda: os.getenv("DB_HOST"))
@click.option("-p", "--db-port", default=lambda: os.getenv("DB_PORT"))
@click.option("-d", "--dialect", default=lambda: os.getenv("DB_DIALECT"))
@click.option(
    "-l", "--log-level", default=lambda: os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
)
@click.pass_context
def cli(ctx, **kwargs) -> None:
    log_level = kwargs.pop("log_level")

    logger.setLevel(log_level.upper())
    logger.debug("Log %s", logging.getLevelName(log_level))

    # Expose db creds to commands via context
    ctx.ensure_object(dict)
    ctx.obj["connection"] = get_connection(
        db_name=kwargs["db_name"],
        db_user=kwargs["db_user"],
        db_pass=kwargs["db_pass"],
        db_host=kwargs["db_host"],
        db_port=kwargs["db_port"],
        dialect=kwargs["dialect"],
    )


@cli.command(short_help="Create migrations table to begin using migri [unsupported]")
@click.pass_context
def init(ctx) -> None:
    asyncio.run(run_initialization())


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
    asyncio.run(apply_migrations(migrations_dir, ctx.obj["connection"], dry_run))


def main():
    try:
        cli()
    except Exception:
        logger.exception(
            "Caught exception in migri.main::main that caused migri to exit"
        )
        sys.exit(1)
