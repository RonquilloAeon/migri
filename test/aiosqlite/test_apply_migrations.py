from datetime import datetime

import pytest

from migri import apply_migrations
from migri.elements import Query

MIGRATIONS_A_DIR = "test/data/migrations_a"

pytestmark = pytest.mark.asyncio


async def test_apply_migrations_successful(capsys, sqlite_conn_factory):
    # Apply migrations
    conn = sqlite_conn_factory()
    await apply_migrations(MIGRATIONS_A_DIR, conn)

    # Check that migrations were recorded
    conn = sqlite_conn_factory()

    async with conn:
        migrations_query = Query("SELECT * FROM applied_migration")
        applied_migrations = await conn.fetch_all(migrations_query)

    assert len(applied_migrations) == 3

    for migration in applied_migrations:
        assert (
                migration["date_applied"].isoformat()
                == f"{datetime.utcnow().isoformat()}+00:00"
        )
