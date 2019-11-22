async def migrate(conn) -> bool:
    await conn.execute('INSERT INTO account (name) VALUES ($1)', 'My Account')
    account = await conn.fetchrow('SELECT * FROM account WHERE name = $1', 'My Account')

    await conn.execute(
        'INSERT INTO app_user (account_id, first_name, last_name, email, password) VALUES ($1, $2, $3, $4, $5)',
        account['id'],
        'M',
        'Test',
        'test@example.com',
        '078bbb4bf0f7117fb131ec45f15b5b87'
    )

    return True
