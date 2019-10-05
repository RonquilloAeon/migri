import click
import glob
import itertools
import os
import sys
from typing import List

MIGRATION_FILE_EXTENSIONS = ['py', 'sql']


@click.group()
def cli():
    pass


def find_migrations(migrations_dir: str) -> List[str]:
    path = os.path.abspath(migrations_dir)

    if os.path.isdir(path):
        return sorted(
            itertools.chain(*(glob.iglob(f'{path}/*.{ext}') for ext in MIGRATION_FILE_EXTENSIONS))
        )
    else:
        raise NotADirectoryError(f'Migrations dir not found: {path}')


@cli.command()
@click.option('-m', '--migrations-dir', required=True, default='migrations')
@click.option('-u', '--db-user', required=True, default=lambda: os.getenv('DB_USER'))
@click.option('-s', '--db-pass', required=True, default=lambda: os.getenv('DB_PASS'))
@click.option('-n', '--db-name', required=True, default=lambda: os.getenv('DB_NAME'))
@click.option('-h', '--db-host', default=lambda: os.getenv('DB_HOST', 'localhost'))
@click.option('-p', '--db-port', default=lambda: os.getenv('DB_PORT', '5432'))
@click.option('-t', '--migrations-table-name', default=os.getenv('MIGRATIONS_TABLE', 'applied_migration'))
def migrate(**kwargs) -> None:
    run(**kwargs)


def run(
    migrations_dir: str,
    db_user: str,
    db_pass: str,
    db_name: str,
    db_host: str,
    db_port: str,
    migrations_table_name: str
) -> None:
    # Manually create migration table

    # Find migration files
    migrations = find_migrations(migrations_dir)
    click.echo(migrations)

    # Find migrations to apply
    # Apply migrations
    # Update migration record


def main():
    try:
        cli()
    except Exception as e:
        click.echo(e)
        sys.exit(1)
