from subprocess import Popen, PIPE

import pytest

from migri.elements import Query

pytestmark = pytest.mark.asyncio


def _create_postgresql_args(connection_details: dict) -> list:
    return [
        "migri",
        "-n",
        connection_details["db_name"],
        "-u",
        connection_details["db_user"],
        "-s",
        connection_details["db_pass"],
        "-p",
        connection_details["db_port"],
        "migrate",
    ]


async def test_migrate_postgresql(
    migrations, postgresql_conn_factory, postgresql_connection_details, postgresql_db
):
    args = _create_postgresql_args(postgresql_connection_details) + [
        "-m",
        migrations["postgresql_a"],
    ]
    p = Popen(args, stdout=PIPE)
    stdout, _ = p.communicate()

    # Check output
    assert stdout.decode("utf-8") == (
        "Applying migrations\n"
        "0001_initial...ok\n"
        "0002_add_initial_data...ok\n"
        "0003_record...ok\n"
    )

    # Check tables
    conn = postgresql_conn_factory()

    async with conn:
        tables_query = Query(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema='public' AND table_type='BASE TABLE';"
        )
        tables = await conn.fetch_all(tables_query)

    assert len(tables) == 4

    for table in tables:
        assert table["table_name"] in [
            "account",
            "applied_migration",
            "app_user",
            "record",
        ]

    # Check that data migration was successful
    conn = postgresql_conn_factory()

    async with conn:
        app_users_query = Query("SELECT email FROM app_user")
        app_users = await conn.fetch_all(app_users_query)

    assert len(app_users) == 1
    assert app_users[0]["email"] == "test@example.com"


async def test_migration_postgresql_dry_run(
    migrations, postgresql_conn_factory, postgresql_connection_details, postgresql_db
):
    args = _create_postgresql_args(postgresql_connection_details) + [
        "-m",
        migrations["postgresql_a"],
        "--dry-run",
    ]
    p = Popen(args, stdout=PIPE)
    stdout, _ = p.communicate()

    # Check output
    assert stdout.decode("utf-8") == (
        "Applying migrations\n"
        "0001_initial...ok\n"
        "0002_add_initial_data...ok\n"
        "0003_record...ok\n"
        "Successfully applied migrations in dry run mode.\n"
    )

    # Check that no tables were created
    conn = postgresql_conn_factory()

    async with conn:
        tables_query = Query(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema='public' AND table_type='BASE TABLE';"
        )
        tables = await conn.fetch_all(tables_query)

    assert len(tables) == 1  # applied_migration expected
    assert tables[0]["table_name"] == "applied_migration"
