import pytest


@pytest.mark.asyncio
async def test_migrate(conn):
    async with conn.transaction():
        async for record in conn.cursor('SELECT current_database() as db'):
            assert record['db'] == 'migritestdb'
