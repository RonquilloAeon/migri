import asyncio
import asyncpg
import click
import glob
import itertools
import logging
import os
import sys
from typing import List

MIGRATION_FILE_EXTENSIONS = ['py', 'sql']

logging.basicConfig(format='%(asctime)s\t%(levelname)s: %(message)s', datefmt='%Y-%m-%d %I:%M:%S%z',
                    level=os.getenv('LOG_LEVEL', 'ERROR'))
log = logging.getLogger('__name__')


def find_migrations(migrations_dir: str) -> List[str]:
    path = os.path.abspath(migrations_dir)

    if os.path.isdir(path):
        return sorted(
            itertools.chain(*(glob.iglob(f'{path}/*.{ext}') for ext in MIGRATION_FILE_EXTENSIONS))
        )
    else:
        raise NotADirectoryError(f'Migrations dir not found: {path}')


async def find_migrations_to_apply(migration_paths: List[str], migrations_table: str) -> List[str]:
    """Takes migration paths and uses migration file names to search for entries in 'applied_migration' table"""
    pass


async def apply_migrations(migrations: List[str]) -> None:
    pass


async def run_migrations(
    migrations_dir: str,
    migrations_table: str,
    conn: asyncpg.Connection = None,
    db_user: str = None,
    db_pass: str = None,
    db_name: str = None,
    db_host: str = None,
    db_port: str = None,
    force_close_conn: bool = True
) -> None:
    """Main migration function"""
    # Manually create migration table

    # Find migration files
    migrations = find_migrations(migrations_dir)
    log.debug('Found %d migrations: %s', len(migrations), ' '.join(migrations))

    # Start migration process
    conn_passed_in = conn is not None

    if not conn_passed_in:
        conn = await asyncpg.connect(host=db_host, port=db_port, user=db_user, password=db_pass, database=db_name)
        log.debug('Created db connection: %s', conn)

    try:
        # Find migrations to apply
        migrations_to_apply = await find_migrations_to_apply(migrations, migrations_table)

        # Apply migrations
        # Update migration record
    finally:
        # Either close connection if instantiated in this function or if it's passed in and user wants it closed
        if not conn_passed_in or force_close_conn:
            await conn.close()


@click.group()
@click.option('-l', '--log-level', default=lambda: os.getenv('LOG_LEVEL', 'ERROR'))
def cli(log_level: str) -> None:
    log.setLevel(log_level)
    log.debug('Log level set to %d', logging.getLevelName(log_level))


@cli.command()
@click.option('-m', '--migrations-dir', required=True, default=lambda: os.getenv('MIGRATIONS_DIR', 'migrations'))
@click.option('-t', '--migrations-table', required=True, default=os.getenv('MIGRATIONS_TABLE', 'applied_migration'))
@click.option('-u', '--db-user', required=True, default=lambda: os.getenv('DB_USER'))
@click.option('-s', '--db-pass', required=True, default=lambda: os.getenv('DB_PASS'))
@click.option('-n', '--db-name', required=True, default=lambda: os.getenv('DB_NAME'))
@click.option('-h', '--db-host', default=lambda: os.getenv('DB_HOST', 'localhost'))
@click.option('-p', '--db-port', default=lambda: os.getenv('DB_PORT', '5432'))
def migrate(**kwargs) -> None:
    asyncio.run(run_migrations(**kwargs))


def main():
    try:
        cli()
    except Exception as e:
        log.error(e)
        log.debug('Exited due to exception', exc_info=True)  # Dump stack trace if log level is debug
        sys.exit(1)
