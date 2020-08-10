from datetime import datetime

import pytest
from freezegun import freeze_time

from migri import apply_migrations
from migri.elements import Query

pytestmark = pytest.mark.asyncio


@freeze_time("2020-7-12 21:30:01")
async def test_apply_migrations_successful(capsys, migrations, sqlite_conn_factory):
    # Apply migrations
    conn = sqlite_conn_factory()
    await apply_migrations(migrations["sqlite_a"], conn)

    # Check tables
    conn = sqlite_conn_factory()

    async with conn:
        table_query = Query("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await conn.fetch_all(table_query)

    assert [t["name"] for t in tables] == ["applied_migration", "account", "record"]

    # Check that account has records
    conn = sqlite_conn_factory()

    async with conn:
        account_query = Query("SELECT * FROM account")
        accounts = await conn.fetch_all(account_query)

    assert [a["name"] for a in accounts] == ["A Star", "B East", "C Me"]

    # Check that migrations were recorded
    conn = sqlite_conn_factory()

    async with conn:
        migrations_query = Query("SELECT * FROM applied_migration")
        applied_migrations = await conn.fetch_all(migrations_query)

    assert len(applied_migrations) == 3

    for migration in applied_migrations:
        date_applied = datetime.fromisoformat(migration["date_applied"])

        assert date_applied.isoformat() == f"{datetime.utcnow().isoformat()}+00:00"

    # Check output
    captured = capsys.readouterr()
    expected_output = (
        "Applying migrations\n"
        "0001_initial...ok\n"
        "0002_add_accounts...ok\n"
        "0003_record...ok\n"
    )

    assert captured.out == expected_output
    assert captured.err == ""


@pytest.mark.skip("not currently supported due to an issue")
async def test_apply_migrations_dry_run(capsys, migrations, sqlite_conn_factory):
    # Apply migrations in dry run mode
    conn = sqlite_conn_factory()
    await apply_migrations(migrations["sqlite_a"], conn, dry_run=True)

    # Check that there aren't any tables
    conn = sqlite_conn_factory()

    async with conn:
        table_query = Query("SELECT name FROM sqlite_master WHERE type='table'")
        tables = await conn.fetch_all(table_query)

    assert len(tables) == 1  # applied_migration expected
    assert tables[0]["name"] == "applied_migration"

    # Check output
    captured = capsys.readouterr()
    expected_output = (
        "Applying migrations\n"
        "0001_initial...ok\n"
        "0002_add_accounts...ok\n"
        "0003_record...ok\n"
        "Successfully applied migrations in dry run mode.\n"
    )

    assert captured.out == expected_output
    assert captured.err == ""
