import pytest
from asyncpg import InterfaceError
from datetime import datetime
from freezegun import freeze_time

from migri import apply_migrations, run_migrations
from migri.elements import Query

# OK
MIGRATIONS_A_DIR = "test/data/migrations_a"
MIGRATIONS_B_DIR = "test/data/migrations_b"

# Empty directory
MIGRATIONS_C_DIR = "test/data/migrations_c"

# Has an empty SQL migration file
MIGRATIONS_D_DIR = "test/data/migrations_d"

# Has an empty Python migration file
MIGRATIONS_E_DIR = "test/data/migrations_e"

pytestmark = pytest.mark.asyncio


@freeze_time("2020-7-3 22:00:01")
async def test_apply_migrations_successful(capsys, postgresql_conn_factory):
    """Apply migrations and then check that friendly message is output if
    migrations are up-to-date"""
    # Apply migrations
    conn = postgresql_conn_factory()
    await apply_migrations(MIGRATIONS_A_DIR, conn)

    # Check that record table was created
    record_query = Query(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = $schema AND table_name = $table_name",
        values={"schema": "public", "table_name": "record"},
    )

    conn = postgresql_conn_factory()

    async with conn:
        record_columns = await conn.fetch_all(record_query)

    assert len(record_columns) == 2
    assert record_columns[0]["column_name"] == "id"
    assert record_columns[1]["column_name"] == "user_id"

    # Check that migrations were recorded
    conn = postgresql_conn_factory()

    async with conn:
        migrations_query = Query("SELECT * FROM applied_migration")
        applied_migrations = await conn.fetch_all(migrations_query)

    assert len(applied_migrations) == 3

    for migration in applied_migrations:
        assert (
            migration["date_applied"].isoformat()
            == f"{datetime.utcnow().isoformat()}+00:00"
        )

    # Check output
    captured = capsys.readouterr()
    expected_output = (
        "Applying migrations\n"
        "0001_initial...ok\n"
        "0002_add_initial_data...ok\n"
        "0003_record...ok\n"
    )

    assert captured.out == expected_output
    assert captured.err == ""

    # Apply migrations again - we expect friendly output to let us know that migrations
    # are all up to date
    conn = postgresql_conn_factory()

    await apply_migrations(MIGRATIONS_A_DIR, conn)

    captured = capsys.readouterr()
    expected_output = "All synced! No new migrations to apply! 🥳\n"

    assert captured.out == expected_output
    assert captured.err == ""


async def test_apply_migrations_none(capsys, postgresql_conn_factory):
    """Ensure friendly message is output when migrations directory is empty"""
    # Apply migrations
    conn = postgresql_conn_factory()
    await apply_migrations(MIGRATIONS_C_DIR, conn)

    # Check that there aren't any tables
    conn = postgresql_conn_factory()

    async with conn:
        tables_query = Query(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema='public' AND table_type='BASE TABLE';"
        )
        tables = await conn.fetch_all(tables_query)

    assert len(tables) == 1  # applied_migration expected
    assert tables[0]["table_name"] == "applied_migration"

    # Check output
    captured = capsys.readouterr()
    expected_output = "No migrations to apply. Migrations directory is empty.\n"

    assert captured.out == expected_output
    assert captured.err == ""


async def test_apply_migrations_dry_run(capsys, postgresql_conn_factory):
    # Apply migrations in dry run mode
    conn = postgresql_conn_factory()
    await apply_migrations(MIGRATIONS_A_DIR, conn, dry_run=True)

    # Check that there aren't any tables
    conn = postgresql_conn_factory()

    async with conn:
        tables_query = Query(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema='public' AND table_type='BASE TABLE';"
        )
        tables = await conn.fetch_all(tables_query)

    assert len(tables) == 1  # applied_migration expected
    assert tables[0]["table_name"] == "applied_migration"

    # Check output
    captured = capsys.readouterr()
    expected_output = (
        "Applying migrations\n"
        "0001_initial...ok\n"
        "0002_add_initial_data...ok\n"
        "0003_record...ok\n"
        "Successfully applied migrations in dry run mode.\n"
    )

    assert captured.out == expected_output
    assert captured.err == ""


async def test_apply_migrations_with_empty_statement_successful(
    capsys, postgresql_conn_factory
):
    """
    If sql file ends w/ empty line, sqlparse returns an empty string as a statement.
    Test that migration goes through and empty statement is filtered out
    """
    conn = postgresql_conn_factory()
    await apply_migrations(MIGRATIONS_B_DIR, conn)

    # Query for tables
    conn = postgresql_conn_factory()

    async with conn:
        tables_query = Query(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema='public' AND table_type='BASE TABLE';"
        )
        tables = await conn.fetch_all(tables_query)

    assert len(tables) == 3

    for table in tables:
        assert table["table_name"] in [
            "applied_migration",
            "state_machine",
            "state_history",
        ]

    # Check output
    captured = capsys.readouterr()
    expected_output = (
        "Applying migrations\n"
        "0001_initial...ok\n"
    )

    assert captured.out == expected_output
    assert captured.err == ""


@pytest.mark.parametrize(
    "migrations_dir,expected_tables,expected_output",
    [
        (
            MIGRATIONS_D_DIR,
            ["applied_migration", "quote"],
            (
                "Applying migrations\n"
                "0001_initial...ok\n"
                "0002_empty...fail [empty migration]\n"
                "0003_view...fail [previous migration failed]\n"
            ),
        ),
        (
            MIGRATIONS_E_DIR,
            ["applied_migration", "satellite"],
            (
                "Applying migrations\n"
                "0001_initial...ok\n"
                "0002_load_satellites...fail [empty migration]\n"
                "0003_add_manufacturer_table...fail [previous migration failed]\n"
            ),
        ),
    ]
)
async def test_apply_migrations_empty_migration(
    migrations_dir, expected_tables, expected_output, capsys, postgresql_conn_factory
):
    # Attempt to run migrations
    conn = postgresql_conn_factory()
    await apply_migrations(migrations_dir, conn)

    # Query for tables
    conn = postgresql_conn_factory()

    async with conn:
        tables_query = Query(
            "SELECT table_name FROM information_schema.tables"
            " WHERE table_schema='public' AND table_type='BASE TABLE';"
        )
        tables = await conn.fetch_all(tables_query)

    assert len(tables) == 2

    for table in tables:
        assert table["table_name"] in expected_tables

    # Check output
    captured = capsys.readouterr()

    assert captured.out == expected_output
    assert captured.err == ""


# TODO remove in 1.1.0
async def test_apply_migrations_no_close_conn(postgresql_conn_factory):
    """force_close_conn is a feature for backwards compatibility. Defaults to true"""
    conn = postgresql_conn_factory()
    await apply_migrations(MIGRATIONS_A_DIR, conn, force_close_conn=False)

    # Check that underlying connection can still be used
    result = await conn.database.fetchrow(
        "SELECT * FROM account WHERE name = $1", "My Account"
    )

    assert result

    await conn.disconnect()


@freeze_time("2019-10-7 19:00:01")
async def test_deprecated_run_migrations_successful(postgresql_conn_factory, conn):
    await run_migrations(MIGRATIONS_A_DIR, conn, force_close_conn=False)

    # Check account
    account = await conn.fetchrow("SELECT * FROM account WHERE name = $1", "My Account")

    assert account["name"] == "My Account"

    # Check user
    user = await conn.fetchrow("SELECT * FROM app_user")

    assert user["account_id"] == account["id"]
    assert user["first_name"] == "M"
    assert user["last_name"] == "Test"
    assert user["email"] == "test@example.com"
    assert user["password"] == "078bbb4bf0f7117fb131ec45f15b5b87"

    # Check that record table was created
    record_columns = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = $1 AND table_name = $2",
        "public",
        "record",
    )

    assert len(record_columns) == 2
    assert record_columns[0]["column_name"] == "id"
    assert record_columns[1]["column_name"] == "user_id"

    # Check that migrations were recorded
    applied_migrations = await conn.fetch("SELECT * FROM applied_migration")

    assert len(applied_migrations) == 3

    for migration in applied_migrations:
        assert (
            migration["date_applied"].isoformat()
            == f"{datetime.utcnow().isoformat()}+00:00"
        )


async def test_deprecated_run_migrations_dry_run(postgresql_conn_factory, conn):
    """If running in dry run mode, pending migration(s) won't be committed. Useful for
    testing that migrations are error-free"""
    await run_migrations(MIGRATIONS_A_DIR, conn, dry_run=True, force_close_conn=False)

    tables = await conn.fetch(
        "SELECT table_name FROM information_schema.tables"
        " WHERE table_schema='public' AND table_type='BASE TABLE';"
    )

    assert len(tables) == 1  # applied_migration expected
    assert tables[0]["table_name"] == "applied_migration"


async def test_deprecated_run_migrations_with_empty_statement_successful(
    postgresql_conn_factory, conn
):
    """
    If sql file ends w/ empty line, sqlparse returns an empty string as a statement.
    Test that migration goes through and empty statement is filtered out
    """
    await run_migrations(MIGRATIONS_B_DIR, conn, force_close_conn=False)

    tables = await conn.fetch(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
    )

    assert len(tables) == 3

    for table in tables:
        assert table["table_name"] in [
            "applied_migration",
            "state_machine",
            "state_history",
        ]


async def test_deprecated_run_migrations_close_conn(postgresql_conn_factory, conn):
    """By default, passed in conn should be closed"""
    await run_migrations(MIGRATIONS_A_DIR, conn)

    with pytest.raises(InterfaceError):
        await conn.fetchrow("SELECT * FROM account WHERE name = $1", "My Account")
