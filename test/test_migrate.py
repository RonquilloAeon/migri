import pytest
from asyncpg import InterfaceError

from migri import run_migrations

MIGRATIONS_DIR = 'test/migrations'
MIGRATIONS_TABLE = 'applied_migration'


@pytest.mark.asyncio
async def test_run_migrations_successful(conn):
    await run_migrations(MIGRATIONS_DIR, MIGRATIONS_TABLE, conn, force_close_conn=False)

    # Check account
    account = await conn.fetchrow('SELECT * FROM account WHERE name = $1', 'My Account')

    assert account['name'] == 'My Account'

    # Check user
    user = await conn.fetchrow('SELECT * FROM user')

    assert user['account_id'] == account['id']
    assert user['first_name'] == 'M'
    assert user['last_name'] == 'Test'
    assert user['email'] == 'test@example.com'
    assert user['password'] == '078bbb4bf0f7117fb131ec45f15b5b87'

    # Check that record table was created
    record_columns = await conn.fetchrow(
        'SELECT * FROM information_schema.columns WHERE table_schema = $1 AND table_name = $2',
        'public',
        'record'
    )

    assert len(record_columns) == 2
    assert record_columns[0]['columns'] == 'id'
    assert record_columns[1]['columns'] == 'user_id'


@pytest.mark.asyncio
async def test_run_migrations_close_conn(conn):
    """By default, passed in conn should be closed"""
    await run_migrations(MIGRATIONS_DIR, MIGRATIONS_TABLE, conn)

    with pytest.raises(InterfaceError):
        await conn.fetchrow('SELECT * FROM account WHERE name = $1', 'My Account')
