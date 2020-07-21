import re
from typing import Any, Dict, List

import aiosqlite

from migri.elements import Query
from migri.interfaces import ConnectionBackend, TransactionBackend


class SQLiteConnection(ConnectionBackend):
    dialect = "sqlite"

    @staticmethod
    def _compile(query: Query) -> dict:
        q = query.statement
        v = []

        if query.placeholders:
            for p in query.placeholders:
                # Append value
                v.append(query.values[p.replace("$", "")])

                # Substitute
                q = re.sub(f"\\{p}", "?", q)

        return {"query": q, "values": v}

    async def connect(self):
        self._db = await aiosqlite.connect(self._db_name)
        self._db.row_factory = aiosqlite.Row

    async def disconnect(self):
        await self._db.close()

    async def execute(self, query: Query):
        q = self._compile(query)
        await self._db.execute(q["query"], q["values"])

    async def fetch(self, query: Query) -> Dict[str, Any]:
        q = self._compile(query)
        cursor = await self._db.execute(q["query"], q["values"])
        res = await cursor.fetchone()
        await cursor.close()

        return dict(res)

    async def fetch_all(self, query: Query) -> List[Dict[str, Any]]:
        q = self._compile(query)
        cursor = await self._db.execute(q["query"], q["values"])
        res = await cursor.fetchall()
        await cursor.close()

        return [dict(r) for r in res]

    def transaction(self) -> "TransactionBackend":
        return SQLiteTransaction(self)


class SQLiteTransaction(TransactionBackend):
    async def start(self):
        # Nothing to do
        return

    async def commit(self):
        await self._connection.database.commit()

    async def rollback(self):
        await self._connection.database.rollback()
