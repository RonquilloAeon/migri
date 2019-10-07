import pytest
from asyncpg import InterfaceError
from datetime import datetime
from freezegun import freeze_time

from migri import run_migrations

MIGRATIONS_DIR = 'test/migrations'


@freeze_time('2019-10-7 19:00:01')
@pytest.mark.asyncio
async def test_run_migrations_successful(conn):
    await run_migrations(MIGRATIONS_DIR, conn, force_close_conn=False)

    # Check account
    account = await conn.fetchrow('SELECT * FROM account WHERE name = $1', 'My Account')

    assert account['name'] == 'My Account'

    # Check user
    user = await conn.fetchrow('SELECT * FROM app_user')

    assert user['account_id'] == account['id']
    assert user['first_name'] == 'M'
    assert user['last_name'] == 'Test'
    assert user['email'] == 'test@example.com'
    assert user['password'] == '078bbb4bf0f7117fb131ec45f15b5b87'

    # Check that record table was created
    record_columns = await conn.fetch(
        'SELECT column_name FROM information_schema.columns WHERE table_schema = $1 AND table_name = $2',
        'public',
        'record'
    )

    assert len(record_columns) == 2
    assert record_columns[0]['column_name'] == 'id'
    assert record_columns[1]['column_name'] == 'user_id'

    #  Check that migrations were recorded
    applied_migrations = await conn.fetch('SELECT * FROM applied_migration')

    assert len(applied_migrations) == 3

    for migration in applied_migrations:
        assert migration['date_applied'].isoformat() == f'{datetime.utcnow().isoformat()}+00:00'


@pytest.mark.asyncio
async def test_run_migrations_close_conn(conn):
    """By default, passed in conn should be closed"""
    await run_migrations(MIGRATIONS_DIR, conn)

    with pytest.raises(InterfaceError):
        await conn.fetchrow('SELECT * FROM account WHERE name = $1', 'My Account')
