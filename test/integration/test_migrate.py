from subprocess import Popen, PIPE

import pytest

from migri.elements import Query

pytestmark = pytest.mark.asyncio


def _create_db_args(connection_details: dict) -> list:
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
        "migrate",
    ]


def _create_sqlite_args(db_name: str) -> list:
    return [
        "migri",
        "-n",
        db_name,
        "migrate",
    ]


async def test_migrate_mysql(migrations, mysql_conn_factory, mysql_connection_details):
    args = _create_db_args(mysql_connection_details) + [
        "-m",
        migrations["mysql_a"],
    ]
    p = Popen(args, stdout=PIPE)
    stdout, _ = p.communicate()

    # Check output
    assert stdout.decode("utf-8") == (
        "Applying migrations\n"
        "0001_initial...ok\n"
        "0002_add_animals...ok\n"
        "0003_exhibit...ok\n"
        "0004_add_exhibit_id_to_animal...ok\n"
    )

    # Check tables
    conn = mysql_conn_factory()

    async with conn:
        table_query = Query(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_type = 'base table' AND table_schema = $db",
            values={"db": mysql_connection_details["db_name"]},
        )
        tables = await conn.fetch_all(table_query)

    assert sorted([t["table_name"] for t in tables]) == [
        "animal",
        "applied_migration",
        "exhibit",
    ]

    # Check data
    conn = mysql_conn_factory()

    async with conn:
        animal_query = Query("SELECT name FROM animal")
        animals = await conn.fetch_all(animal_query)

    assert [a["name"] for a in animals] == ["bear", "penguin", "turkey"]


async def test_migrate_mysql_dry_run(
    migrations, mysql_conn_factory, mysql_connection_details
):
    args = _create_db_args(mysql_connection_details) + [
        "-m",
        migrations["mysql_a"],
        "--dry-run",
    ]
    p = Popen(args, stdout=PIPE)
    stdout, _ = p.communicate()

    # Check output
    assert stdout.decode("utf-8") == "Dry run mode is not supported with MySQL.\n"

    # Check that no migrations were applied
    conn = mysql_conn_factory()

    async with conn:
        table_query = Query(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_type = 'base table' AND table_schema = $db",
            values={"db": mysql_connection_details["db_name"]},
        )
        tables = await conn.fetch_all(table_query)

    assert len(tables) == 1  # applied_migration expected
    assert tables[0]["table_name"] == "applied_migration"


async def test_migrate_postgresql(
    migrations, postgresql_conn_factory, postgresql_connection_details, postgresql_db
):
    args = _create_db_args(postgresql_connection_details) + [
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

    assert sorted([t["table_name"] for t in tables]) == [
        "account",
        "app_user",
        "applied_migration",
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
    args = _create_db_args(postgresql_connection_details) + [
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


async def test_migrate_sqlite(
    migrations, sqlite_conn_factory, sqlite_connection_details
):
    args = _create_sqlite_args(sqlite_connection_details["db_name"]) + [
        "-m",
        migrations["sqlite_a"],
    ]
    p = Popen(args, stdout=PIPE)
    stdout, _ = p.communicate()

    assert stdout.decode("utf-8") == (
        "Applying migrations\n"
        "0001_initial...ok\n"
        "0002_add_accounts...ok\n"
        "0003_record...ok\n"
    )

    # Check tables
    conn = sqlite_conn_factory()

    async with conn:
        table_query = Query("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await conn.fetch_all(table_query)

    assert [t["name"] for t in tables] == ["applied_migration", "account", "record"]

    # Check for account records
    conn = sqlite_conn_factory()

    async with conn:
        account_query = Query("SELECT * FROM account")
        accounts = await conn.fetch_all(account_query)

    assert [a["name"] for a in accounts] == ["A Star", "B East", "C Me"]


async def test_migrate_sqlite_dry_run(
    migrations, sqlite_conn_factory, sqlite_connection_details
):
    args = _create_sqlite_args(sqlite_connection_details["db_name"]) + ["--dry-run"]
    p = Popen(args, stdout=PIPE)
    stdout, _ = p.communicate()

    assert stdout.decode("utf-8") == (
        "Dry run mode is not currently supported with SQLite.\n"
    )

    # Check that no tables were created
    conn = sqlite_conn_factory()

    async with conn:
        table_query = Query("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await conn.fetch_all(table_query)

    assert len(tables) == 1  # applied_migration expected
    assert tables[0]["name"] == "applied_migration"
