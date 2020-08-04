async def migrate(conn) -> bool:
    animal_names = [("bear",), ("penguin",), ("turkey",)]

    cur = await conn.cursor()
    await cur.executemany("INSERT INTO animal (name) VALUES (%s)", animal_names)

    return True
