from datetime import datetime, timezone

import pytest
from freezegun import freeze_time

from migri import apply_migrations
from migri.elements import Query

MIGRATIONS_BASE = "test/aiomysql/migrations"

# OK
MIGRATIONS_A_DIR = f"{MIGRATIONS_BASE}/migrations_a"

pytestmark = pytest.mark.asyncio


@freeze_time("2020-7-12 21:30:01")
async def test_apply_migrations_successful(capsys, db_creds, mysql_conn_factory):
    # Apply migrations
    conn = mysql_conn_factory()
    await apply_migrations(MIGRATIONS_A_DIR, conn)

    # Check tables
    conn = mysql_conn_factory()

    async with conn:
        table_query = Query(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_type = 'base table' AND table_schema = $db",
            values={"db": db_creds["db_name"]},
        )
        tables = await conn.fetch_all(table_query)

    assert sorted([t["table_name"] for t in tables]) == [
        "animal",
        "applied_migration",
        "exhibit",
    ]

    # Check for animal entries
    conn = mysql_conn_factory()

    async with conn:
        animal_query = Query("SELECT * FROM animal")
        animals = await conn.fetch_all(animal_query)

    assert [a["name"] for a in animals] == ["bear", "penguin", "turkey"]

    # Check that migrations were recorded
    conn = mysql_conn_factory()

    async with conn:
        migrations_query = Query("SELECT * FROM applied_migration")
        applied_migrations = await conn.fetch_all(migrations_query)

    assert len(applied_migrations) == 4

    for migration in applied_migrations:
        date_applied = migration["date_applied"].replace(tzinfo=timezone.utc)

        assert date_applied.isoformat() == f"{datetime.utcnow().isoformat()}+00:00"

    # Check output
    captured = capsys.readouterr()
    expected_output = (
        "Applying migrations\n"
        "0001_initial...ok\n"
        "0002_add_animals...ok\n"
        "0003_exhibit...ok\n"
        "0004_add_exhibit_id_to_animal...ok\n"
    )

    assert captured.out == expected_output
    assert captured.err == ""
