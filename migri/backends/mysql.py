import re
from typing import Any, Dict, List

import aiomysql

from migri.elements import Query
from migri.interfaces import ConnectionBackend, TransactionBackend


class MySQLConnection(ConnectionBackend):
    dialect = "mysql"

    @staticmethod
    def _compile(query: Query) -> dict:
        q = query.statement
        v = []

        if query.placeholders:
            for p in query.placeholders:
                # Append value
                v.append(query.values[p.replace("$", "")])

                # Substitute
                q = re.sub(f"\\{p}", "%s", q)

        return {"query": q, "values": v}

    async def _cursor_execute(self, query: Query) -> aiomysql.Cursor:
        q = self._compile(query)
        cur = await self._db.cursor(aiomysql.DictCursor)
        await cur.execute(q["query"], q["values"])
        return cur

    async def connect(self):
        if not self._db:
            self._db = await aiomysql.connect(
                host=self._db_host,
                port=self._db_port,
                user=self._db_user,
                password=self._db_pass,
                db=self._db_name,
            )

    async def disconnect(self):
        self._db.close()

    async def execute(self, query: Query):
        await self._cursor_execute(query)

    async def fetch(self, query: Query) -> Dict[str, Any]:
        cursor = await self._cursor_execute(query)
        return await cursor.fetchone()

    async def fetch_all(self, query: Query) -> List[Dict[str, Any]]:
        cursor = await self._cursor_execute(query)
        return await cursor.fetchall()

    def transaction(self) -> "TransactionBackend":
        return MySQLTransaction(self)


class MySQLTransaction(TransactionBackend):
    async def start(self):
        await self._connection.database.begin()

    async def commit(self):
        await self._connection.database.commit()

    async def rollback(self):
        await self._connection.database.rollback()
