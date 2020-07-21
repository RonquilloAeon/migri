async def migrate(conn) -> bool:
    account_names = [("A Star",), ("B East",), ("C Me",)]
    await conn.executemany("INSERT INTO account (name) VALUES (?)", account_names)

    return True
